from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.postgres import get_db
from app.schemas.pydantic_models import GraphDataResponse, CytoscapeNode, CytoscapeNodeData, CytoscapeEdge, CytoscapeEdgeData
from app.services.graph_service import get_graph_for_incident, PROP_CONFIG
from app.models.database import Incident, Property, IncidentProperty

router = APIRouter(prefix="/graph", tags=["Graph & Visualizer"])

@router.get("/incident/{id}", response_model=GraphDataResponse)
def get_incident_graph(id: str, db: Session = Depends(get_db)):
    return get_graph_for_incident(incident_id=id, db=db)

@router.get("/entity/{type}/{value}", response_model=GraphDataResponse)
def get_entity_graph(type: str, value: str, db: Session = Depends(get_db)):
    nodes_dict = {}
    edges_dict = {}

    props = db.query(Property).filter(
        Property.type == type.upper(),
        Property.normalized_value == value
    ).all()

    if not props:
        props = db.query(Property).filter(Property.normalized_value == value).all()

    prop_ids = [p.id for p in props]

    label, rel = PROP_CONFIG.get(type.upper(), ("Property", "HAS_PROPERTY"))
    p_id = f"{label}:{value}"

    nodes_dict[p_id] = CytoscapeNodeData(
        id=p_id,
        label=f"{label}: {value}",
        type=label,
        raw_value=props[0].raw_value if props else value,
        normalized_value=value
    )

    inc_props = db.query(IncidentProperty).filter(IncidentProperty.property_id.in_(prop_ids)).all()
    inc_ids = [ip.incident_id for ip in inc_props]

    incidents = db.query(Incident).filter(Incident.id.in_(inc_ids)).all()

    for inc in incidents:
        nodes_dict[inc.id] = CytoscapeNodeData(
            id=inc.id,
            label=f"INC-{inc.id[:8]}",
            type="Incident",
            raw_value=inc.id,
            normalized_value=inc.id
        )
        e_id = f"{inc.id}--{rel}->{p_id}"
        edges_dict[e_id] = CytoscapeEdgeData(
            id=e_id,
            source=inc.id,
            target=p_id,
            label=rel
        )

        # Also get other properties for these connected incidents
        other_ips = db.query(Property, IncidentProperty)\
            .join(IncidentProperty, Property.id == IncidentProperty.property_id)\
            .filter(IncidentProperty.incident_id == inc.id).all()

        for op, oip in other_ips:
            o_label, o_rel = PROP_CONFIG.get(op.type, ("Property", "HAS_PROPERTY"))
            op_id = f"{o_label}:{op.normalized_value}"
            if op_id not in nodes_dict:
                nodes_dict[op_id] = CytoscapeNodeData(
                    id=op_id,
                    label=f"{o_label}: {op.normalized_value}",
                    type=o_label,
                    raw_value=op.raw_value,
                    normalized_value=op.normalized_value
                )
            oe_id = f"{inc.id}--{o_rel}->{op_id}"
            edges_dict[oe_id] = CytoscapeEdgeData(
                id=oe_id,
                source=inc.id,
                target=op_id,
                label=o_rel
            )

    return GraphDataResponse(
        nodes=[CytoscapeNode(data=n) for n in nodes_dict.values()],
        edges=[CytoscapeEdge(data=e) for e in edges_dict.values()]
    )

@router.get("/filter", response_model=GraphDataResponse)
def get_filtered_graph(
    property_types: Optional[List[str]] = Query(None),
    location: Optional[str] = Query(None),
    min_connections: int = Query(1),
    db: Session = Depends(get_db)
):
    nodes_dict = {}
    edges_dict = {}

    query = db.query(Incident)

    if location:
        query = query.filter(Incident.location.ilike(f"%{location}%"))

    incidents = query.limit(50).all()

    for inc in incidents:
        # Check incident properties
        props_query = db.query(Property, IncidentProperty)\
            .join(IncidentProperty, Property.id == IncidentProperty.property_id)\
            .filter(IncidentProperty.incident_id == inc.id)

        if property_types:
            props_query = props_query.filter(Property.type.in_([pt.upper() for pt in property_types]))

        props = props_query.all()
        if len(props) < min_connections:
            continue

        nodes_dict[inc.id] = CytoscapeNodeData(
            id=inc.id,
            label=f"INC-{inc.id[:8]}",
            type="Incident",
            raw_value=inc.id,
            normalized_value=inc.id
        )

        for p, ip in props:
            label, rel = PROP_CONFIG.get(p.type, ("Property", "HAS_PROPERTY"))
            p_id = f"{label}:{p.normalized_value}"

            if p_id not in nodes_dict:
                nodes_dict[p_id] = CytoscapeNodeData(
                    id=p_id,
                    label=f"{label}: {p.normalized_value}",
                    type=label,
                    raw_value=p.raw_value,
                    normalized_value=p.normalized_value
                )

            e_id = f"{inc.id}--{rel}->{p_id}"
            edges_dict[e_id] = CytoscapeEdgeData(
                id=e_id,
                source=inc.id,
                target=p_id,
                label=rel
            )

    return GraphDataResponse(
        nodes=[CytoscapeNode(data=n) for n in nodes_dict.values()],
        edges=[CytoscapeEdge(data=e) for e in edges_dict.values()]
    )
