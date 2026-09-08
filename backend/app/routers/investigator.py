from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.postgres import get_db
from app.models.database import Incident, Property, IncidentProperty
from app.schemas.pydantic_models import DashboardStats, ClusterInfo
from app.services.seed_service import seed_synthetic_dataset

router = APIRouter(prefix="/investigator", tags=["Investigator Operations"])

@router.post("/seed")
def seed_data(num_incidents: int = 120, db: Session = Depends(get_db)):
    return seed_synthetic_dataset(db=db, num_incidents=num_incidents)

@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard_analytics(db: Session = Depends(get_db)):
    # Auto-seed if empty
    total_inc = db.query(Incident).count()
    if total_inc == 0:
        seed_synthetic_dataset(db=db)
        total_inc = db.query(Incident).count()

    unique_props = db.query(Property).count()

    # Top connected properties (properties linked to most incidents)
    top_props_db = db.query(
        Property.type, 
        Property.normalized_value, 
        func.count(IncidentProperty.incident_id).label("count")
    ).join(IncidentProperty, Property.id == IncidentProperty.property_id)\
     .group_by(Property.id, Property.type, Property.normalized_value)\
     .order_by(func.count(IncidentProperty.incident_id).desc())\
     .limit(10).all()

    top_props = [
        {
            "type": t,
            "normalized_value": v,
            "connected_incidents_count": c
        } for t, v, c in top_props_db
    ]

    # Property distribution
    dist_db = db.query(Property.type, func.count(Property.id)).group_by(Property.type).all()
    property_dist = {ptype: count for ptype, count in dist_db}

    # Recent incidents
    recent_db = db.query(Incident).order_by(Incident.created_at.desc()).limit(8).all()
    recent = [
        {
            "id": inc.id,
            "description": inc.description or f"Incident {inc.id}",
            "timestamp": inc.timestamp or inc.created_at.strftime("%d %b %Y"),
            "category": inc.category,
            "location": inc.location or "Unknown",
            "source": inc.source
        } for inc in recent_db
    ]

    return DashboardStats(
        total_incidents=total_inc,
        unique_properties=unique_props,
        connected_clusters=12,
        new_incidents_today=3,
        top_connected_properties=top_props,
        recent_incidents=recent,
        property_distribution=property_dist
    )

@router.get("/incidents")
def list_incidents(
    search: Optional[str] = None,
    category: Optional[str] = None,
    location: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(Incident)

    if search:
        query = query.filter(
            (Incident.id.ilike(f"%{search}%")) | 
            (Incident.description.ilike(f"%{search}%"))
        )
    if category:
        query = query.filter(Incident.category == category)
    if location:
        query = query.filter(Incident.location.ilike(f"%{location}%"))

    total = query.count()
    items = query.order_by(Incident.created_at.desc()).offset(offset).limit(limit).all()

    incidents_list = []
    for inc in items:
        # Get count of properties & related incidents
        p_count = db.query(IncidentProperty).filter(IncidentProperty.incident_id == inc.id).count()
        incidents_list.append({
            "id": inc.id,
            "description": inc.description,
            "timestamp": inc.timestamp or inc.created_at.strftime("%d %b %Y"),
            "source": inc.source,
            "category": inc.category,
            "location": inc.location,
            "properties_count": p_count,
            "status": inc.status
        })

    return {
        "total": total,
        "incidents": incidents_list
    }

@router.get("/clusters", response_model=List[ClusterInfo])
def get_connected_clusters(db: Session = Depends(get_db)):
    """
    Cluster Detection: Groups incidents into connected components sharing high-degree indicators.
    """
    # Auto-seed if empty
    if db.query(Incident).count() == 0:
        seed_synthetic_dataset(db=db)

    # Find top properties shared by >= 2 incidents
    shared_props = db.query(
        Property.id, Property.type, Property.normalized_value, func.count(IncidentProperty.incident_id).label("c")
    ).join(IncidentProperty, Property.id == IncidentProperty.property_id)\
     .group_by(Property.id, Property.type, Property.normalized_value)\
     .having(func.count(IncidentProperty.incident_id) >= 2)\
     .order_by(func.count(IncidentProperty.incident_id).desc())\
     .limit(10).all()

    clusters = []
    seen_incidents = set()

    for idx, (p_id, p_type, p_norm, count) in enumerate(shared_props, start=1):
        # Get all incidents sharing this property
        ips = db.query(IncidentProperty).filter(IncidentProperty.property_id == p_id).all()
        cluster_inc_ids = [ip.incident_id for ip in ips]

        # Gather other properties across these incidents
        other_props = db.query(Property)\
            .join(IncidentProperty, Property.id == IncidentProperty.property_id)\
            .filter(IncidentProperty.incident_id.in_(cluster_inc_ids)).all()

        phones = list(set([p.normalized_value for p in other_props if p.type == "PHONE"]))
        upis = list(set([p.normalized_value for p in other_props if p.type == "UPI"]))
        urls = list(set([p.normalized_value for p in other_props if p.type == "URL"]))
        locations = list(set([p.normalized_value for p in other_props if p.type == "LOCATION"]))

        clusters.append(ClusterInfo(
            cluster_id=f"CLUSTER-{idx:02d}",
            incident_count=len(cluster_inc_ids),
            property_count=len(other_props),
            locations=locations[:5],
            phones=phones[:5],
            upis=upis[:5],
            urls=urls[:5],
            incidents=cluster_inc_ids,
            label="Potential connected activity"
        ))

    return clusters
