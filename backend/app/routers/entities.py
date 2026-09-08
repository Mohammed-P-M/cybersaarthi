from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.core.postgres import get_db
from app.models.database import Property, IncidentProperty, Incident
from app.schemas.pydantic_models import EntityDetailResponse
from app.services.graph_service import get_entity_details

router = APIRouter(prefix="/entities", tags=["Entities & Search"])

@router.get("/search")
def search_entities(
    query: str = Query(..., min_length=1),
    db: Session = Depends(get_db)
):
    """
    Global Investigator Search: Search across Phone, UPI, Transaction ID, URL, Email, Location, Person, Org.
    Returns matched entity summaries + total connected incidents.
    """
    clean_query = query.strip()
    
    # Search properties matching raw or normalized value
    props = db.query(Property).filter(
        (Property.normalized_value.ilike(f"%{clean_query}%")) | 
        (Property.raw_value.ilike(f"%{clean_query}%"))
    ).limit(30).all()

    results = []
    seen = set()

    for p in props:
        key = (p.type, p.normalized_value)
        if key in seen:
            continue
        seen.add(key)

        # Count connected incidents
        inc_count = db.query(IncidentProperty).filter(IncidentProperty.property_id == p.id).count()

        results.append({
            "property_id": p.id,
            "type": p.type,
            "raw_value": p.raw_value,
            "normalized_value": p.normalized_value,
            "connected_incidents_count": inc_count
        })

    # Also search incidents by ID or Description
    incidents = db.query(Incident).filter(
        (Incident.id.ilike(f"%{clean_query}%")) |
        (Incident.description.ilike(f"%{clean_query}%")) |
        (Incident.location.ilike(f"%{clean_query}%"))
    ).limit(10).all()

    inc_results = [
        {
            "id": inc.id,
            "description": inc.description,
            "category": inc.category,
            "timestamp": inc.timestamp,
            "location": inc.location
        } for inc in incidents
    ]

    return {
        "query": query,
        "matched_entities": results,
        "matched_incidents": inc_results
    }

@router.get("/{type}/{value}", response_model=EntityDetailResponse)
def get_entity_by_type_value(
    type: str,
    value: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve full connection details for a specific entity type and value.
    """
    return get_entity_details(entity_type=type, normalized_value=value, db=db)
