"""
FHIR R4 endpoints — lightweight compliance for local interoperability.
Supports the discharge summary app patient lookup by name or MRN.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Patient, Encounter, Observation, Medication, DiagnosticReport, Procedure, ClinicalNote

router = APIRouter(prefix="/fhir", tags=["fhir"])


def fhir_patient(p, enc=None):
    resource = {
        "resourceType": "Patient",
        "id": p.id,
        "identifier": [{"system": "urn:oid:hospital.mrn", "value": p.mrn}],
        "name": [{"family": p.last_name, "given": [p.first_name], "use": "official"}],
        "birthDate": p.dob,
        "gender": p.gender,
        "extension": [
            {"url": "allergies", "valueString": str(p.allergies or [])},
            {"url": "pastMedicalHistory", "valueString": ", ".join(p.past_medical_history or [])},
            {"url": "medicationHistory", "valueString": ", ".join(p.medication_history or [])},
        ]
    }
    if enc:
        resource["extension"].append({"url": "activeEncounter", "valueReference": {"reference": f"Encounter/{enc.id}"}})
        resource["extension"].append({"url": "primaryDiagnosis", "valueString": enc.primary_diagnosis})
        resource["extension"].append({"url": "admissionDate", "valueDateTime": enc.admission_date.isoformat() if enc.admission_date else None})
        resource["extension"].append({"url": "encounterStatus", "valueString": enc.status})
    return resource


def fhir_encounter(e):
    return {
        "resourceType": "Encounter",
        "id": e.id,
        "status": e.status,
        "subject": {"reference": f"Patient/{e.patient_id}"},
        "period": {
            "start": e.admission_date.isoformat() if e.admission_date else None,
            "end": e.discharge_date.isoformat() if e.discharge_date else None,
        },
        "reasonCode": [{"text": e.admission_reason}],
        "diagnosis": [{"condition": {"display": e.primary_diagnosis}}],
    }


@router.get("/Patient")
def search_patients(
    name: str = Query(None, description="Patient name (partial match on first or last name)"),
    identifier: str = Query(None, description="MRN e.g. MRN-001001"),
    _count: int = Query(20),
    db: Session = Depends(get_db)
):
    """FHIR Patient search — supports ?name= and ?identifier= for discharge app lookup."""
    query = db.query(Patient)
    if name:
        term = f"%{name.lower()}%"
        from sqlalchemy import func
        query = query.filter(
            (func.lower(Patient.first_name).like(term)) |
            (func.lower(Patient.last_name).like(term))
        )
    if identifier:
        query = query.filter(Patient.mrn == identifier)

    patients = query.limit(_count).all()
    entries = []
    for p in patients:
        enc = db.query(Encounter).filter(Encounter.patient_id == p.id, Encounter.status == "active").first()
        entries.append({"resource": fhir_patient(p, enc)})

    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": len(entries),
        "entry": entries
    }


@router.get("/Patient/{patient_id}")
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    p = db.query(Patient).filter(Patient.id == patient_id).first()
    if not p:
        return {"resourceType": "OperationOutcome", "issue": [{"severity": "error", "details": {"text": "Patient not found"}}]}
    enc = db.query(Encounter).filter(Encounter.patient_id == p.id, Encounter.status == "active").first()
    return fhir_patient(p, enc)


@router.get("/Patient/{patient_id}/context")
def get_patient_context_fhir(patient_id: str, db: Session = Depends(get_db)):
    """
    Full clinical context bundle for this patient — used by the discharge summary app
    to pre-populate the summary form.
    """
    p = db.query(Patient).filter(Patient.id == patient_id).first()
    if not p:
        return {"error": "Patient not found"}

    enc = db.query(Encounter).filter(Encounter.patient_id == patient_id, Encounter.status == "active").first()
    if not enc:
        enc = db.query(Encounter).filter(Encounter.patient_id == patient_id).order_by(Encounter.admission_date.desc()).first()

    observations = db.query(Observation).filter(Observation.patient_id == patient_id).order_by(Observation.timestamp).all()
    medications = db.query(Medication).filter(Medication.patient_id == patient_id).order_by(Medication.timestamp).all()
    reports = db.query(DiagnosticReport).filter(DiagnosticReport.patient_id == patient_id).order_by(DiagnosticReport.timestamp).all()
    procedures = db.query(Procedure).filter(Procedure.patient_id == patient_id).order_by(Procedure.timestamp).all()
    notes = db.query(ClinicalNote).filter(ClinicalNote.patient_id == patient_id).order_by(ClinicalNote.timestamp).all()

    # Latest labs
    latest_labs = {}
    for o in observations:
        if o.type == "lab":
            latest_labs[o.display] = {"value": o.value, "unit": o.unit, "timestamp": o.timestamp.isoformat()}

    # Latest vitals
    latest_vitals = {}
    for o in observations:
        if o.type == "vital-signs":
            latest_vitals[o.display] = {"value": o.value, "unit": o.unit, "timestamp": o.timestamp.isoformat()}

    active_meds = [m for m in medications if m.status == "active"]

    return {
        "resourceType": "Bundle",
        "type": "patient-context",
        "patient": {
            "id": p.id,
            "mrn": p.mrn,
            "name": f"{p.first_name} {p.last_name}",
            "dob": p.dob,
            "gender": p.gender,
            "allergies": p.allergies or [],
            "pastMedicalHistory": p.past_medical_history or [],
            "medicationHistory": p.medication_history or [],
        },
        "encounter": fhir_encounter(enc) if enc else None,
        "latestVitals": latest_vitals,
        "latestLabs": latest_labs,
        "activeMedications": [
            {"name": m.name, "dose": m.dose, "route": m.route, "frequency": m.frequency, "indication": m.indication}
            for m in active_meds
        ],
        "diagnosticReports": [
            {"timestamp": r.timestamp.isoformat(), "category": r.category, "display": r.display,
             "findings": r.findings, "conclusion": r.conclusion}
            for r in reports
        ],
        "procedures": [
            {"timestamp": pr.timestamp.isoformat(), "display": pr.display, "performer": pr.performer, "notes": pr.notes}
            for pr in procedures
        ],
        "clinicalNotes": [
            {"timestamp": n.timestamp.isoformat(), "type": n.type, "author": n.author, "subject": n.subject, "content": n.content}
            for n in notes
        ],
    }


@router.get("/Encounter/{encounter_id}")
def get_encounter(encounter_id: str, db: Session = Depends(get_db)):
    e = db.query(Encounter).filter(Encounter.id == encounter_id).first()
    if not e:
        return {"resourceType": "OperationOutcome", "issue": [{"severity": "error", "details": {"text": "Not found"}}]}
    return fhir_encounter(e)


@router.post("/Composition")
def store_discharge_summary_fhir(payload: dict, db: Session = Depends(get_db)):
    """
    Accepts a FHIR Composition resource (discharge summary) and saves it to the EHR.
    Called by the discharge summary app when saving back to the EHR.
    """
    from app.models.models import DischargeSummary
    from datetime import datetime

    patient_ref = payload.get("subject", {}).get("reference", "")
    patient_id = patient_ref.replace("Patient/", "") if patient_ref else None
    enc_ref = payload.get("encounter", {}).get("reference", "")
    encounter_id = enc_ref.replace("Encounter/", "") if enc_ref else None

    if not patient_id:
        return {"error": "subject.reference required"}

    text_sections = []
    for section in payload.get("section", []):
        title = section.get("title", "")
        text = section.get("text", {}).get("div", "")
        text_sections.append(f"## {title}\n{text}")
    summary_text = "\n\n".join(text_sections) or payload.get("title", "")

    summary = DischargeSummary(
        patient_id=patient_id,
        encounter_id=encounter_id,
        created_at=datetime.utcnow(),
        summary_text=summary_text,
        structured_data=payload,
        generated_by="discharge-app"
    )
    db.add(summary)

    # Only mark encounter as discharged when explicitly requested via markDischarged flag.
    # A plain FHIR save must NOT change encounter status.
    if encounter_id and payload.get("markDischarged") is True:
        today = datetime.utcnow()
        enc = db.query(Encounter).filter(Encounter.id == encounter_id).first()
        if enc:
            enc.status = "discharged"
            end_date = None
            for ev in payload.get("event", []):
                end_date = ev.get("period", {}).get("end")
                if end_date:
                    break
            try:
                enc.discharge_date = datetime.fromisoformat(end_date) if end_date else today
            except Exception:
                enc.discharge_date = today

    db.commit()
    db.refresh(summary)
    return {"resourceType": "Composition", "id": summary.id, "status": "final"}


@router.post("/note")
def save_clinical_note(payload: dict, db: Session = Depends(get_db)):
    """
    Saves a discharge summary as a clinical note in the EHR.
    Called by the discharge summary app — label is always 'Discharge Summary Notes'.
    """
    from app.models.models import ClinicalNote
    from datetime import datetime

    patient_id = payload.get("patientId")
    encounter_id = payload.get("encounterId")
    if not patient_id:
        return {"error": "patientId required"}

    ts_raw = payload.get("timestamp")
    try:
        ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00")) if ts_raw else datetime.utcnow()
    except Exception:
        ts = datetime.utcnow()

    note = ClinicalNote(
        patient_id=patient_id,
        encounter_id=encounter_id,
        timestamp=ts,
        type="discharge-summary",
        author=payload.get("author", "Attending Physician"),
        subject="Discharge Summary Notes",
        content=payload.get("content", "")
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return {"id": note.id, "status": "saved", "subject": "Discharge Summary Notes", "timestamp": ts.isoformat()}
