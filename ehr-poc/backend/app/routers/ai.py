from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Any, Optional
from app.database import get_db
from app.models.models import Patient, Encounter, Observation, Medication, DiagnosticReport, Procedure, ClinicalNote, DischargeSummary
from datetime import datetime

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/patient-context/{patient_id}")
def get_patient_context(patient_id: str, db: Session = Depends(get_db)):
    """Full longitudinal structured dataset for LLM consumption."""
    p = db.query(Patient).filter(Patient.id == patient_id).first()
    if not p:
        return {"error": "Patient not found"}

    encounters = db.query(Encounter).filter(Encounter.patient_id == patient_id).all()
    observations = db.query(Observation).filter(Observation.patient_id == patient_id).order_by(Observation.timestamp).all()
    medications = db.query(Medication).filter(Medication.patient_id == patient_id).order_by(Medication.timestamp).all()
    reports = db.query(DiagnosticReport).filter(DiagnosticReport.patient_id == patient_id).order_by(DiagnosticReport.timestamp).all()
    procedures = db.query(Procedure).filter(Procedure.patient_id == patient_id).order_by(Procedure.timestamp).all()
    notes = db.query(ClinicalNote).filter(ClinicalNote.patient_id == patient_id).order_by(ClinicalNote.timestamp).all()

    return {
        "resourceType": "Bundle",
        "type": "longitudinal-patient-context",
        "patient": {
            "id": p.id, "mrn": p.mrn,
            "name": f"{p.first_name} {p.last_name}",
            "dob": p.dob, "gender": p.gender,
            "allergies": p.allergies,
            "pastMedicalHistory": p.past_medical_history,
            "medicationHistory": p.medication_history,
        },
        "encounters": [{"id": e.id, "admissionDate": e.admission_date.isoformat(),
                        "dischargeDate": e.discharge_date.isoformat() if e.discharge_date else None,
                        "status": e.status, "primaryDiagnosis": e.primary_diagnosis,
                        "admissionReason": e.admission_reason} for e in encounters],
        "observations": [{"timestamp": o.timestamp.isoformat(), "type": o.type,
                          "display": o.display, "value": o.value, "unit": o.unit} for o in observations],
        "medications": [{"timestamp": m.timestamp.isoformat(), "name": m.name,
                         "dose": m.dose, "route": m.route, "frequency": m.frequency,
                         "status": m.status, "indication": m.indication} for m in medications],
        "diagnosticReports": [{"timestamp": r.timestamp.isoformat(), "category": r.category,
                                "display": r.display, "findings": r.findings, "conclusion": r.conclusion} for r in reports],
        "procedures": [{"timestamp": pr.timestamp.isoformat(), "display": pr.display,
                        "performer": pr.performer, "notes": pr.notes} for pr in procedures],
        "clinicalNotes": [{"timestamp": n.timestamp.isoformat(), "type": n.type,
                           "author": n.author, "subject": n.subject, "content": n.content} for n in notes],
    }


@router.get("/discharge-ready/{encounter_id}")
def discharge_ready(encounter_id: str, db: Session = Depends(get_db)):
    """Summarisation-ready bundle for discharge summary generation."""
    e = db.query(Encounter).filter(Encounter.id == encounter_id).first()
    if not e:
        return {"error": "Encounter not found"}

    p = db.query(Patient).filter(Patient.id == e.patient_id).first()
    notes = db.query(ClinicalNote).filter(ClinicalNote.encounter_id == encounter_id).order_by(ClinicalNote.timestamp).all()
    reports = db.query(DiagnosticReport).filter(DiagnosticReport.encounter_id == encounter_id).all()
    meds = db.query(Medication).filter(Medication.encounter_id == encounter_id).all()
    procs = db.query(Procedure).filter(Procedure.encounter_id == encounter_id).all()

    # Most recent vitals per type
    from sqlalchemy import func
    latest_labs = db.query(Observation).filter(
        Observation.encounter_id == encounter_id,
        Observation.type == "lab"
    ).order_by(Observation.timestamp.desc()).limit(10).all()

    return {
        "resourceType": "Bundle",
        "type": "discharge-ready",
        "encounter": {
            "id": e.id,
            "admissionDate": e.admission_date.isoformat(),
            "dischargeDate": e.discharge_date.isoformat() if e.discharge_date else None,
            "primaryDiagnosis": e.primary_diagnosis,
            "admissionReason": e.admission_reason,
        },
        "patient": {
            "id": p.id, "mrn": p.mrn,
            "name": f"{p.first_name} {p.last_name}",
            "dob": p.dob, "gender": p.gender,
            "allergies": p.allergies,
            "pastMedicalHistory": p.past_medical_history,
        },
        "clinicalNotes": [{"timestamp": n.timestamp.isoformat(), "type": n.type,
                           "author": n.author, "subject": n.subject, "content": n.content} for n in notes],
        "diagnosticReports": [{"timestamp": r.timestamp.isoformat(), "category": r.category,
                                "display": r.display, "findings": r.findings, "conclusion": r.conclusion} for r in reports],
        "medications": [{"name": m.name, "dose": m.dose, "route": m.route,
                         "frequency": m.frequency, "status": m.status, "indication": m.indication} for m in meds],
        "procedures": [{"timestamp": pr.timestamp.isoformat(), "display": pr.display,
                        "performer": pr.performer, "notes": pr.notes} for pr in procs],
        "latestLabs": [{"timestamp": o.timestamp.isoformat(), "display": o.display,
                        "value": o.value, "unit": o.unit} for o in latest_labs],
    }


class DischargeSummaryInput(BaseModel):
    patientId: str
    encounterId: str
    summaryText: str
    structuredData: Optional[Any] = None


@router.post("/discharge-summary")
def store_discharge_summary(payload: DischargeSummaryInput, db: Session = Depends(get_db)):
    summary = DischargeSummary(
        patient_id=payload.patientId,
        encounter_id=payload.encounterId,
        created_at=datetime.utcnow(),
        summary_text=payload.summaryText,
        structured_data=payload.structuredData,
        generated_by="llm"
    )
    db.add(summary)
    db.commit()
    db.refresh(summary)
    return {"id": summary.id, "status": "stored", "generatedBy": "llm"}
