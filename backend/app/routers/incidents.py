import os
import hashlib
import uuid
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.core.postgres import get_db
from app.core.config import settings
from app.models.database import Incident, Evidence, Property, IncidentProperty, AuditLog
from app.schemas.pydantic_models import IncidentCreate, IncidentResponse, EvidenceResponse, PropertyItem, ProcessResultResponse
from app.services.ocr_service import extract_ocr_text
from app.services.extractor_service import extract_properties
from app.services.graph_service import add_incident_to_graph

router = APIRouter(prefix="/incidents", tags=["Incidents"])

@router.post("", response_model=IncidentResponse)
def create_incident(data: IncidentCreate, db: Session = Depends(get_db)):
    inc_id = f"INC{str(uuid.uuid4())[:8].upper()}"
    inc = Incident(
        id=inc_id,
        description=data.description,
        timestamp=data.timestamp or datetime.utcnow().strftime("%d %b %Y"),
        source=data.source or "CITIZEN",
        category=data.category or "CYBER_FRAUD",
        location=data.location,
        status="NEW"
    )
    db.add(inc)
    
    audit = AuditLog(action="CREATE", resource_type="INCIDENT", resource_id=inc.id)
    db.add(audit)

    db.commit()
    db.refresh(inc)
    
    return IncidentResponse(
        id=inc.id,
        description=inc.description,
        timestamp=inc.timestamp,
        source=inc.source,
        category=inc.category,
        location=inc.location,
        created_at=inc.created_at,
        evidence_items=[],
        properties=[],
        related_incidents_count=0
    )

