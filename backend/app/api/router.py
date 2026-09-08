import uuid
import datetime
import hashlib
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import Incident, Evidence, Property, IncidentProperty, AuditLog
from app.schemas.schemas import IncidentCreate, IncidentResponse, PropertyResponse, DashboardMetrics
from app.ocr.ocr_service import ocr_service
from app.extraction.extractor import property_extractor
from app.graph.graph_service import graph_service, fallback_graph
from app.seed.seed import generate_synthetic_dataset

router = APIRouter()

# Populate synthetic dataset at startup
_synthetic_populated = False

def ensure_synthetic_data(db: Session):
    global _synthetic_populated
    if _synthetic_populated:
        return
        
    try:
        existing = db.query(Incident).first()
        if existing:
            _synthetic_populated = True
            return
            
        data = generate_synthetic_dataset()
        for item in data:
            inc = Incident(
                id=item["id"],
                description=item["description"],
                timestamp=datetime.datetime.fromisoformat(item["timestamp"]),
                source=item["source"],
                category=item["category"],
                location=item["location"]
            )
            db.add(inc)
            
            # Sync graph & properties
            for p in item["properties"]:
                prop = db.query(Property).filter_by(normalized_value=p["normalized_value"]).first()
                if not prop:
                    prop = Property(
                        id=f"prop_{uuid.uuid4().hex[:12]}",
                        type=p["type"],
                        raw_value=p["raw_value"],
                        normalized_value=p["normalized_value"]
                    )
                    db.add(prop)
                    db.flush()
                
                inc_prop = IncidentProperty(
                    incident_id=inc.id,
                    property_id=prop.id,
                    confidence=p["confidence"],
                    source=p["source"]
                )
                db.add(inc_prop)
            
            graph_service.sync_incident_to_graph(inc.id, item, item["properties"])
            
        db.commit()
        _synthetic_populated = True
    except Exception as e:
        db.rollback()

@router.post("/incidents", response_model=IncidentResponse)
def create_incident(
    description: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    category: Optional[str] = Form("CYBER_FRAUD"),
    db: Session = Depends(get_db)
):
    ensure_synthetic_data(db)
    
    inc_num = db.query(Incident).count() + 1
    inc_id = f"INC{inc_num:03d}"
    
    inc = Incident(
        id=inc_id,
        description=description or "Citizen cybercrime submission",
        timestamp=datetime.datetime.utcnow(),
        source="CITIZEN_REPORT",
        category=category or "CYBER_FRAUD",
        location=location or "Unknown"
    )
    db.add(inc)
    db.commit()
    db.refresh(inc)
    return inc

