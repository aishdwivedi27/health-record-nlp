"""
Seed script — 3 synthetic ACTIVE inpatients.
Patient 1: Appendicitis (Day 2 of admission — post-op)
Patient 2: Community-acquired pneumonia + cardiac workup (Day 3)
Patient 3: Hip fracture, awaiting/post surgery (Day 2)
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from datetime import datetime, timedelta
from app.database import engine, SessionLocal
from app.models.models import Base, Patient, Encounter, Observation, Medication, DiagnosticReport, Procedure, ClinicalNote, DischargeSummary
import uuid

Base.metadata.create_all(bind=engine)

def gen_id(): return str(uuid.uuid4())
def dt(base, days=0, hours=0): return base + timedelta(days=days, hours=hours)

# Admissions are recent — relative to "now" so they're always current
NOW = datetime.utcnow()
P1_ADMIT = NOW - timedelta(days=2, hours=4)
P2_ADMIT = NOW - timedelta(days=3, hours=8)
P3_ADMIT = NOW - timedelta(days=2, hours=1)

def seed():
    db = SessionLocal()
    for model in [DischargeSummary, ClinicalNote, Procedure, DiagnosticReport, Medication, Observation, Encounter, Patient]:
        db.query(model).delete()
    db.commit()

    # ─────────────────────────────────────────────
    # PATIENT 1 — James Harrington — Appendicitis (active, post-op day 2)
    # ─────────────────────────────────────────────
    p1_id = gen_id()
    db.add(Patient(
        id=p1_id, first_name="James", last_name="Harrington", dob="1988-03-14",
        gender="male", mrn="MRN-001001",
        allergies=[{"substance": "Penicillin", "reaction": "Rash", "severity": "moderate"}],
        past_medical_history=["Nil significant"],
        medication_history=["Nil regular medications"]
    ))
    enc1_id = gen_id()
    db.add(Encounter(
        id=enc1_id, patient_id=p1_id,
        admission_date=P1_ADMIT,
        discharge_date=None,
        status="active",
        primary_diagnosis="Acute appendicitis",
        admission_reason="Acute right iliac fossa pain, nausea, fever"
    ))

    vitals_p1 = [
        (dt(P1_ADMIT), "8867-4", "Heart rate", 108, "bpm"),
        (dt(P1_ADMIT), "8310-5", "Body temperature", 38.4, "Cel"),
        (dt(P1_ADMIT), "55284-4", "Blood pressure systolic", 128, "mmHg"),
        (dt(P1_ADMIT), "59408-5", "SpO2", 98, "%"),
        (dt(P1_ADMIT, hours=6), "8867-4", "Heart rate", 112, "bpm"),
        (dt(P1_ADMIT, hours=6), "8310-5", "Body temperature", 38.7, "Cel"),
        (dt(P1_ADMIT, days=1, hours=6), "8867-4", "Heart rate", 96, "bpm"),
        (dt(P1_ADMIT, days=1, hours=6), "8310-5", "Body temperature", 37.8, "Cel"),
        (dt(P1_ADMIT, days=1, hours=14), "8867-4", "Heart rate", 90, "bpm"),
        (dt(P1_ADMIT, days=1, hours=14), "8310-5", "Body temperature", 37.4, "Cel"),
        (dt(P1_ADMIT, days=2, hours=6), "8867-4", "Heart rate", 84, "bpm"),
        (dt(P1_ADMIT, days=2, hours=6), "8310-5", "Body temperature", 37.1, "Cel"),
        (dt(P1_ADMIT, days=2, hours=6), "59408-5", "SpO2", 99, "%"),
    ]
    for ts, code, display, val, unit in vitals_p1:
        db.add(Observation(id=gen_id(), patient_id=p1_id, encounter_id=enc1_id,
            timestamp=ts, type="vital-signs", code=code, display=display, value=val, unit=unit))

    labs_p1 = [
        (dt(P1_ADMIT, hours=1), "6690-2", "WBC", 15.2, "10*3/uL"),
        (dt(P1_ADMIT, hours=1), "718-7", "Haemoglobin", 142, "g/L"),
        (dt(P1_ADMIT, hours=1), "1988-5", "CRP", 88, "mg/L"),
        (dt(P1_ADMIT, days=1, hours=6), "6690-2", "WBC", 17.4, "10*3/uL"),
        (dt(P1_ADMIT, days=1, hours=6), "1988-5", "CRP", 142, "mg/L"),
        (dt(P1_ADMIT, days=1, hours=6), "718-7", "Haemoglobin", 128, "g/L"),
        (dt(P1_ADMIT, days=2, hours=6), "6690-2", "WBC", 12.1, "10*3/uL"),
        (dt(P1_ADMIT, days=2, hours=6), "1988-5", "CRP", 95, "mg/L"),
    ]
    for ts, code, display, val, unit in labs_p1:
        db.add(Observation(id=gen_id(), patient_id=p1_id, encounter_id=enc1_id,
            timestamp=ts, type="lab", code=code, display=display, value=val, unit=unit))

    db.add(DiagnosticReport(id=gen_id(), patient_id=p1_id, encounter_id=enc1_id,
        timestamp=dt(P1_ADMIT, hours=2), category="imaging", code="CT-ABD-PEL",
        display="CT Abdomen and Pelvis with contrast",
        findings="Distended appendix measuring 11mm. Periappendiceal fat stranding. No perforation.",
        conclusion="Acute uncomplicated appendicitis.", status="final"))

    db.add(Procedure(id=gen_id(), patient_id=p1_id, encounter_id=enc1_id,
        timestamp=dt(P1_ADMIT, hours=4), code="80146006", display="Laparoscopic appendectomy",
        status="completed", performer="Dr R. Chen (General Surgery)",
        notes="Three-port laparoscopic approach. Retrocaecal appendix, acutely inflamed, intact. Ligated with EndoGIA stapler. EBL <50mL. No complications."))

    meds_p1 = [
        (dt(P1_ADMIT, hours=1), "Cefazolin 2g IV", "2g", "IV", "Pre-op single dose", "completed", "Surgical prophylaxis"),
        (dt(P1_ADMIT, days=1), "Cefazolin 1g IV", "1g", "IV", "Q8H", "active", "Post-op antibiotics"),
        (dt(P1_ADMIT, days=1), "Metronidazole 400mg PO", "400mg", "oral", "TDS", "active", "Anaerobic cover"),
        (dt(P1_ADMIT, hours=1), "Morphine 2.5mg IV PRN", "2.5mg", "IV", "Q4H PRN", "active", "Pain"),
        (dt(P1_ADMIT, days=1), "Paracetamol 1g IV", "1g", "IV", "Q6H", "active", "Analgesia"),
        (dt(P1_ADMIT, days=1), "Ibuprofen 400mg PO", "400mg", "oral", "TDS with food", "active", "Analgesia"),
    ]
    for ts, name, dose, route, freq, status, indication in meds_p1:
        db.add(Medication(id=gen_id(), patient_id=p1_id, encounter_id=enc1_id,
            timestamp=ts, name=name, dose=dose, route=route, frequency=freq, status=status, indication=indication))

    notes_p1 = [
        (dt(P1_ADMIT), "progress-note", "Dr S. Patel (ED)", "ED Assessment",
         "28M with 18h periumbilical pain migrating to RIF, nausea, vomiting x1. Temp 38.4, HR 108. Guarding and rebound at McBurney's. Rovsing's positive. WBC 15.2, CRP 88. CT confirms acute appendicitis. Surgical consult called. NBM, IV access, analgesia."),
        (dt(P1_ADMIT, hours=3), "consult", "Dr R. Chen (General Surgery)", "Surgical Consult",
         "CT-confirmed acute appendicitis. No perforation. Consented for laparoscopic appendectomy. Proceeding to theatre tonight."),
        (dt(P1_ADMIT, days=1, hours=8), "progress-note", "Dr R. Chen (General Surgery)", "Post-operative Day 1",
         "Post laparoscopic appendectomy Day 1. Comfortable. Tolerating sips. Wounds clean. Afebrile 37.8. HR 96. Encouraging mobilisation. IV antibiotics continuing."),
        (dt(P1_ADMIT, days=2, hours=8), "progress-note", "Dr R. Chen (General Surgery)", "Post-operative Day 2",
         "POD2. Eating and drinking well. Mobilising independently. Afebrile 37.1. WBC improving to 12.1, CRP 95. Plan: transition to oral antibiotics, discharge tomorrow if continued improvement."),
    ]
    for ts, ntype, author, subject, content in notes_p1:
        db.add(ClinicalNote(id=gen_id(), patient_id=p1_id, encounter_id=enc1_id,
            timestamp=ts, type=ntype, author=author, subject=subject, content=content))

    # ─────────────────────────────────────────────
    # PATIENT 2 — Margaret Okonkwo — CAP + Cardiac (active, day 3)
    # ─────────────────────────────────────────────
    p2_id = gen_id()
    db.add(Patient(
        id=p2_id, first_name="Margaret", last_name="Okonkwo", dob="1952-11-28",
        gender="female", mrn="MRN-001002",
        allergies=[{"substance": "Sulfonamides", "reaction": "Stevens-Johnson syndrome", "severity": "severe"}],
        past_medical_history=["Hypertension", "Type 2 diabetes mellitus", "Hypothyroidism", "Ex-smoker (20 pack-years, quit 2010)"],
        medication_history=["Metformin 1g BD", "Perindopril 5mg daily", "Thyroxine 100mcg mane", "Aspirin 100mg daily"]
    ))
    enc2_id = gen_id()
    db.add(Encounter(
        id=enc2_id, patient_id=p2_id,
        admission_date=P2_ADMIT,
        discharge_date=None,
        status="active",
        primary_diagnosis="Community-acquired pneumonia (right lower lobe)",
        admission_reason="Productive cough, fever, dyspnoea, pleuritic chest pain"
    ))

    vitals_p2 = [
        (dt(P2_ADMIT), "8867-4", "Heart rate", 102, "bpm"),
        (dt(P2_ADMIT), "8310-5", "Body temperature", 39.1, "Cel"),
        (dt(P2_ADMIT), "59408-5", "SpO2", 91, "%"),
        (dt(P2_ADMIT), "9279-1", "Respiratory rate", 24, "/min"),
        (dt(P2_ADMIT, days=1, hours=6), "8867-4", "Heart rate", 98, "bpm"),
        (dt(P2_ADMIT, days=1, hours=6), "8310-5", "Body temperature", 38.3, "Cel"),
        (dt(P2_ADMIT, days=1, hours=6), "59408-5", "SpO2", 95, "%"),
        (dt(P2_ADMIT, days=2, hours=6), "8867-4", "Heart rate", 88, "bpm"),
        (dt(P2_ADMIT, days=2, hours=6), "8310-5", "Body temperature", 37.6, "Cel"),
        (dt(P2_ADMIT, days=2, hours=6), "59408-5", "SpO2", 97, "%"),
        (dt(P2_ADMIT, days=3, hours=6), "8867-4", "Heart rate", 82, "bpm"),
        (dt(P2_ADMIT, days=3, hours=6), "8310-5", "Body temperature", 37.0, "Cel"),
        (dt(P2_ADMIT, days=3, hours=6), "59408-5", "SpO2", 98, "%"),
    ]
    for ts, code, display, val, unit in vitals_p2:
        db.add(Observation(id=gen_id(), patient_id=p2_id, encounter_id=enc2_id,
            timestamp=ts, type="vital-signs", code=code, display=display, value=val, unit=unit))

    labs_p2 = [
        (dt(P2_ADMIT, hours=1), "6690-2", "WBC", 18.6, "10*3/uL"),
        (dt(P2_ADMIT, hours=1), "1988-5", "CRP", 210, "mg/L"),
        (dt(P2_ADMIT, hours=1), "10839-9", "Troponin I", 0.04, "ug/L"),
        (dt(P2_ADMIT, hours=1), "42637-9", "BNP", 310, "ng/L"),
        (dt(P2_ADMIT, hours=1), "2160-0", "Creatinine", 102, "umol/L"),
        (dt(P2_ADMIT, days=1, hours=6), "6690-2", "WBC", 16.2, "10*3/uL"),
        (dt(P2_ADMIT, days=1, hours=6), "1988-5", "CRP", 188, "mg/L"),
        (dt(P2_ADMIT, days=1, hours=8), "10839-9", "Troponin I", 0.06, "ug/L"),
        (dt(P2_ADMIT, days=2, hours=6), "6690-2", "WBC", 12.4, "10*3/uL"),
        (dt(P2_ADMIT, days=2, hours=6), "1988-5", "CRP", 130, "mg/L"),
        (dt(P2_ADMIT, days=2, hours=8), "10839-9", "Troponin I", 0.04, "ug/L"),
        (dt(P2_ADMIT, days=3, hours=6), "6690-2", "WBC", 9.2, "10*3/uL"),
        (dt(P2_ADMIT, days=3, hours=6), "1988-5", "CRP", 68, "mg/L"),
        (dt(P2_ADMIT, days=3, hours=6), "10839-9", "Troponin I", 0.02, "ug/L"),
    ]
    for ts, code, display, val, unit in labs_p2:
        db.add(Observation(id=gen_id(), patient_id=p2_id, encounter_id=enc2_id,
            timestamp=ts, type="lab", code=code, display=display, value=val, unit=unit))

    db.add(DiagnosticReport(id=gen_id(), patient_id=p2_id, encounter_id=enc2_id,
        timestamp=dt(P2_ADMIT, hours=2), category="imaging", code="XR-CHEST",
        display="Chest X-ray PA",
        findings="Right lower lobe consolidation with air bronchograms. No pleural effusion. Cardiac silhouette upper normal limits.",
        conclusion="RLL consolidation consistent with pneumonia.", status="final"))
    db.add(DiagnosticReport(id=gen_id(), patient_id=p2_id, encounter_id=enc2_id,
        timestamp=dt(P2_ADMIT, days=1, hours=14), category="cardiac", code="ECHO-TTE",
        display="Transthoracic echocardiogram",
        findings="LVEF 55-60%. Mild LV diastolic dysfunction. No RWMA. No pericardial effusion.",
        conclusion="Preserved LVEF. Mild diastolic dysfunction consistent with hypertension. No acute cardiomyopathy.", status="final"))

    meds_p2 = [
        (dt(P2_ADMIT, hours=2), "Ceftriaxone 1g IV", "1g", "IV", "Daily", "active", "Community-acquired pneumonia"),
        (dt(P2_ADMIT, hours=2), "Azithromycin 500mg PO", "500mg", "oral", "Daily", "active", "Atypical organism cover"),
        (dt(P2_ADMIT, hours=1), "Oxygen via nasal prongs 2L/min", "2L/min", "inhalation", "Continuous", "active", "Hypoxaemia"),
        (dt(P2_ADMIT, hours=2), "Paracetamol 1g PO", "1g", "oral", "Q6H", "active", "Fever and analgesia"),
        (dt(P2_ADMIT, hours=2), "Metformin 1g PO", "1g", "oral", "BD", "active", "Diabetes"),
        (dt(P2_ADMIT, hours=2), "Aspirin 100mg PO", "100mg", "oral", "Daily", "active", "Cardiovascular prevention"),
        (dt(P2_ADMIT, hours=2), "Enoxaparin 40mg SC", "40mg", "subcutaneous", "Daily", "active", "VTE prophylaxis"),
    ]
    for ts, name, dose, route, freq, status, indication in meds_p2:
        db.add(Medication(id=gen_id(), patient_id=p2_id, encounter_id=enc2_id,
            timestamp=ts, name=name, dose=dose, route=route, frequency=freq, status=status, indication=indication))

    notes_p2 = [
        (dt(P2_ADMIT), "progress-note", "Dr T. Nguyen (ED)", "ED Assessment",
         "72F with 5-day productive cough, fever 39.1, dyspnoea, right pleuritic chest pain. HTN, T2DM, hypothyroidism, ex-smoker. SpO2 91% RA. CXR: RLL consolidation. WBC 18.6, CRP 210. Troponin 0.04 (demand ischaemia vs ACS — serial troponins ordered). CURB-65 score 3. IV ceftriaxone + azithromycin, O2 therapy started."),
        (dt(P2_ADMIT, days=1, hours=9), "consult", "Dr A. Shah (Cardiology)", "Cardiology Consult",
         "Serial troponins 0.04 → 0.06: Type 2 MI in setting of sepsis, not ACS. Echo: preserved EF 55-60%, mild diastolic dysfunction. No ischaemic changes on ECG. Continue aspirin, serial monitoring. No cath indicated."),
        (dt(P2_ADMIT, days=2, hours=9), "progress-note", "Dr L. Davies (Medicine)", "Ward Round Day 2",
         "Improving. Temp 37.6, SpO2 97% on 1L. CRP 130, WBC 12.4, troponin stable 0.04. Transitioning IV to oral antibiotics. Weaning O2."),
        (dt(P2_ADMIT, days=3, hours=9), "progress-note", "Dr L. Davies (Medicine)", "Ward Round Day 3",
         "Good progress. Afebrile 37.0, SpO2 98% on room air. WBC 9.2, CRP 68, troponin trending down to 0.02. Tolerating oral diet. Mobilising well. Discharge planning — likely tomorrow if stable overnight."),
    ]
    for ts, ntype, author, subject, content in notes_p2:
        db.add(ClinicalNote(id=gen_id(), patient_id=p2_id, encounter_id=enc2_id,
            timestamp=ts, type=ntype, author=author, subject=subject, content=content))

    # ─────────────────────────────────────────────
    # PATIENT 3 — Robert Stanton — NOF Fracture (active, post-op day 2)
    # ─────────────────────────────────────────────
    p3_id = gen_id()
    db.add(Patient(
        id=p3_id, first_name="Robert", last_name="Stanton", dob="1941-07-02",
        gender="male", mrn="MRN-001003",
        allergies=[],
        past_medical_history=["Osteoporosis", "Atrial fibrillation (on warfarin)", "Chronic kidney disease Stage 3", "Benign prostatic hyperplasia"],
        medication_history=["Warfarin 4mg daily (INR target 2.0-3.0)", "Digoxin 125mcg daily", "Tamsulosin 400mcg daily", "Calcium 600mg + Vitamin D3 1000IU daily"]
    ))
    enc3_id = gen_id()
    db.add(Encounter(
        id=enc3_id, patient_id=p3_id,
        admission_date=P3_ADMIT,
        discharge_date=None,
        status="active",
        primary_diagnosis="Right subcapital neck of femur fracture",
        admission_reason="Fall at home — right hip pain, unable to weight bear"
    ))

    vitals_p3 = [
        (dt(P3_ADMIT), "8867-4", "Heart rate", 78, "bpm"),
        (dt(P3_ADMIT), "8310-5", "Body temperature", 36.9, "Cel"),
        (dt(P3_ADMIT), "55284-4", "Blood pressure systolic", 142, "mmHg"),
        (dt(P3_ADMIT), "59408-5", "SpO2", 97, "%"),
        (dt(P3_ADMIT, days=1, hours=6), "8867-4", "Heart rate", 82, "bpm"),
        (dt(P3_ADMIT, days=1, hours=6), "8310-5", "Body temperature", 37.2, "Cel"),
        (dt(P3_ADMIT, days=1, hours=6), "59408-5", "SpO2", 96, "%"),
        (dt(P3_ADMIT, days=2, hours=6), "8867-4", "Heart rate", 76, "bpm"),
        (dt(P3_ADMIT, days=2, hours=6), "8310-5", "Body temperature", 36.8, "Cel"),
        (dt(P3_ADMIT, days=2, hours=6), "59408-5", "SpO2", 97, "%"),
    ]
    for ts, code, display, val, unit in vitals_p3:
        db.add(Observation(id=gen_id(), patient_id=p3_id, encounter_id=enc3_id,
            timestamp=ts, type="vital-signs", code=code, display=display, value=val, unit=unit))

    labs_p3 = [
        (dt(P3_ADMIT, hours=1), "6690-2", "WBC", 8.4, "10*3/uL"),
        (dt(P3_ADMIT, hours=1), "718-7", "Haemoglobin", 108, "g/L"),
        (dt(P3_ADMIT, hours=1), "5902-2", "INR", 2.8, "ratio"),
        (dt(P3_ADMIT, hours=1), "2160-0", "Creatinine", 148, "umol/L"),
        (dt(P3_ADMIT, days=1, hours=6), "5902-2", "INR", 1.8, "ratio"),
        (dt(P3_ADMIT, days=1, hours=6), "718-7", "Haemoglobin", 104, "g/L"),
        (dt(P3_ADMIT, days=2, hours=6), "5902-2", "INR", 1.4, "ratio"),
        (dt(P3_ADMIT, days=2, hours=6), "718-7", "Haemoglobin", 98, "g/L"),
        (dt(P3_ADMIT, days=2, hours=6), "2160-0", "Creatinine", 162, "umol/L"),
    ]
    for ts, code, display, val, unit in labs_p3:
        db.add(Observation(id=gen_id(), patient_id=p3_id, encounter_id=enc3_id,
            timestamp=ts, type="lab", code=code, display=display, value=val, unit=unit))

    db.add(DiagnosticReport(id=gen_id(), patient_id=p3_id, encounter_id=enc3_id,
        timestamp=dt(P3_ADMIT, hours=1), category="imaging", code="XR-HIP-R",
        display="X-ray right hip",
        findings="Subcapital fracture of right neck of femur with varus angulation. Moderate osteopenia.",
        conclusion="Right subcapital NOF fracture. Pre-op warfarin reversal required.", status="final"))

    db.add(Procedure(id=gen_id(), patient_id=p3_id, encounter_id=enc3_id,
        timestamp=dt(P3_ADMIT, days=1, hours=10), code="52734007", display="Right hemiarthroplasty (cemented)",
        status="completed", performer="Mr D. Osei (Orthopaedics)",
        notes="Posterior approach. INR 1.4 at surgery following Vitamin K reversal. EBL 380mL. No intraoperative complications. WBAT with physiotherapy from Day 1 post-op."))

    meds_p3 = [
        (dt(P3_ADMIT, hours=1), "Morphine 2.5mg IV PRN", "2.5mg", "IV", "Q4H PRN", "active", "Acute pain"),
        (dt(P3_ADMIT, hours=1), "Paracetamol 1g IV", "1g", "IV", "Q6H", "active", "Analgesia"),
        (dt(P3_ADMIT, hours=2), "Vitamin K 5mg IV", "5mg", "IV", "Single dose", "completed", "Warfarin reversal"),
        (dt(P3_ADMIT, hours=2), "Enoxaparin 20mg SC", "20mg", "subcutaneous", "Daily", "active", "VTE prophylaxis (renal dose)"),
        (dt(P3_ADMIT, days=2), "Warfarin 4mg PO", "4mg", "oral", "Daily", "active", "AF — resumed post-op Day 2"),
        (dt(P3_ADMIT), "Digoxin 125mcg PO", "125mcg", "oral", "Daily", "active", "AF rate control"),
        (dt(P3_ADMIT), "Tamsulosin 400mcg PO", "400mcg", "oral", "Daily", "active", "BPH"),
    ]
    for ts, name, dose, route, freq, status, indication in meds_p3:
        db.add(Medication(id=gen_id(), patient_id=p3_id, encounter_id=enc3_id,
            timestamp=ts, name=name, dose=dose, route=route, frequency=freq, status=status, indication=indication))

    notes_p3 = [
        (dt(P3_ADMIT), "progress-note", "Dr C. Williams (ED)", "ED Assessment",
         "83M, fall from verandah, right hip pain, unable to weight bear. AF on warfarin, osteoporosis, CKD3. Right leg externally rotated, shortened. INR 2.8. XR confirms subcapital NOF fracture. Vitamin K ordered, orthopaedics and geriatrics notified."),
        (dt(P3_ADMIT, hours=2), "consult", "Mr D. Osei (Orthopaedics)", "Orthopaedic Consult",
         "Right subcapital NOF fracture confirmed. Warfarin reversal underway. Plan cemented hemiarthroplasty once INR <1.5. Consented. Theatre booked for tomorrow morning."),
        (dt(P3_ADMIT, hours=3), "consult", "Dr P. Murray (Geriatrics)", "Geriatric Review",
         "83M fragility fracture. Cognitively intact (MMSE 28/30). Lives alone, independent ADLs. High falls risk. Pre-op optimisation: hydration, analgesia, avoid sedatives, continue digoxin. Post-op: early mobilisation Day 1, OT and physio, delirium prevention."),
        (dt(P3_ADMIT, days=1, hours=14), "progress-note", "Mr D. Osei (Orthopaedics)", "Post-op Day 0",
         "Post cemented hemiarthroplasty. INR 1.4 at surgery. EBL 380mL. Haemodynamically stable. Drains in. WBAT with physio from tomorrow. Resuming warfarin post-op Day 2."),
        (dt(P3_ADMIT, days=2, hours=9), "progress-note", "Dr P. Murray (Geriatrics)", "Post-op Day 1",
         "Alert, oriented, no delirium. Physio: stood with frame, 3 steps. Wound clean. Hb 98 — monitoring, no transfusion threshold. Warfarin 4mg resumed. INR check tomorrow."),
    ]
    for ts, ntype, author, subject, content in notes_p3:
        db.add(ClinicalNote(id=gen_id(), patient_id=p3_id, encounter_id=enc3_id,
            timestamp=ts, type=ntype, author=author, subject=subject, content=content))

    db.commit()
    db.close()
    print("Seed complete — 3 active patients loaded.")

if __name__ == "__main__":
    seed()
