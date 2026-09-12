import logging
from typing import List, Dict, Any, Tuple
from app.core.neo4j import get_neo4j_driver
from app.schemas.pydantic_models import PropertyItem, CytoscapeNode, CytoscapeNodeData, CytoscapeEdge, CytoscapeEdgeData, GraphDataResponse, EntityDetailResponse, ClusterInfo
from sqlalchemy.orm import Session
from app.models.database import Incident, Property, IncidentProperty

logger = logging.getLogger(__name__)

# Map property type string to Neo4j Label and Relationship Type
PROP_CONFIG = {
    "PHONE": ("Phone", "HAS_PHONE"),
    "UPI": ("UPI", "HAS_UPI"),
    "TRANSACTION_ID": ("Transaction", "HAS_TRANSACTION"),
    "URL": ("URL", "HAS_URL"),
    "EMAIL": ("Email", "HAS_EMAIL"),
    "IFSC": ("IFSC", "HAS_IFSC"),
    "AMOUNT": ("Amount", "HAS_AMOUNT"),
    "LOCATION": ("Location", "OCCURRED_AT"),
    "PERSON": ("Person", "MENTIONS"),
    "ORGANIZATION": ("Organization", "MENTIONS"),
    "SOCIAL_HANDLE": ("SocialHandle", "HAS_SOCIAL_HANDLE"),
    "DATE": ("Date", "OCCURRED_ON"),
    "TIME": ("Time", "OCCURRED_AT_TIME"),
}

def add_incident_to_graph(incident_id: str, timestamp: str, category: str, properties: List[PropertyItem]):
    """
    Upserts an Incident node and connects it to merged Property nodes in Neo4j.
    """
    driver = get_neo4j_driver()
    if driver:
        try:
            with driver.session() as session:
                # Merge Incident node
                session.run(
                    "MERGE (i:Incident {id: $id}) SET i.timestamp = $ts, i.category = $cat",
                    id=incident_id, ts=timestamp or "", cat=category or ""
                )
                
                # Merge Property nodes and relationships
                for p in properties:
                    label, rel = PROP_CONFIG.get(p.type, ("Property", "HAS_PROPERTY"))
                    cypher = f"""
                    MERGE (p:{label} {{normalized_value: $norm}})
                    ON CREATE SET p.raw_value = $raw, p.type = $ptype, p.created_at = timestamp()
                    WITH p
                    MATCH (i:Incident {{id: $inc_id}})
                    MERGE (i)-[r:{rel}]->(p)
                    SET r.confidence = $conf, r.source = $src
                    """
                    session.run(cypher, norm=p.normalized_value, raw=p.raw_value, ptype=p.type, inc_id=incident_id, conf=p.confidence, src=p.source)
            return
        except Exception as e:
            logger.error(f"Failed to write to Neo4j: {e}")
            pass

