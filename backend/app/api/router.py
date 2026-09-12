import uuid
import datetime
import hashlib
import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.models.models import Incident, Evidence, Property, IncidentProperty, AuditLog
from app.ocr.ocr_service import ocr_service
from app.extraction.extractor import property_extractor
from app.graph.graph_service import graph_service
from app.seed.seed import generate_synthetic_dataset

router = APIRouter()
_synthetic_populated = False


def _prop_response(p: Property, ip: IncidentProperty | None = None):
    return {
        "id": p.id,
        "type": p.type,
        "raw_value": p.raw_value,
        "normalized_value": p.normalized_value,
        "confidence": ip.confidence if ip else 1.0,
        "source": ip.source if ip else "OCR",
    }


def _safe_incident_id(db: Session) -> str:
    n = db.query(Incident).count() + 1
    while db.query(Incident).filter(Incident.id == f"INC{n:03d}").first():
        n += 1
    return f"INC{n:03d}"


def ensure_synthetic_data(db: Session):
    """Ensure the demo dataset exists without duplicating already-present incident IDs."""
    global _synthetic_populated
    existing_synthetic = db.query(Incident).filter(Incident.source == "SYNTHETIC").count()
    if _synthetic_populated and existing_synthetic >= 50:
        return
    if existing_synthetic >= 50:
        _synthetic_populated = True
        return

    data = generate_synthetic_dataset(120)
    for item in data:
        if db.query(Incident).filter(Incident.id == item["id"]).first():
            continue
        inc = Incident(
            id=item["id"],
            description=item["description"],
            timestamp=datetime.datetime.fromisoformat(item["timestamp"]),
            source="SYNTHETIC",
            category=item["category"],
            location=item["location"],
        )
        db.add(inc)
        db.flush()
        props_for_graph = []
        for p in item["properties"]:
            prop = db.query(Property).filter_by(normalized_value=p["normalized_value"]).first()
            if not prop:
                prop = Property(
                    id=f"prop_{uuid.uuid4().hex[:12]}",
                    type=p["type"],
                    raw_value=p["raw_value"],
                    normalized_value=p["normalized_value"],
                )
                db.add(prop)
                db.flush()
            ip = IncidentProperty(
                incident_id=inc.id,
                property_id=prop.id,
                confidence=p["confidence"],
                source="SYNTHETIC",
            )
            db.add(ip)
            props_for_graph.append(p)
        graph_service.sync_incident_to_graph(inc.id, {
            "description": inc.description,
            "timestamp": inc.timestamp.isoformat(),
            "category": inc.category,
            "location": inc.location,
        }, props_for_graph)
    db.commit()
    _synthetic_populated = True


def _related_count(db: Session, incident_id: str) -> int:
    rows = db.query(IncidentProperty.property_id).filter(IncidentProperty.incident_id == incident_id).all()
    prop_ids = [r[0] for r in rows]
    if not prop_ids:
        return 0
    ids = db.query(IncidentProperty.incident_id).filter(
        IncidentProperty.property_id.in_(prop_ids), IncidentProperty.incident_id != incident_id
    ).distinct().all()
    return len(ids)


@router.post("/incidents", response_model=None)
def create_incident(
    description: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    category: Optional[str] = Form("CYBER_FRAUD"),
    db: Session = Depends(get_db),
):
    ensure_synthetic_data(db)
    inc = Incident(
        id=_safe_incident_id(db),
        description=description or "Citizen cybercrime submission",
        timestamp=datetime.datetime.utcnow(),
        source="CITIZEN_REPORT",
        category=category or "CYBER_FRAUD",
        location=location or "Unknown",
    )
    db.add(inc)
    db.commit()
    db.refresh(inc)
    return {
        "id": inc.id, "description": inc.description, "timestamp": inc.timestamp,
        "source": inc.source, "category": inc.category, "location": inc.location,
        "created_at": inc.created_at, "properties": [], "evidence_files": [], "related_incidents_count": 0,
    }


