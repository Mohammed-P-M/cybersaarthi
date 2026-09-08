from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

class PropertyBase(BaseModel):
    type: str
    raw_value: str
    normalized_value: str
    confidence: float = 1.0
    source: str = "OCR"

class PropertyResponse(PropertyBase):
    id: str
    created_at: Optional[datetime] = None

class EvidenceResponse(BaseModel):
    id: str
    incident_id: str
    file_name: str
    file_type: str
    storage_path: str
    sha256_hash: str
    ocr_text: Optional[str] = None
    created_at: Optional[datetime] = None

class IncidentCreate(BaseModel):
    description: Optional[str] = None
    location: Optional[str] = None
    category: Optional[str] = "CYBER_FRAUD"

class IncidentResponse(BaseModel):
    id: str
    description: Optional[str] = None
    timestamp: datetime
    source: str
    category: str
    location: Optional[str] = None
    created_at: datetime
    properties: List[PropertyResponse] = []
    evidence_files: List[EvidenceResponse] = []

class SearchEntityResult(BaseModel):
    query: str
    total_connected_incidents: int
    connected_properties_count: int
    properties: List[PropertyResponse]
    incidents: List[IncidentResponse]

class DashboardMetrics(BaseModel):
    total_incidents: int
    unique_properties: int
    connected_clusters: int
    new_incidents: int
    most_connected_properties: List[Any]
    recent_incidents: List[Any]
    location_distribution: List[Any]
    category_distribution: List[Any]