def get_graph_for_incident(incident_id: str, db: Session) -> GraphDataResponse:
    """
    Retrieves the 1-hop & 2-hop neighborhood of an incident to discover connected incidents via shared properties.
    """
    nodes_dict: Dict[str, CytoscapeNodeData] = {}
    edges_dict: Dict[str, CytoscapeEdgeData] = {}

    driver = get_neo4j_driver()
    if driver:
        try:
            with driver.session() as session:
                query = """
                MATCH (i:Incident {id: $id})-[r1]->(p)
                OPTIONAL MATCH (p)<-[r2]-(i2:Incident)
                RETURN i, r1, p, r2, i2
                """
                res = session.run(query, id=incident_id)
                for record in res:
                    i = record["i"]
                    p = record["p"]
                    r1 = record["r1"]
                    i2 = record["i2"]
                    r2 = record["r2"]

                    # Main Incident node
                    if i and i["id"] not in nodes_dict:
                        nodes_dict[i["id"]] = CytoscapeNodeData(
                            id=i["id"],
                            label=f"INC-{i['id'][:8]}",
                            type="Incident",
                            raw_value=i["id"],
                            normalized_value=i["id"]
                        )
                    
                    # Property node
                    if p:
                        p_labels = list(p.labels)
                        ptype = p_labels[0] if p_labels else "Property"
                        p_id = f"{ptype}:{p['normalized_value']}"
                        if p_id not in nodes_dict:
                            nodes_dict[p_id] = CytoscapeNodeData(
                                id=p_id,
                                label=f"{ptype}: {p['normalized_value']}",
                                type=ptype,
                                raw_value=p.get("raw_value", p["normalized_value"]),
                                normalized_value=p["normalized_value"]
                            )
                        
                        # Edge i -> p
                        if i and r1:
                            e1_id = f"{i['id']}--{r1.type}->{p_id}"
                            edges_dict[e1_id] = CytoscapeEdgeData(
                                id=e1_id,
                                source=i["id"],
                                target=p_id,
                                label=r1.type
                            )
                        
                        # Shared Incident node i2
                        if i2:
                            if i2["id"] not in nodes_dict:
                                nodes_dict[i2["id"]] = CytoscapeNodeData(
                                    id=i2["id"],
                                    label=f"INC-{i2['id'][:8]}",
                                    type="Incident",
                                    raw_value=i2["id"],
                                    normalized_value=i2["id"]
                                )
                            if r2:
                                e2_id = f"{i2['id']}--{r2.type}->{p_id}"
                                edges_dict[e2_id] = CytoscapeEdgeData(
                                    id=e2_id,
                                    source=i2["id"],
                                    target=p_id,
                                    label=r2.type
                                )

                return GraphDataResponse(
                    nodes=[CytoscapeNode(data=n) for n in nodes_dict.values()],
                    edges=[CytoscapeEdge(data=e) for e in edges_dict.values()]
                )
        except Exception as e:
            logger.error(f"Error querying Neo4j for incident graph: {e}")

    # Fallback using PostgreSQL database query when Neo4j is offline
    return _get_graph_from_postgres(incident_id=incident_id, db=db)

def _get_graph_from_postgres(incident_id: str, db: Session) -> GraphDataResponse:
    nodes_dict: Dict[str, CytoscapeNodeData] = {}
    edges_dict: Dict[str, CytoscapeEdgeData] = {}

    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        return GraphDataResponse(nodes=[], edges=[])

    # Root Incident Node
    nodes_dict[inc.id] = CytoscapeNodeData(
        id=inc.id,
        label=f"INC-{inc.id[:8]}",
        type="Incident",
        raw_value=inc.id,
        normalized_value=inc.id
    )

    # Get properties for this incident
    props = db.query(Property, IncidentProperty)\
        .join(IncidentProperty, Property.id == IncidentProperty.property_id)\
        .filter(IncidentProperty.incident_id == incident_id).all()

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

        e1_id = f"{inc.id}--{rel}->{p_id}"
        edges_dict[e1_id] = CytoscapeEdgeData(
            id=e1_id,
            source=inc.id,
            target=p_id,
            label=rel,
            confidence=ip.confidence
        )

        # Find other incidents sharing this property!
        shared_ips = db.query(IncidentProperty)\
            .filter(IncidentProperty.property_id == p.id, IncidentProperty.incident_id != incident_id)\
            .limit(20).all()

        for s_ip in shared_ips:
            other_inc = db.query(Incident).filter(Incident.id == s_ip.incident_id).first()
            if other_inc:
                if other_inc.id not in nodes_dict:
                    nodes_dict[other_inc.id] = CytoscapeNodeData(
                        id=other_inc.id,
                        label=f"INC-{other_inc.id[:8]}",
                        type="Incident",
                        raw_value=other_inc.id,
                        normalized_value=other_inc.id
                    )
                e2_id = f"{other_inc.id}--{rel}->{p_id}"
                edges_dict[e2_id] = CytoscapeEdgeData(
                    id=e2_id,
                    source=other_inc.id,
                    target=p_id,
                    label=rel,
                    confidence=s_ip.confidence
                )

    return GraphDataResponse(
        nodes=[CytoscapeNode(data=n) for n in nodes_dict.values()],
        edges=[CytoscapeEdge(data=e) for e in edges_dict.values()]
    )

