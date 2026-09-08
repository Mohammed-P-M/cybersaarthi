from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class PropertyItem(BaseModel):
    id: Optional[str] = None
    type: str # PHONE, UPI, TRANSACTION_ID, URL, EMAIL, IFSC, AMOUNT, LOCATION, PERSON, ORGANIZATION, DATE, TIME, SOCIAL_HANDLE
    raw_value: str
    normalized_value: str
    confidence: float = 1.0
    source: str = "OCR"

class IncidentCreate(BaseModel):
    description: Optional[str] = ""
    timestamp: Optional[str] = None
    location: Optional[str] = None
    source: Optional[str] = "CITIZEN"
    category: Optional[str] = "CYBER_FRAUD"

class EvidenceResponse(BaseModel):
    id: str
    file_name: str
    file_type: str
    storage_path: str
    sha256_hash: str
    ocr_text: Optional[str] = None
    created_at: datetime

class IncidentResponse(BaseModel):
    id: str
    description: Optional[str]
    timestamp: Optional[str]
    source: str
    category: str
    location: Optional[str]
    created_at: datetime
    evidence_items: List[EvidenceResponse] = []
    properties: List[PropertyItem] = []
    related_incidents_count: int = 0

class ProcessResultResponse(BaseModel):
    incident_id: str
    ocr_text: str
    properties: List[PropertyItem]
    database_matches: Dict[str, int] # e.g. {"UPI": 6, "PHONE": 4}
    related_incidents_count: int
    message: str

# Graph / Cytoscape Pydantic models
class CytoscapeNodeData(BaseModel):
    id: str
    label: str
    type: str # Incident, Phone, UPI, Transaction, URL, Email, IFSC, Amount, Location, Person, Organization, SocialHandle
    raw_value: Optional[str] = None
    normalized_value: Optional[str] = None
    connected_count: Optional[int] = 0
    first_observed: Optional[str] = None
    last_observed: Optional[str] = None

class CytoscapeNode(BaseModel):
    data: CytoscapeNodeData

class CytoscapeEdgeData(BaseModel):
    id: str
    source: str
    target: str
    label: str # HAS_PHONE, HAS_UPI, HAS_TRANSACTION, MENTIONS, OCCURRED_AT, etc.
    confidence: Optional[float] = 1.0

class CytoscapeEdge(BaseModel):
    data: CytoscapeEdgeData

class GraphDataResponse(BaseModel):
    nodes: List[CytoscapeNode]
    edges: List[CytoscapeEdge]

class EntityDetailResponse(BaseModel):
    type: str
    raw_value: str
    normalized_value: str
    connected_incidents_count: int
    connected_phones_count: int
    connected_urls_count: int
    connected_locations_count: int
    first_observed: Optional[str]
    last_observed: Optional[str]
    connected_incidents: List[Dict[str, Any]] = []

class ClusterInfo(BaseModel):
    cluster_id: str
    incident_count: int
    property_count: int
    locations: List[str]
    phones: List[str]
    upis: List[str]
    urls: List[str]
    incidents: List[str]
    label: str = "Potential connected activity"

class DashboardStats(BaseModel):
    total_incidents: int
    unique_properties: int
    connected_clusters: int
    new_incidents_today: int
    top_connected_properties: List[Dict[str, Any]]
    recent_incidents: List[Dict[str, Any]]
    property_distribution: Dict[str, int]

class UserAuth(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]