@router.post("/incidents/{incident_id}/evidence")
async def upload_evidence(
    incident_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    inc = db.query(Incident).filter_by(id=incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    content = await file.read()
    sha256 = hashlib.sha256(content).hexdigest()

    ev_id = f"ev_{uuid.uuid4().hex[:12]}"
    ev = Evidence(
        id=ev_id,
        incident_id=incident_id,
        file_name=file.filename,
        file_type=file.content_type or "image/png",
        storage_path=f"/uploads/{ev_id}_{file.filename}",
        sha256_hash=sha256,
        ocr_text=""
    )
    db.add(ev)
    db.commit()

    # Step 2: OCR
    ocr_text = ocr_service.extract_text(content, file.filename)
    ev.ocr_text = ocr_text
    db.commit()

    # Step 3 & 4: Property extraction & normalization
    extracted_props = property_extractor.extract_properties(ocr_text)

    # Save properties & links
    saved_props = []
    for p in extracted_props:
        prop = db.query(Property).filter_by(normalized_value=p["normalized_value"]).first()
        if not prop:
            prop = Property(
                id=p["id"],
                type=p["type"],
                raw_value=p["raw_value"],
                normalized_value=p["normalized_value"]
            )
            db.add(prop)
            db.flush()
        
        inc_prop = db.query(IncidentProperty).filter_by(incident_id=incident_id, property_id=prop.id).first()
        if not inc_prop:
            inc_prop = IncidentProperty(
                incident_id=incident_id,
                property_id=prop.id,
                confidence=p["confidence"],
                source=p["source"]
            )
            db.add(inc_prop)
        saved_props.append(p)

    db.commit()

    # Step 5 & 6: Neo4j Graph Synchronization & Automatic relationship discovery
    graph_service.sync_incident_to_graph(
        incident_id,
        {
            "description": inc.description,
            "timestamp": inc.timestamp.isoformat(),
            "category": inc.category,
            "location": inc.location
        },
        saved_props
    )

    return {
        "status": "success",
        "incident_id": incident_id,
        "ocr_text": ocr_text,
        "extracted_properties": saved_props
    }

@router.get("/incidents/{incident_id}")
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    ensure_synthetic_data(db)
    inc = db.query(Incident).filter_by(id=incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    props = db.query(Property).join(IncidentProperty).filter(IncidentProperty.incident_id == incident_id).all()
    ev = db.query(Evidence).filter_by(incident_id=incident_id).all()
    
    return {
        "id": inc.id,
        "description": inc.description,
        "timestamp": inc.timestamp,
        "source": inc.source,
        "category": inc.category,
        "location": inc.location,
        "created_at": inc.created_at,
        "properties": [
            {"id": p.id, "type": p.type, "raw_value": p.raw_value, "normalized_value": p.normalized_value}
            for p in props
        ],
        "evidence_files": [
            {"id": e.id, "file_name": e.file_name, "sha256_hash": e.sha256_hash, "ocr_text": e.ocr_text}
            for e in ev
        ]
    }

@router.get("/entities/search")
def search_entities(q: str = Query(...), db: Session = Depends(get_db)):
    ensure_synthetic_data(db)
    norm_q = property_extractor.normalize_property("QUERY", q)
    
    props = db.query(Property).filter(
        (Property.normalized_value.like(f"%{norm_q}%")) | (Property.raw_value.like(f"%{q}%"))
    ).all()
    
    connected_inc_ids = set()
    for p in props:
        inc_props = db.query(IncidentProperty).filter_by(property_id=p.id).all()
        for ip in inc_props:
            connected_inc_ids.add(ip.incident_id)
            
    incidents = db.query(Incident).filter(Incident.id.in_(list(connected_inc_ids))).all()
    
    return {
        "query": q,
        "normalized_query": norm_q,
        "total_connected_incidents": len(incidents),
        "total_matched_properties": len(props),
        "properties": [{"id": p.id, "type": p.type, "raw_value": p.raw_value, "normalized_value": p.normalized_value} for p in props],
        "incidents": [{"id": i.id, "description": i.description, "location": i.location, "timestamp": i.timestamp} for i in incidents]
    }

@router.get("/graph/incident/{incident_id}")
def get_incident_graph_endpoint(incident_id: str, db: Session = Depends(get_db)):
    ensure_synthetic_data(db)
    return graph_service.get_graph_for_incident(incident_id)

@router.get("/investigator/dashboard")
def get_dashboard_metrics(db: Session = Depends(get_db)):
    ensure_synthetic_data(db)
    
    total_incidents = db.query(Incident).count()
    unique_properties = db.query(Property).count()
    
    # Calculate top properties
    top_props = (
        db.query(Property.type, Property.normalized_value, IncidentProperty.property_id)
        .join(IncidentProperty, Property.id == IncidentProperty.property_id)
        .all()
    )
    
    counts = {}
    for tp in top_props:
        key = f"{tp.type}:{tp.normalized_value}"
        counts[key] = counts.get(key, 0) + 1
        
    sorted_most_connected = sorted(
        [{"type": k.split(":")[0], "value": k.split(":")[1], "count": v} for k, v in counts.items()],
        key=lambda x: x["count"],
        reverse=True
    )[:10]

    recent_incidents = (
        db.query(Incident)
        .order_by(Incident.timestamp.desc())
        .limit(8)
        .all()
    )

    return {
        "total_incidents": total_incidents,
        "unique_properties": unique_properties,
        "connected_clusters": 10,
        "new_incidents": 14,
        "most_connected_properties": sorted_most_connected,
        "recent_incidents": [
            {"id": i.id, "description": i.description, "location": i.location, "timestamp": i.timestamp, "category": i.category}
            for i in recent_incidents
        ]
    }

@router.get("/investigator/incidents")
def list_investigator_incidents(
    location: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    ensure_synthetic_data(db)
    query = db.query(Incident)
    if location:
        query = query.filter(Incident.location.ilike(f"%{location}%"))
    if category:
        query = query.filter(Incident.category == category)
        
    incidents = query.order_by(Incident.timestamp.desc()).limit(limit).all()
    return [
        {"id": i.id, "description": i.description, "location": i.location, "timestamp": i.timestamp, "category": i.category, "source": i.source}
        for i in incidents
    ]