def get_entity_details(entity_type: str, normalized_value: str, db: Session) -> EntityDetailResponse:
    """
    Returns statistics and connected incidents for a selected property node.
    """
    # Query matching property
    props = db.query(Property).filter(
        Property.type == entity_type.upper(), 
        Property.normalized_value == normalized_value
    ).all()

    if not props:
        # Fallback search by normalized_value across any property type
        props = db.query(Property).filter(Property.normalized_value == normalized_value).all()

    prop_ids = [p.id for p in props]

    if not prop_ids:
        return EntityDetailResponse(
            type=entity_type,
            raw_value=normalized_value,
            normalized_value=normalized_value,
            connected_incidents_count=0,
            connected_phones_count=0,
            connected_urls_count=0,
            connected_locations_count=0,
            first_observed=None,
            last_observed=None,
            connected_incidents=[]
        )

    # Get incident properties links
    inc_props = db.query(IncidentProperty).filter(IncidentProperty.property_id.in_(prop_ids)).all()
    inc_ids = list(set([ip.incident_id for ip in inc_props]))

    connected_incidents_db = db.query(Incident).filter(Incident.id.in_(inc_ids)).all()

    connected_incidents_list = []
    dates = []
    for inc in connected_incidents_db:
        if inc.timestamp:
            dates.append(inc.timestamp)
        elif inc.created_at:
            dates.append(inc.created_at.strftime("%Y-%m-%d"))
        connected_incidents_list.append({
            "id": inc.id,
            "description": inc.description or f"Cybercrime Incident {inc.id[:8]}",
            "timestamp": inc.timestamp or inc.created_at.strftime("%d %b %Y"),
            "category": inc.category,
            "source": inc.source,
            "location": inc.location or "Unknown"
        })

    # Count neighboring connected entity types across these incidents
    other_props = db.query(Property, IncidentProperty)\
        .join(IncidentProperty, Property.id == IncidentProperty.property_id)\
        .filter(IncidentProperty.incident_id.in_(inc_ids)).all()

    phones = set()
    urls = set()
    locations = set()

    for p, ip in other_props:
        if p.type == "PHONE":
            phones.add(p.normalized_value)
        elif p.type == "URL":
            urls.add(p.normalized_value)
        elif p.type == "LOCATION":
            locations.add(p.normalized_value)

    dates.sort()
    first_obs = dates[0] if dates else "01 Aug 2026"
    last_obs = dates[-1] if dates else "27 Aug 2026"

    return EntityDetailResponse(
        type=entity_type,
        raw_value=props[0].raw_value if props else normalized_value,
        normalized_value=normalized_value,
        connected_incidents_count=len(inc_ids),
        connected_phones_count=len(phones),
        connected_urls_count=len(urls),
        connected_locations_count=len(locations),
        first_observed=first_obs,
        last_observed=last_obs,
        connected_incidents=connected_incidents_list
    )


def sync_all_to_neo4j(db: Session):
    driver=get_neo4j_driver()
    if not driver: return False
    incidents=db.query(Incident).all()
    for inc in incidents:
        rows=db.query(Property,IncidentProperty).join(IncidentProperty,Property.id==IncidentProperty.property_id).filter(IncidentProperty.incident_id==inc.id).all()
        props=[PropertyItem(id=p.id,type=p.type,raw_value=p.raw_value,normalized_value=p.normalized_value,confidence=ip.confidence,source=ip.source) for p,ip in rows]
        add_incident_to_graph(inc.id,inc.timestamp,inc.category,props)
    logger.info("Synchronized %s PostgreSQL incidents to Neo4j",len(incidents))
    return True
