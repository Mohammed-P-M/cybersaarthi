import datetime
from sqlalchemy import Column, String, Text, DateTime, Float, ForeignKey, Table
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class IncidentProperty(Base):
    __tablename__ = "incident_properties"
    
    incident_id = Column(String(64), ForeignKey("incidents.id"), primary_key=True)
    property_id = Column(String(64), ForeignKey("properties.id"), primary_key=True)
    confidence = Column(Float, default=1.0)
    source = Column(String(64), default="OCR")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Incident(Base):
    __tablename__ = "incidents"
    
    id = Column(String(64), primary_key=True)
    description = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    source = Column(String(64), default="CITIZEN_REPORT")
    category = Column(String(64), default="CYBER_FRAUD")
    location = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    evidence_files = relationship("Evidence", back_populates="incident", cascade="all, delete-orphan")
    properties = relationship("Property", secondary="incident_properties", back_populates="incidents")

class Evidence(Base):
    __tablename__ = "evidence"
    
    id = Column(String(64), primary_key=True)
    incident_id = Column(String(64), ForeignKey("incidents.id"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(64), nullable=False)
    storage_path = Column(String(512), nullable=False)
    sha256_hash = Column(String(64), nullable=False)
    ocr_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationship
    incident = relationship("Incident", back_populates="evidence_files")

class Property(Base):
    __tablename__ = "properties"
    
    id = Column(String(64), primary_key=True)
    type = Column(String(64), nullable=False, index=True) # PHONE, UPI, TRANSACTION_ID, URL, EMAIL, IFSC, AMOUNT, LOCATION, PERSON, ORGANIZATION, DATE, TIME, SOCIAL_HANDLE
    raw_value = Column(String(255), nullable=False)
    normalized_value = Column(String(255), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationship
    incidents = relationship("Incident", secondary="incident_properties", back_populates="properties")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(String(64), primary_key=True)
    user_id = Column(String(64), nullable=False, default="system")
    action = Column(String(128), nullable=False)
    resource_type = Column(String(64), nullable=False)
    resource_id = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
