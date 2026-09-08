import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Float, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.core.postgres import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="INVESTIGATOR")
    created_at = Column(DateTime, default=datetime.utcnow)

class IncidentProperty(Base):
    __tablename__ = "incident_properties"

    incident_id = Column(String, ForeignKey("incidents.id", ondelete="CASCADE"), primary_key=True)
    property_id = Column(String, ForeignKey("properties.id", ondelete="CASCADE"), primary_key=True)
    confidence = Column(Float, default=1.0)
    source = Column(String, default="OCR")

    incident = relationship("Incident", back_populates="incident_properties")
    property = relationship("Property", back_populates="incident_properties")

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String, primary_key=True, default=generate_uuid)
    description = Column(Text, nullable=True)
    timestamp = Column(String, nullable=True)
    source = Column(String, default="CITIZEN") # CITIZEN, SYNTHETIC, LAW_ENFORCEMENT
    category = Column(String, default="CYBER_FRAUD")
    location = Column(String, nullable=True)
    status = Column(String, default="NEW")
    created_at = Column(DateTime, default=datetime.utcnow)

    evidence_items = relationship("Evidence", back_populates="incident", cascade="all, delete-orphan")
    incident_properties = relationship("IncidentProperty", back_populates="incident", cascade="all, delete-orphan")

class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(String, primary_key=True, default=generate_uuid)
    incident_id = Column(String, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    file_name = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    sha256_hash = Column(String, nullable=False)
    ocr_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    incident = relationship("Incident", back_populates="evidence_items")

class Property(Base):
    __tablename__ = "properties"

    id = Column(String, primary_key=True, default=generate_uuid)
    type = Column(String, index=True, nullable=False) # PHONE, UPI, TRANSACTION_ID, URL, EMAIL, IFSC, AMOUNT, LOCATION, PERSON, ORGANIZATION, DATE, TIME, SOCIAL_HANDLE
    raw_value = Column(String, nullable=False)
    normalized_value = Column(String, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    incident_properties = relationship("IncidentProperty", back_populates="property", cascade="all, delete-orphan")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, nullable=True)
    action = Column(String, nullable=False)
    resource_type = Column(String, nullable=False)
    resource_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
