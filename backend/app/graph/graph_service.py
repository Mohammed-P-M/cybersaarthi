import logging
from typing import List, Dict, Any
from app.db.session import neo4j_conn

logger = logging.getLogger("cybersaarthi.graph")

RELATIONSHIP_MAP = {
    "PHONE": "HAS_PHONE",
    "UPI": "HAS_UPI",
    "TRANSACTION_ID": "HAS_TRANSACTION",
    "URL": "HAS_URL",
    "EMAIL": "HAS_EMAIL",
    "IFSC": "HAS_IFSC",
    "AMOUNT": "HAS_AMOUNT",
    "LOCATION": "OCCURRED_AT",
    "PERSON": "MENTIONS",
    "ORGANIZATION": "MENTIONS",
    "SOCIAL_HANDLE": "HAS_SOCIAL_HANDLE",
    "CRIME_CATEGORY": "HAS_CATEGORY",
}

NODE_LABEL_MAP = {
    "PHONE": "Phone", "UPI": "UPI", "TRANSACTION_ID": "Transaction", "URL": "URL",
    "EMAIL": "Email", "IFSC": "IFSC", "AMOUNT": "Amount", "LOCATION": "Location",
    "PERSON": "Person", "ORGANIZATION": "Organization", "SOCIAL_HANDLE": "SocialHandle",
    "CRIME_CATEGORY": "CrimeCategory",
}

class InMemoryGraphEngine:
    def __init__(self):
        self.nodes = {}
        self.edges = []

    def add_incident_node(self, incident_id: str, props: Dict[str, Any]):
        self.nodes[incident_id] = {"id": incident_id, "label": "Incident", "type": "Incident", "properties": props}

    def add_property_and_connect(self, incident_id: str, prop_type: str, raw_value: str, norm_value: str):
        label = NODE_LABEL_MAP.get(prop_type, "Property")
        rel_type = RELATIONSHIP_MAP.get(prop_type, "HAS_PROPERTY")
        prop_node_id = f"{prop_type}:{norm_value}"
        if prop_node_id not in self.nodes:
            self.nodes[prop_node_id] = {"id": prop_node_id, "label": label, "type": prop_type,
                                        "properties": {"raw_value": raw_value, "normalized_value": norm_value, "type": prop_type}}
        edge_id = f"{incident_id}->{prop_node_id}"
        if not any(e["source"] == incident_id and e["target"] == prop_node_id for e in self.edges):
            self.edges.append({"id": edge_id, "source": incident_id, "target": prop_node_id, "rel_type": rel_type})

    def get_incident_graph(self, incident_id: str) -> Dict[str, Any]:
        sub_nodes = {incident_id} if incident_id in self.nodes else set()
        sub_edges = []
        connected_prop_ids = set()
        for e in self.edges:
            if e["source"] == incident_id:
                sub_edges.append(e); connected_prop_ids.add(e["target"])
        for prop_id in connected_prop_ids:
            sub_nodes.add(prop_id)
            for e in self.edges:
                if e["target"] == prop_id:
                    sub_nodes.add(e["source"])
                    if e not in sub_edges:
                        sub_edges.append(e)
        return {"nodes": [self.nodes[n] for n in sub_nodes if n in self.nodes], "edges": sub_edges}

fallback_graph = InMemoryGraphEngine()

class GraphService:
    def metadata_property(self, prop_type: str, raw_value: str, norm_value: str, confidence: float = 1.0, source: str = "REPORT"):
        return {
            "id": f"meta_{prop_type}_{abs(hash(norm_value)) % 10**10}",
            "type": prop_type,
            "raw_value": raw_value,
            "normalized_value": norm_value,
            "confidence": confidence,
            "source": source,
        }

    def sync_incident_to_graph(self, incident_id: str, metadata: Dict[str, Any], properties: List[Dict[str, Any]]):
        fallback_graph.add_incident_node(incident_id, metadata)
        for p in properties:
            fallback_graph.add_property_and_connect(incident_id, p["type"], p["raw_value"], p["normalized_value"])

        if not neo4j_conn.driver:
            return

        with neo4j_conn.driver.session() as session:
            session.run(
                """
                MERGE (i:Incident {id: $incident_id})
                SET i.description = $description,
                    i.timestamp = $timestamp,
                    i.category = $category,
                    i.location = $location
                """,
                incident_id=incident_id,
                description=metadata.get("description", "") or "",
                timestamp=str(metadata.get("timestamp", "")),
                category=metadata.get("category", "OTHER") or "OTHER",
                location=metadata.get("location"),
            )
            for prop in properties:
                ptype = prop["type"]
                label = NODE_LABEL_MAP.get(ptype, "Property")
                rel_type = RELATIONSHIP_MAP.get(ptype, "HAS_PROPERTY")
                session.run(
                    f"""
                    MATCH (i:Incident {{id: $incident_id}})
                    MERGE (p:{label} {{normalized_value: $norm_val}})
                    SET p.raw_value = $raw_val, p.type = $ptype
                    MERGE (i)-[:{rel_type}]->(p)
                    """,
                    incident_id=incident_id,
                    norm_val=prop["normalized_value"],
                    raw_val=prop["raw_value"],
                    ptype=ptype,
                )

    def get_graph_for_incident(self, incident_id: str) -> Dict[str, Any]:
        if not neo4j_conn.driver:
            return fallback_graph.get_incident_graph(incident_id)
        cypher = """
        MATCH (i:Incident {id: $incident_id})-[r1]-(p)-[r2]-(i2:Incident)
        RETURN i, r1, p, r2, i2
        """
        nodes_dict, edges_list = {}, []
        with neo4j_conn.driver.session() as session:
            for record in session.run(cypher, incident_id=incident_id):
                i, p, i2 = record["i"], record["p"], record["i2"]
                nodes_dict[i["id"]] = {"id": i["id"], "label": "Incident", "type": "Incident", "properties": dict(i)}
                prop_id = f"{p['type']}:{p['normalized_value']}"
                nodes_dict[prop_id] = {"id": prop_id, "label": p["type"], "type": p["type"], "properties": dict(p)}
                nodes_dict[i2["id"]] = {"id": i2["id"], "label": "Incident", "type": "Incident", "properties": dict(i2)}
                edges_list.extend([
                    {"id": f"{i['id']}->{prop_id}", "source": i["id"], "target": prop_id, "rel_type": record["r1"].type},
                    {"id": f"{i2['id']}->{prop_id}", "source": i2["id"], "target": prop_id, "rel_type": record["r2"].type},
                ])
        return {"nodes": list(nodes_dict.values()), "edges": edges_list} if nodes_dict else fallback_graph.get_incident_graph(incident_id)

graph_service = GraphService()