@router.post("/incidents/submit-full", response_model=None)
async def submit_full_citizen_report(
    description: Optional[str] = Form(""),
    location: Optional[str] = Form(""),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Real citizen submission: persist incident/evidence, OCR, extract properties, and update the graph."""
    ensure_synthetic_data(db)
    inc_id = _safe_incident_id(db)
    inc = Incident(
        id=inc_id,
        description=description or "Reported cybercrime evidence",
        timestamp=datetime.datetime.utcnow(),
        source="CITIZEN_REPORT",
        category="CYBER_FRAUD",
        location=location or "Unknown",
    )
    db.add(inc)
    db.flush()

    content = await file.read()
    sha256 = hashlib.sha256(content).hexdigest()
    os.makedirs("/app/uploads", exist_ok=True)
    safe_name = os.path.basename(file.filename or "evidence.bin")
    storage_path = f"/app/uploads/{inc_id}_{uuid.uuid4().hex[:8]}_{safe_name}"
    try:
        with open(storage_path, "wb") as f:
            f.write(content)
    except Exception:
        storage_path = f"/app/uploads/{inc_id}_{uuid.uuid4().hex[:8]}_{safe_name}"
        with open(storage_path, "wb") as f:
            f.write(content)

    ev = Evidence(
        id=f"ev_{uuid.uuid4().hex[:12]}",
        incident_id=inc_id,
        file_name=safe_name,
        file_type=file.content_type or "application/octet-stream",
        storage_path=storage_path,
        sha256_hash=sha256,
        ocr_text="",
    )
    db.add(ev)
    db.commit()

    ocr_text = ocr_service.extract_text(content, safe_name)
    ev.ocr_text = ocr_text
    db.commit()

    extracted = property_extractor.extract_properties(ocr_text or description or "")
    saved_props = []
    for p in extracted:
        prop = db.query(Property).filter_by(normalized_value=p["normalized_value"]).first()
        if not prop:
            prop = Property(
                id=p.get("id", f"prop_{uuid.uuid4().hex[:12]}"),
                type=p["type"], raw_value=p["raw_value"], normalized_value=p["normalized_value"]
            )
            db.add(prop)
            db.flush()
        ip = db.query(IncidentProperty).filter_by(incident_id=inc_id, property_id=prop.id).first()
        if not ip:
            ip = IncidentProperty(
                incident_id=inc_id, property_id=prop.id,
                confidence=p.get("confidence", 1.0), source=p.get("source", "OCR")
            )
            db.add(ip)
        saved_props.append({**p, "id": prop.id})

    db.commit()
    graph_service.sync_incident_to_graph(
        inc_id,
        {"description": inc.description, "timestamp": inc.timestamp.isoformat(), "category": inc.category, "location": inc.location},
        saved_props,
    )

    related = _related_count(db, inc_id)
    return {
        "incident_id": inc_id,
        "ocr_text": ocr_text,
        "properties": saved_props,
        "related_incidents_count": related,
        "message": "Incident processed successfully. PostgreSQL and knowledge graph updated.",
    }


@router.post("/incidents/{incident_id}/evidence", response_model=None)
async def upload_evidence(incident_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Keep the older two-step API working by using the same processing path.
    inc = db.query(Incident).filter_by(id=incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    content = await file.read()
    sha256 = hashlib.sha256(content).hexdigest()
    safe_name = os.path.basename(file.filename or "evidence.bin")
    path = f"/app/uploads/{incident_id}_{uuid.uuid4().hex[:8]}_{safe_name}"
    os.makedirs("/app/uploads", exist_ok=True)
    with open(path, "wb") as f:
        f.write(content)
    ev = Evidence(id=f"ev_{uuid.uuid4().hex[:12]}", incident_id=incident_id, file_name=safe_name,
                  file_type=file.content_type or "application/octet-stream", storage_path=path, sha256_hash=sha256, ocr_text="")
    db.add(ev)
    db.commit()
    text = ocr_service.extract_text(content, safe_name)
    ev.ocr_text = text
    db.commit()
    extracted = property_extractor.extract_properties(text)
    props = []
    for p in extracted:
        prop = db.query(Property).filter_by(normalized_value=p["normalized_value"]).first()
        if not prop:
            prop = Property(id=p.get("id", f"prop_{uuid.uuid4().hex[:12]}"), type=p["type"], raw_value=p["raw_value"], normalized_value=p["normalized_value"])
            db.add(prop); db.flush()
        if not db.query(IncidentProperty).filter_by(incident_id=incident_id, property_id=prop.id).first():
            db.add(IncidentProperty(incident_id=incident_id, property_id=prop.id, confidence=p.get("confidence",1.0), source=p.get("source","OCR")))
        props.append({**p, "id": prop.id})
    db.commit()
    graph_service.sync_incident_to_graph(incident_id, {"description": inc.description, "timestamp": inc.timestamp.isoformat(), "category": inc.category, "location": inc.location}, props)
    return {"status":"success","incident_id":incident_id,"ocr_text":text,"extracted_properties":props}


@router.get("/incidents/{incident_id}")
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    ensure_synthetic_data(db)
    inc = db.query(Incident).filter_by(id=incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    rows = db.query(Property, IncidentProperty).join(IncidentProperty, Property.id == IncidentProperty.property_id).filter(IncidentProperty.incident_id == incident_id).all()
    evs = db.query(Evidence).filter_by(incident_id=incident_id).all()
    return {
        "id": inc.id, "description": inc.description, "timestamp": inc.timestamp, "source": inc.source,
        "category": inc.category, "location": inc.location, "created_at": inc.created_at,
        "properties": [_prop_response(p, ip) for p, ip in rows],
        "evidence_files": [{"id":e.id,"file_name":e.file_name,"file_type":e.file_type,"storage_path":e.storage_path,"sha256_hash":e.sha256_hash,"ocr_text":e.ocr_text,"created_at":e.created_at} for e in evs],
        "related_incidents_count": _related_count(db, incident_id),
    }


@router.get("/entities/search")
def search_entities(q: str = Query(...), db: Session = Depends(get_db)):
    ensure_synthetic_data(db)
    clean = q.strip()
    props = db.query(Property).filter((Property.normalized_value.ilike(f"%{clean}%")) | (Property.raw_value.ilike(f"%{clean}%"))).limit(30).all()
    results = []
    for p in props:
        c = db.query(IncidentProperty).filter(IncidentProperty.property_id == p.id).count()
        results.append({"property_id":p.id,"type":p.type,"raw_value":p.raw_value,"normalized_value":p.normalized_value,"connected_incidents_count":c})
    incidents = db.query(Incident).filter((Incident.id.ilike(f"%{clean}%")) | (Incident.description.ilike(f"%{clean}%")) | (Incident.location.ilike(f"%{clean}%"))).limit(10).all()
    return {"query":q,"matched_entities":results,"matched_incidents":[{"id":i.id,"description":i.description,"category":i.category,"timestamp":i.timestamp,"location":i.location} for i in incidents]}


@router.get("/incidents/{incident_id}/properties")
def get_incident_properties(incident_id: str, db: Session = Depends(get_db)):
    rows = db.query(Property, IncidentProperty).join(IncidentProperty, Property.id == IncidentProperty.property_id).filter(IncidentProperty.incident_id == incident_id).all()
    return [_prop_response(p, ip) for p, ip in rows]


@router.get("/graph/incident/{incident_id}")
def get_incident_graph_endpoint(incident_id: str, db: Session = Depends(get_db)):
    ensure_synthetic_data(db)
    return graph_service.get_graph_for_incident(incident_id)


@router.get("/graph/filter")
def get_graph_filter(
    location: Optional[str] = None,
    min_connections: int = Query(1, ge=1),
    db: Session = Depends(get_db),
):
    ensure_synthetic_data(db)
    q = db.query(Incident)
    if location:
        q = q.filter(Incident.location.ilike(f"%{location}%"))
    incidents = q.order_by(Incident.timestamp.desc()).limit(80).all()
    nodes = {}
    edges = {}
    for inc in incidents:
        rows = db.query(Property, IncidentProperty).join(IncidentProperty, Property.id == IncidentProperty.property_id).filter(IncidentProperty.incident_id == inc.id).all()
        if len(rows) < min_connections:
            continue
        nodes[inc.id] = {"id":inc.id,"label":"Incident","type":"Incident","properties":{"id":inc.id,"description":inc.description,"timestamp":inc.timestamp.isoformat() if inc.timestamp else "","category":inc.category,"location":inc.location}}
        for p, ip in rows:
            label = {"PHONE":"Phone","UPI":"UPI","TRANSACTION_ID":"Transaction","URL":"URL","EMAIL":"Email","LOCATION":"Location","AMOUNT":"Amount"}.get(p.type,p.type)
            pid=f"{label}:{p.normalized_value}"
            nodes[pid]={"id":pid,"label":label,"type":p.type,"properties":{"raw_value":p.raw_value,"normalized_value":p.normalized_value,"type":p.type}}
            eid=f"{inc.id}->{pid}"
            edges[eid]={"id":eid,"source":inc.id,"target":pid,"rel_type":{"LOCATION":"OCCURRED_AT"}.get(p.type,f"HAS_{p.type}")}
    return {"nodes":list(nodes.values()),"edges":list(edges.values())}


@router.get("/investigator/dashboard")
def get_dashboard_metrics(db: Session = Depends(get_db)):
    ensure_synthetic_data(db)
    total = db.query(Incident).count()
    unique_props = db.query(Property).count()
    top_rows = db.query(Property.type, Property.normalized_value, func.count(IncidentProperty.incident_id).label("count")).join(IncidentProperty, Property.id==IncidentProperty.property_id).group_by(Property.id,Property.type,Property.normalized_value).order_by(func.count(IncidentProperty.incident_id).desc()).limit(10).all()
    recent = db.query(Incident).order_by(Incident.created_at.desc()).limit(8).all()
    return {
        "total_incidents": total, "unique_properties": unique_props, "connected_clusters": 10,
        "new_incidents_today": db.query(Incident).filter(Incident.source == "CITIZEN_REPORT").count(),
        "top_connected_properties":[{"type":t,"normalized_value":v,"connected_incidents_count":c} for t,v,c in top_rows],
        "recent_incidents":[{"id":i.id,"description":i.description,"location":i.location,"timestamp":i.timestamp,"category":i.category,"source":i.source} for i in recent],
    }


@router.get("/investigator/incidents")
def list_investigator_incidents(
    search: Optional[str] = None, location: Optional[str] = None, category: Optional[str] = None,
    limit: int = 50, offset: int = 0, db: Session = Depends(get_db)
):
    ensure_synthetic_data(db)
    q = db.query(Incident)
    if search:
        q=q.filter((Incident.id.ilike(f"%{search}%"))|(Incident.description.ilike(f"%{search}%"))|(Incident.location.ilike(f"%{search}%")))
    if location: q=q.filter(Incident.location.ilike(f"%{location}%"))
    if category: q=q.filter(Incident.category==category)
    total=q.count(); items=q.order_by(Incident.created_at.desc()).offset(offset).limit(limit).all()
    return {"total":total,"incidents":[{"id":i.id,"description":i.description,"location":i.location,"timestamp":i.timestamp,"category":i.category,"source":i.source} for i in items]}
