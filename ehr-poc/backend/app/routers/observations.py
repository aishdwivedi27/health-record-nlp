from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Observation

router = APIRouter(prefix="/observations", tags=["observations"])


@router.get("")
def get_observations(patientId: str = Query(...), db: Session = Depends(get_db)):
    obs = db.query(Observation).filter(Observation.patient_id == patientId).order_by(Observation.timestamp).all()
    return [{"id": o.id, "patientId": o.patient_id, "encounterId": o.encounter_id,
             "timestamp": o.timestamp.isoformat(), "type": o.type, "code": o.code,
             "display": o.display, "value": o.value, "unit": o.unit, "status": o.status} for o in obs]
