from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import DiagnosticReport

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("")
def get_reports(patientId: str = Query(...), db: Session = Depends(get_db)):
    reports = db.query(DiagnosticReport).filter(DiagnosticReport.patient_id == patientId).order_by(DiagnosticReport.timestamp).all()
    return [{"id": r.id, "patientId": r.patient_id, "encounterId": r.encounter_id,
             "timestamp": r.timestamp.isoformat(), "category": r.category, "code": r.code,
             "display": r.display, "findings": r.findings, "conclusion": r.conclusion, "status": r.status} for r in reports]