@router.post("/{id}/evidence", response_model=EvidenceResponse)
async def upload_evidence(id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    inc = db.query(Incident).filter(Incident.id == id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    file_bytes = await file.read()
    sha256 = hashlib.sha256(file_bytes).hexdigest()

    file_ext = os.path.splitext(file.filename)[1]
    saved_filename = f"{id}_{uuid.uuid4().hex[:8]}{file_ext}"
    storage_path = os.path.join(settings.UPLOAD_DIR, saved_filename)

    with open(storage_path, "wb") as f:
        f.write(file_bytes)

    ev = Evidence(
        id=str(uuid.uuid4()),
        incident_id=id,
        file_name=file.filename,
        file_type=file.content_type or "image/png",
        storage_path=storage_path,
        sha256_hash=sha256,
        created_at=datetime.utcnow()
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)

    return EvidenceResponse(
        id=ev.id,
        file_name=ev.file_name,
        file_type=ev.file_type,
        storage_path=ev.storage_path,
        sha256_hash=ev.sha256_hash,
        created_at=ev.created_at
    )

@router.post("/{id}/process", response_model=ProcessResultResponse)
def process_incident(id: str, db: Session = Depends(get_db)):
    inc = db.query(Incident).filter(Incident.id == id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    evidences = db.query(Evidence).filter(Evidence.incident_id == id).all()
    full_ocr_text = ""
    for ev in evidences:
        if os.path.exists(ev.storage_path):
            text = extract_ocr_text(ev.storage_path)
            ev.ocr_text = text
            full_ocr_text += text + "\n"
    
    if not full_ocr_text.strip() and inc.description:
        full_ocr_text = inc.description

    # Extract & Normalize properties
    extracted_props = extract_properties(full_ocr_text)

    # Save to PostgreSQL
    db_props = []
    database_matches = {}
    related_incident_ids = set()

    for p_item in extracted_props:
        # Check existing Property by type & normalized_value
        prop = db.query(Property).filter(
            Property.type == p_item.type, 
            Property.normalized_value == p_item.normalized_value
        ).first()

        if not prop:
            prop = Property(
                id=str(uuid.uuid4()),
                type=p_item.type,
                raw_value=p_item.raw_value,
                normalized_value=p_item.normalized_value
            )
            db.add(prop)
            db.flush()
        
        # Link IncidentProperty
        existing_ip = db.query(IncidentProperty).filter(
            IncidentProperty.incident_id == id,
            IncidentProperty.property_id == prop.id
        ).first()

        if not existing_ip:
            ip = IncidentProperty(
                incident_id=id,
                property_id=prop.id,
                confidence=p_item.confidence,
                source=p_item.source
            )
            db.add(ip)

        p_item.id = prop.id
        db_props.append(p_item)

        # Count database matches (other incidents sharing this normalized property value)
        other_ips = db.query(IncidentProperty).filter(
            IncidentProperty.property_id == prop.id,
            IncidentProperty.incident_id != id
        ).all()

        match_count = len(other_ips)
        if match_count > 0:
            database_matches[p_item.type] = database_matches.get(p_item.type, 0) + match_count
            for oip in other_ips:
                related_incident_ids.add(oip.incident_id)

    db.commit()

    # Sync to Neo4j graph engine
    add_incident_to_graph(inc.id, inc.timestamp, inc.category, db_props)

    return ProcessResultResponse(
        incident_id=inc.id,
        ocr_text=full_ocr_text,
        properties=db_props,
        database_matches=database_matches,
        related_incidents_count=len(related_incident_ids),
        message="Incident processed successfully. Network graph updated."
    )

@router.post("/submit-full", response_model=ProcessResultResponse)
async def submit_full_citizen_report(
    description: Optional[str] = Form(""),
    location: Optional[str] = Form(""),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Combined endpoint for Citizen Portal: Uploads screenshot, creates incident, performs OCR, extracts properties, saves to DB/Graph in one single step.
    """
    inc_id = f"INC{str(uuid.uuid4())[:8].upper()}"
    inc = Incident(
        id=inc_id,
        description=description,
        timestamp=datetime.utcnow().strftime("%d %b %Y"),
        source="CITIZEN",
        category="CYBER_FRAUD",
        location=location or "Kochi",
        status="NEW"
    )
    db.add(inc)
    db.flush()

    file_bytes = await file.read()
    sha256 = hashlib.sha256(file_bytes).hexdigest()

    file_ext = os.path.splitext(file.filename)[1]
    saved_filename = f"{inc_id}_{uuid.uuid4().hex[:8]}{file_ext}"
    storage_path = os.path.join(settings.UPLOAD_DIR, saved_filename)

    with open(storage_path, "wb") as f:
        f.write(file_bytes)

    ev = Evidence(
        id=str(uuid.uuid4()),
        incident_id=inc_id,
        file_name=file.filename,
        file_type=file.content_type or "image/png",
        storage_path=storage_path,
        sha256_hash=sha256,
        created_at=datetime.utcnow()
    )
    db.add(ev)
    db.commit()

    # Run processing
    return process_incident(id=inc_id, db=db)

@router.get("/{id}", response_model=IncidentResponse)
def get_incident(id: str, db: Session = Depends(get_db)):
    inc = db.query(Incident).filter(Incident.id == id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    evidences = db.query(Evidence).filter(Evidence.incident_id == id).all()
    evidence_items = [
        EvidenceResponse(
            id=ev.id,
            file_name=ev.file_name,
            file_type=ev.file_type,
            storage_path=ev.storage_path,
            sha256_hash=ev.sha256_hash,
            ocr_text=ev.ocr_text,
            created_at=ev.created_at
        ) for ev in evidences
    ]

    props_db = db.query(Property, IncidentProperty)\
        .join(IncidentProperty, Property.id == IncidentProperty.property_id)\
        .filter(IncidentProperty.incident_id == id).all()

    properties = []
    related_incident_ids = set()

    for p, ip in props_db:
        properties.append(PropertyItem(
            id=p.id,
            type=p.type,
            raw_value=p.raw_value,
            normalized_value=p.normalized_value,
            confidence=ip.confidence,
            source=ip.source
        ))

        # Check related
        shared = db.query(IncidentProperty).filter(
            IncidentProperty.property_id == p.id,
            IncidentProperty.incident_id != id
        ).all()
        for s in shared:
            related_incident_ids.add(s.incident_id)

    return IncidentResponse(
        id=inc.id,
        description=inc.description,
        timestamp=inc.timestamp,
        source=inc.source,
        category=inc.category,
        location=inc.location,
        created_at=inc.created_at,
        evidence_items=evidence_items,
        properties=properties,
        related_incidents_count=len(related_incident_ids)
    )

@router.get("/{id}/properties", response_model=List[PropertyItem])
def get_incident_properties(id: str, db: Session = Depends(get_db)):
    props_db = db.query(Property, IncidentProperty)\
        .join(IncidentProperty, Property.id == IncidentProperty.property_id)\
        .filter(IncidentProperty.incident_id == id).all()

    return [
        PropertyItem(
            id=p.id,
            type=p.type,
            raw_value=p.raw_value,
            normalized_value=p.normalized_value,
            confidence=ip.confidence,
            source=ip.source
        ) for p, ip in props_db
    ]
