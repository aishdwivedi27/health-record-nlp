from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Encounter

router = APIRouter(prefix="/encounters", tags=["encounters"])


@router.get("/{encounter_id}")
def get_encounter(encounter_id: str, db: Session = Depends(get_db)):
    e = db.query(Encounter).filter(Encounter.id == encounter_id).first()
    if not e:
        return {"error": "Encounter not found"}
    return {
        "resourceType": "Encounter",
        "id": e.id,
        "patientId": e.patient_id,
        "admissionDate": e.admission_date.isoformat() if e.admission_date else None,
        "dischargeDate": e.discharge_date.isoformat() if e.discharge_date else None,
        "status": e.status,
        "primaryDiagnosis": e.primary_diagnosis,
        "admissionReason": e.admission_reason,
    }
