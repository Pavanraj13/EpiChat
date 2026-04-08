from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.db_models import Scan
from typing import List

router = APIRouter(prefix="/api/records", tags=["records"])

@router.get("/", response_model=List[dict])
def get_records(email: str, db: Session = Depends(get_db)):
    """Fetch all scan records for a specific user email."""
    records = db.query(Scan).filter(Scan.patient_email == email).order_by(Scan.scanned_at.desc()).all()
    return [r.to_dict() for r in records]

@router.get("/latest")
def get_latest_record(email: str, db: Session = Depends(get_db)):
    """Fetch the most recent scan record for a specific user email."""
    record = db.query(Scan).filter(Scan.patient_email == email).order_by(Scan.scanned_at.desc()).first()
    if not record:
        return {"result": None}
    return record.to_dict()
