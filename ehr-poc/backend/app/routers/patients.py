from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Patient, Encounter, Observation, Medication, DiagnosticReport, Procedure, ClinicalNote, DischargeSummary
from sqlalchemy import asc

router = APIRouter(prefix="/patients", tags=["patients"])


def patient_to_dict(p):
    return {
        "resourceType": "Patient",
        "id": p.id,
        "mrn": p.mrn,
        "name": {"family": p.last_name, "given": p.first_name},
        "birthDate": p.dob,
        "gender": p.gender,
        "allergies": p.allergies or [],
        "pastMedicalHistory": p.past_medical_history or [],
        "medicationHistory": p.medication_history or [],
    }


def encounter_to_dict(e):
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


@router.get("")
def list_patients(db: Session = Depends(get_db)):
    patients = db.query(Patient).all()
    result = []
    for p in patients:
        enc = db.query(Encounter).filter(Encounter.patient_id == p.id).order_by(Encounter.admission_date.desc()).first()
        d = patient_to_dict(p)
        d["activeEncounter"] = encounter_to_dict(enc) if enc else None
        result.append(d)
    return result


@router.get("/{patient_id}")
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    p = db.query(Patient).filter(Patient.id == patient_id).first()
    if not p:
        return {"error": "Patient not found"}
    d = patient_to_dict(p)
    d["encounters"] = [encounter_to_dict(e) for e in p.encounters]
    return d


@router.get("/{patient_id}/timeline")
def get_timeline(patient_id: str, db: Session = Depends(get_db)):
    events = []

    obs = db.query(Observation).filter(Observation.patient_id == patient_id).order_by(asc(Observation.timestamp)).all()
    for o in obs:
        events.append({"timestamp": o.timestamp.isoformat(), "type": o.type, "resource": "Observation",
            "display": o.display, "value": o.value, "unit": o.unit, "valueString": o.value_string})

    meds = db.query(Medication).filter(Medication.patient_id == patient_id).order_by(asc(Medication.timestamp)).all()
    for m in meds:
        events.append({"timestamp": m.timestamp.isoformat(), "type": "medication", "resource": "Medication",
            "display": m.name, "dose": m.dose, "route": m.route, "frequency": m.frequency, "status": m.status})

    reports = db.query(DiagnosticReport).filter(DiagnosticReport.patient_id == patient_id).order_by(asc(DiagnosticReport.timestamp)).all()
    for r in reports:
        events.append({"timestamp": r.timestamp.isoformat(), "type": "report", "resource": "DiagnosticReport",
            "category": r.category, "display": r.display, "conclusion": r.conclusion})

    procs = db.query(Procedure).filter(Procedure.patient_id == patient_id).order_by(asc(Procedure.timestamp)).all()
    for pr in procs:
        events.append({"timestamp": pr.timestamp.isoformat(), "type": "procedure", "resource": "Procedure",
            "display": pr.display, "performer": pr.performer, "notes": pr.notes})

    notes = db.query(ClinicalNote).filter(ClinicalNote.patient_id == patient_id).order_by(asc(ClinicalNote.timestamp)).all()
    for n in notes:
        events.append({"timestamp": n.timestamp.isoformat(), "type": n.type, "resource": "ClinicalNote",
            "subject": n.subject, "author": n.author, "content": n.content})

    events.sort(key=lambda x: x["timestamp"])
    return {"patientId": patient_id, "events": events}
