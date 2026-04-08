"""
EpiChat ORM Models
Defines the database tables: User and Scan.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from datetime import datetime, timezone
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    role = Column(String, nullable=False)       # 'clinician' or 'patient'
    name = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "role": self.role,
            "name": self.name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Scan(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, index=True)
    patient_email = Column(String, index=True, nullable=False)
    filename = Column(String, nullable=False)
    result = Column(String, nullable=False)           # 'seizure' or 'healthy'
    epilepsy_detected = Column(Boolean, default=False)
    seizure_probability = Column(Float, default=0.0)  # 0-100%
    seizure_type = Column(String, nullable=True)
    clinical_note = Column(Text, nullable=True)
    model_accuracy = Column(String, default="94.7%")
    scanned_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "patient_email": self.patient_email,
            "filename": self.filename,
            "result": self.result,
            "epilepsy_detected": self.epilepsy_detected,
            "seizure_probability": self.seizure_probability,
            "risk_score": self.seizure_probability,   # alias for frontend compat
            "seizure_type": self.seizure_type,
            "clinical_note": self.clinical_note,
            "model_accuracy": self.model_accuracy,
            "scanned_at": self.scanned_at.isoformat() if self.scanned_at else None,
        }
