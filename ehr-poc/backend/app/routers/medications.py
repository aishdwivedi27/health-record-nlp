from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Medication

router = APIRouter(prefix="/medications", tags=["medications"])


@router.get("")
def get_medications(patientId: str = Query(...), db: Session = Depends(get_db)):
    meds = db.query(Medication).filter(Medication.patient_id == patientId).order_by(Medication.timestamp).all()
    return [{"id": m.id, "patientId": m.patient_id, "encounterId": m.encounter_id,
             "timestamp": m.timestamp.isoformat(), "name": m.name, "dose": m.dose,
             "route": m.route, "frequency": m.frequency, "status": m.status, "indication": m.indication} for m in meds]
