import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import engine, SessionLocal
from app.models.models import (Base, Patient, Encounter, Observation,
                                MedicationRequest, DiagnosticReport,
                                Procedure, ClinicalNote, DischargeSummary)

def ts(base, days=0, hours=0):
    return base + timedelta(days=days, hours=hours)

def seed():
    os.makedirs("data", exist_ok=True)
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    if db.query(Patient).count() > 0:
        print("Already seeded.")
        db.close()
        return

    # ─────────────────────────────────────────
    # PATIENT 1 — Appendicitis + Surgery
    # ─────────────────────────────────────────
    adm1 = datetime(2024, 3, 10, 14, 30)
    p1 = Patient(
        id="pat-001", mrn="MRN-001",
        first_name="James", last_name="Mitchell",
        dob="1989-06-15", gender="male", blood_type="O+",
        allergies=["Penicillin"],
        past_medical_history=["Nil significant"],
        medication_history=["Nil regular"],
        contact={"phone": "0412345678", "emergency": "Sarah Mitchell (wife)"}
    )
    db.add(p1)

    e1 = Encounter(
        id="enc-001", patient_id="pat-001",
        admission_date=adm1, discharge_date=ts(adm1, days=4, hours=10),
        status="discharged", primary_diagnosis="Acute appendicitis",
        admission_type="emergency", ward="Surgical Ward 3B",
        attending_physician="Dr. Priya Sharma"
    )
    db.add(e1)

    # Vitals — trending inflammation then improving post-op
    vitals1 = [
        # Day 0 — admission, fever + tachycardia
        ("HR", "heart_rate", adm1, 102, "bpm", "60-100"),
        ("BP_sys", "blood_pressure_systolic", adm1, 118, "mmHg", "90-140"),
        ("Temp", "temperature", adm1, 38.4, "°C", "36.1-37.2"),
        ("RR", "respiratory_rate", adm1, 18, "breaths/min", "12-20"),
        ("SpO2", "oxygen_saturation", adm1, 98, "%", "95-100"),
        ("HR", "heart_rate", ts(adm1, hours=8), 98, "bpm", "60-100"),
        ("Temp", "temperature", ts(adm1, hours=8), 38.6, "°C", "36.1-37.2"),
        # Day 1 — pre-op
        ("HR", "heart_rate", ts(adm1, days=1), 105, "bpm", "60-100"),
        ("Temp", "temperature", ts(adm1, days=1), 38.8, "°C", "36.1-37.2"),
        ("BP_sys", "blood_pressure_systolic", ts(adm1, days=1), 115, "mmHg", "90-140"),
        ("SpO2", "oxygen_saturation", ts(adm1, days=1), 97, "%", "95-100"),
        # Day 2 — post-op recovery
        ("HR", "heart_rate", ts(adm1, days=2), 88, "bpm", "60-100"),
        ("Temp", "temperature", ts(adm1, days=2), 37.8, "°C", "36.1-37.2"),
        ("BP_sys", "blood_pressure_systolic", ts(adm1, days=2), 122, "mmHg", "90-140"),
        ("SpO2", "oxygen_saturation", ts(adm1, days=2), 99, "%", "95-100"),
        # Day 3 — improving
        ("HR", "heart_rate", ts(adm1, days=3), 78, "bpm", "60-100"),
        ("Temp", "temperature", ts(adm1, days=3), 37.1, "°C", "36.1-37.2"),
        ("BP_sys", "blood_pressure_systolic", ts(adm1, days=3), 124, "mmHg", "90-140"),
        ("SpO2", "oxygen_saturation", ts(adm1, days=3), 99, "%", "95-100"),
        # Day 4 — discharge ready
        ("HR", "heart_rate", ts(adm1, days=4), 72, "bpm", "60-100"),
        ("Temp", "temperature", ts(adm1, days=4), 36.8, "°C", "36.1-37.2"),
    ]
    for code, display, t, val, unit, ref in vitals1:
        db.add(Observation(patient_id="pat-001", encounter_id="enc-001",
            timestamp=t, category="vitals", code=code, display=display,
            value=val, unit=unit, reference_range=ref))

    # Labs — CBC + CRP trending
    labs1 = [
        # Day 0
        ("WBC", "White Blood Cell Count", adm1, 14.2, "x10^9/L", "4.0-11.0"),
        ("CRP", "C-Reactive Protein", adm1, 78.0, "mg/L", "<5"),
        ("Hgb", "Haemoglobin", adm1, 148.0, "g/L", "130-175"),
        ("Plt", "Platelets", adm1, 310.0, "x10^9/L", "150-400"),
        # Day 1
        ("WBC", "White Blood Cell Count", ts(adm1, days=1), 16.8, "x10^9/L", "4.0-11.0"),
        ("CRP", "C-Reactive Protein", ts(adm1, days=1), 142.0, "mg/L", "<5"),
        ("Hgb", "Haemoglobin", ts(adm1, days=1), 142.0, "g/L", "130-175"),
        # Day 2 post-op
        ("WBC", "White Blood Cell Count", ts(adm1, days=2), 13.1, "x10^9/L", "4.0-11.0"),
        ("CRP", "C-Reactive Protein", ts(adm1, days=2), 98.0, "mg/L", "<5"),
        ("Hgb", "Haemoglobin", ts(adm1, days=2), 138.0, "g/L", "130-175"),
        # Day 3
        ("WBC", "White Blood Cell Count", ts(adm1, days=3), 9.4, "x10^9/L", "4.0-11.0"),
        ("CRP", "C-Reactive Protein", ts(adm1, days=3), 44.0, "mg/L", "<5"),
        ("Hgb", "Haemoglobin", ts(adm1, days=3), 135.0, "g/L", "130-175"),
        # Day 4
        ("WBC", "White Blood Cell Count", ts(adm1, days=4), 7.8, "x10^9/L", "4.0-11.0"),
        ("CRP", "C-Reactive Protein", ts(adm1, days=4), 18.0, "mg/L", "<5"),
    ]
    for code, display, t, val, unit, ref in labs1:
        db.add(Observation(patient_id="pat-001", encounter_id="enc-001",
            timestamp=t, category="labs", code=code, display=display,
            value=val, unit=unit, reference_range=ref))

    # Medications
    meds1 = [
        ("Metronidazole 500mg IV", "500mg", "IV", "TDS", "Appendicitis prophylaxis",
         "active", adm1,
         [{"time": str(ts(adm1, hours=2)), "note": "Given pre-op"},
          {"time": str(ts(adm1, days=1, hours=2)), "note": "Continued"},
          {"time": str(ts(adm1, days=2, hours=2)), "note": "Switched oral"}]),
        ("Cefazolin 2g IV", "2g", "IV", "BD", "Surgical prophylaxis",
         "completed", adm1,
         [{"time": str(ts(adm1, hours=1)), "note": "Pre-op dose"},
          {"time": str(ts(adm1, hours=9)), "note": "Post-op dose 1"}]),
        ("Morphine 5mg IV PRN", "5mg", "IV", "PRN Q4H", "Post-op analgesia",
         "active", ts(adm1, days=1, hours=6),
         [{"time": str(ts(adm1, days=1, hours=8)), "note": "Given for pain 7/10"},
          {"time": str(ts(adm1, days=2)), "note": "Pain 5/10"}]),
        ("Paracetamol 1g PO", "1g", "oral", "QID", "Analgesia",
         "active", adm1,
         [{"time": str(ts(adm1, hours=3)), "note": "Given"},
          {"time": str(ts(adm1, hours=9)), "note": "Given"},
          {"time": str(ts(adm1, days=1)), "note": "Given"},
          {"time": str(ts(adm1, days=2)), "note": "Given"}]),
    ]
    for name, dose, route, freq, ind, status, t, admins in meds1:
        db.add(MedicationRequest(patient_id="pat-001", encounter_id="enc-001",
            timestamp=t, medication_name=name, dose=dose, route=route,
            frequency=freq, indication=ind, status=status, administrations=admins))

    # Reports
    db.add(DiagnosticReport(
        patient_id="pat-001", encounter_id="enc-001",
        timestamp=ts(adm1, hours=3), category="imaging", code="CT-ABD",
        display="CT Abdomen and Pelvis",
        status="final",
        conclusion="Acute appendicitis with periappendiceal fat stranding. No perforation.",
        full_report="""CT ABDOMEN AND PELVIS WITH CONTRAST

Clinical indication: RIF pain, query appendicitis.

Technique: Portal venous phase contrast-enhanced CT.

Findings:
- Appendix measures 9mm in diameter with wall thickening and surrounding fat stranding in the right iliac fossa.
- No free air or free fluid to suggest perforation.
- No appendicolith identified.
- Remainder of bowel appears normal. No obstruction.
- Liver, spleen, kidneys and adrenals are unremarkable.
- No lymphadenopathy.

Impression: Findings consistent with acute non-perforated appendicitis.
Recommend urgent surgical review.

Reported by: Dr. Kevin Tran, Radiologist."""
    ))

    db.add(DiagnosticReport(
        patient_id="pat-001", encounter_id="enc-001",
        timestamp=ts(adm1, days=3, hours=4), category="pathology", code="HISTO-001",
        display="Appendix Histopathology",
        status="final",
        conclusion="Acute suppurative appendicitis. No evidence of malignancy.",
        full_report="""HISTOPATHOLOGY REPORT

Specimen: Appendix (laparoscopic appendicectomy)

Macroscopy: Appendix measuring 65mm in length and 12mm in diameter. Serosal surface shows congestion and fibrinous exudate. Lumen contains purulent material.

Microscopy: Transmural neutrophilic infiltrate consistent with acute suppurative appendicitis. No perforation. No granulomata. No evidence of malignancy or carcinoid tumour.

Diagnosis: Acute suppurative appendicitis.

Reported by: Dr. Angela Park, Anatomical Pathologist."""
    ))

    # Procedures
    db.add(Procedure(
        patient_id="pat-001", encounter_id="enc-001",
        timestamp=ts(adm1, days=1, hours=6), code="PROC-LAP-APPY",
        display="Laparoscopic Appendicectomy",
        performer="Dr. Priya Sharma (Surgeon), Dr. Tom Walsh (Anaesthetist)",
        status="completed",
        notes="""OPERATIVE NOTE

Procedure: Laparoscopic appendicectomy
Date: Day 1 of admission, 20:30

Anaesthesia: General anaesthesia

Operative findings:
- Acutely inflamed appendix with serosal congestion
- Periappendiceal fibrinous exudate
- No perforation, no free pus

Technique:
- Standard three-port laparoscopic approach
- Mesoappendix divided with LigaSure
- Appendix ligated at base with Endoloop x2
- Appendix removed in retrieval bag
- Thorough washout performed
- Ports closed in layers

Estimated blood loss: <20mL
Complications: None
Duration: 45 minutes

Post-op instructions: IV antibiotics 24hrs, early mobilisation, liquid diet day 1 post-op."""
    ))

    # Clinical Notes
    notes1 = [
        (adm1, "admission", "Dr. Priya Sharma", "Surgeon",
         """ADMISSION NOTE

Patient: James Mitchell, 34M
Presenting complaint: 18-hour history of right iliac fossa pain, nausea, anorexia.

History of presenting illness:
Onset periumbilical, migrated to RIF. Associated nausea x3 vomits. Low-grade fever at home (38.1). No diarrhoea. Last bowel motion yesterday. No urinary symptoms.

Examination:
- Temp 38.4, HR 102, BP 118/76, RR 18, SpO2 98%
- Abdomen: RIF guarding and tenderness. Positive Rovsing sign. Positive psoas sign.
- Rebound tenderness present in RIF.

Impression: Clinical appendicitis. Alvarado score 8.

Plan:
1. Nil by mouth
2. IV fluids
3. Bloods: FBC, CRP, UEC, LFTs, lipase, blood cultures
4. Urine MCS
5. CT abdomen/pelvis
6. Surgical consent for appendicectomy
7. Analgesia: paracetamol + morphine PRN"""),
        (ts(adm1, days=1), "progress", "Dr. Priya Sharma", "Surgeon",
         """SURGICAL PROGRESS NOTE — Day 1

Patient remains febrile (38.8) and symptomatic. WBC 16.8, CRP 142.
CT confirmed acute appendicitis without perforation.

Plan:
- Listed for laparoscopic appendicectomy tonight at 20:30
- IV Cefazolin 2g pre-op + Metronidazole continued
- Consented and marked
- Anaesthesia reviewed, cleared for GA"""),
        (ts(adm1, days=2), "progress", "Dr. Priya Sharma", "Surgeon",
         """POST-OPERATIVE NOTE — Day 2

Uncomplicated laparoscopic appendicectomy performed last evening (Day 1, 20:30).
Operative findings: acute suppurative appendicitis, no perforation.

Overnight: tolerating sips, no fever. SpO2 99% on air.

Examination: Abdomen soft. Mild port-site tenderness. Bowel sounds present.

Results: WBC 13.1 (down), CRP 98 (down from 142).

Plan:
- Upgrade to light diet
- Continue IV Metronidazole → switch to oral Metronidazole 400mg TDS today
- Continue paracetamol + ibuprofen regular
- Physiotherapy for early mobilisation
- Remove IDC"""),
        (ts(adm1, days=3), "progress", "Dr. Priya Sharma", "Surgeon",
         """PROGRESS NOTE — Day 3

Clinically improving. Afebrile (37.1). Tolerating full diet and oral medications.
WBC 9.4, CRP 44 — trending down. Histopath pending.

Mobilising independently. Wound sites clean and dry.

Plan:
- Continue oral antibiotics
- Target discharge tomorrow if remains well
- Histopath result expected today"""),
        (ts(adm1, days=4), "progress", "Dr. Priya Sharma", "Surgeon",
         """DISCHARGE PROGRESS NOTE — Day 4

Patient well, afebrile, tolerating diet. WBC 7.8, CRP 18.
Histopathology: acute suppurative appendicitis, no malignancy.

Fit for discharge today.

Discharge plan:
- Metronidazole 400mg TDS x 5 more days (oral)
- Paracetamol 1g QID PRN
- Wound review in 7 days with GP
- Return precautions: fever, worsening pain, wound discharge"""),
    ]
    for t, ntype, author, role, content in notes1:
        db.add(ClinicalNote(patient_id="pat-001", encounter_id="enc-001",
            timestamp=t, note_type=ntype, author=author, author_role=role, content=content))

    db.add(DischargeSummary(
        patient_id="pat-001", encounter_id="enc-001",
        timestamp=ts(adm1, days=4, hours=9),
        summary_text="""DISCHARGE SUMMARY

Patient: James Mitchell | DOB: 15/06/1989 | MRN: MRN-001
Admission: 10/03/2024 | Discharge: 14/03/2024
Ward: Surgical 3B | Consultant: Dr. Priya Sharma

Presenting Complaint: Right iliac fossa pain, fever, nausea.

Diagnosis: Acute suppurative appendicitis (non-perforated).

Treatment:
- Laparoscopic appendicectomy (11/03/2024)
- IV Cefazolin (pre/post-op) + IV Metronidazole → oral step-down
- IV/oral analgesia

Investigations:
- CT abdomen: acute appendicitis, no perforation
- Histopathology: acute suppurative appendicitis, no malignancy
- WBC peak 16.8, normalised to 7.8 at discharge
- CRP peak 142, normalised to 18 at discharge

Discharge medications:
1. Metronidazole 400mg oral TDS x 5 days
2. Paracetamol 1g QID PRN

Follow-up:
- GP wound review in 7 days
- Return to ED if: fever >38.5, wound breakdown, worsening pain""",
        structured_data={
            "diagnosis": "Acute suppurative appendicitis",
            "procedure": "Laparoscopic appendicectomy",
            "los_days": 4,
            "peak_wbc": 16.8,
            "peak_crp": 142,
            "discharge_medications": ["Metronidazole 400mg TDS x5d", "Paracetamol 1g QID PRN"],
            "complications": None
        },
        generated_by="manual"
    ))

    # ─────────────────────────────────────────
    # PATIENT 2 — Pneumonia + Cardiac Workup
    # ─────────────────────────────────────────
    adm2 = datetime(2024, 3, 12, 9, 15)
    p2 = Patient(
        id="pat-002", mrn="MRN-002",
        first_name="Margaret", last_name="Chen",
        dob="1952-11-02", gender="female", blood_type="A+",
        allergies=["Sulfonamides"],
        past_medical_history=["Hypertension", "Type 2 Diabetes", "Hyperlipidaemia"],
        medication_history=["Metformin 1g BD", "Amlodipine 5mg daily", "Atorvastatin 40mg nocte"],
        contact={"phone": "0498765432", "emergency": "David Chen (son)"}
    )
    db.add(p2)

    e2 = Encounter(
        id="enc-002", patient_id="pat-002",
        admission_date=adm2, discharge_date=ts(adm2, days=5, hours=11),
        status="discharged", primary_diagnosis="Community-acquired pneumonia with cardiac monitoring",
        admission_type="emergency", ward="Respiratory Ward 5A",
        attending_physician="Dr. Leila Nouri"
    )
    db.add(e2)

    vitals2 = [
        ("HR", "heart_rate", adm2, 108, "bpm", "60-100"),
        ("BP_sys", "blood_pressure_systolic", adm2, 138, "mmHg", "90-140"),
        ("Temp", "temperature", adm2, 39.1, "°C", "36.1-37.2"),
        ("RR", "respiratory_rate", adm2, 24, "breaths/min", "12-20"),
        ("SpO2", "oxygen_saturation", adm2, 91, "%", "95-100"),
        ("FiO2", "oxygen_flow", adm2, 4, "L/min", ""),
        ("HR", "heart_rate", ts(adm2, hours=6), 112, "bpm", "60-100"),
        ("SpO2", "oxygen_saturation", ts(adm2, hours=6), 93, "%", "95-100"),
        ("Temp", "temperature", ts(adm2, hours=6), 39.3, "°C", "36.1-37.2"),

        ("HR", "heart_rate", ts(adm2, days=1), 104, "bpm", "60-100"),
        ("Temp", "temperature", ts(adm2, days=1), 38.7, "°C", "36.1-37.2"),
        ("RR", "respiratory_rate", ts(adm2, days=1), 22, "breaths/min", "12-20"),
        ("SpO2", "oxygen_saturation", ts(adm2, days=1), 94, "%", "95-100"),

        ("HR", "heart_rate", ts(adm2, days=2), 96, "bpm", "60-100"),
        ("Temp", "temperature", ts(adm2, days=2), 38.0, "°C", "36.1-37.2"),
        ("RR", "respiratory_rate", ts(adm2, days=2), 20, "breaths/min", "12-20"),
        ("SpO2", "oxygen_saturation", ts(adm2, days=2), 95, "%", "95-100"),

        ("HR", "heart_rate", ts(adm2, days=3), 88, "bpm", "60-100"),
        ("Temp", "temperature", ts(adm2, days=3), 37.4, "°C", "36.1-37.2"),
        ("SpO2", "oxygen_saturation", ts(adm2, days=3), 97, "%", "95-100"),

        ("HR", "heart_rate", ts(adm2, days=4), 80, "bpm", "60-100"),
        ("Temp", "temperature", ts(adm2, days=4), 36.9, "°C", "36.1-37.2"),
        ("SpO2", "oxygen_saturation", ts(adm2, days=4), 98, "%", "95-100"),

        ("HR", "heart_rate", ts(adm2, days=5), 76, "bpm", "60-100"),
        ("SpO2", "oxygen_saturation", ts(adm2, days=5), 98, "%", "95-100"),
        ("Temp", "temperature", ts(adm2, days=5), 36.7, "°C", "36.1-37.2"),
    ]
    for code, display, t, val, unit, ref in vitals2:
        db.add(Observation(patient_id="pat-002", encounter_id="enc-002",
            timestamp=t, category="vitals", code=code, display=display,
            value=val, unit=unit, reference_range=ref))

    labs2 = [
        ("WBC", "White Blood Cell Count", adm2, 18.2, "x10^9/L", "4.0-11.0"),
        ("CRP", "C-Reactive Protein", adm2, 188.0, "mg/L", "<5"),
        ("Trop", "Troponin I", adm2, 0.06, "ug/L", "<0.04"),
        ("BNP", "B-Natriuretic Peptide", adm2, 420.0, "pg/mL", "<100"),
        ("HbA1c", "HbA1c", adm2, 7.8, "%", "<7.0"),
        ("Cr", "Creatinine", adm2, 98.0, "umol/L", "45-90"),

        ("WBC", "White Blood Cell Count", ts(adm2, days=1), 16.4, "x10^9/L", "4.0-11.0"),
        ("CRP", "C-Reactive Protein", ts(adm2, days=1), 162.0, "mg/L", "<5"),
        ("Trop", "Troponin I", ts(adm2, days=1), 0.09, "ug/L", "<0.04"),
        ("BNP", "B-Natriuretic Peptide", ts(adm2, days=1), 510.0, "pg/mL", "<100"),

        ("WBC", "White Blood Cell Count", ts(adm2, days=2), 12.8, "x10^9/L", "4.0-11.0"),
        ("CRP", "C-Reactive Protein", ts(adm2, days=2), 118.0, "mg/L", "<5"),
        ("Trop", "Troponin I", ts(adm2, days=2), 0.07, "ug/L", "<0.04"),
        ("BNP", "B-Natriuretic Peptide", ts(adm2, days=2), 390.0, "pg/mL", "<100"),

        ("WBC", "White Blood Cell Count", ts(adm2, days=3), 9.6, "x10^9/L", "4.0-11.0"),
        ("CRP", "C-Reactive Protein", ts(adm2, days=3), 64.0, "mg/L", "<5"),
        ("Trop", "Troponin I", ts(adm2, days=3), 0.04, "ug/L", "<0.04"),
        ("BNP", "B-Natriuretic Peptide", ts(adm2, days=3), 290.0, "pg/mL", "<100"),

        ("WBC", "White Blood Cell Count", ts(adm2, days=4), 7.9, "x10^9/L", "4.0-11.0"),
        ("CRP", "C-Reactive Protein", ts(adm2, days=4), 28.0, "mg/L", "<5"),
        ("Trop", "Troponin I", ts(adm2, days=4), 0.02, "ug/L", "<0.04"),
        ("BNP", "B-Natriuretic Peptide", ts(adm2, days=4), 180.0, "pg/mL", "<100"),
    ]
    for code, display, t, val, unit, ref in labs2:
        db.add(Observation(patient_id="pat-002", encounter_id="enc-002",
            timestamp=t, category="labs", code=code, display=display,
            value=val, unit=unit, reference_range=ref))

    meds2 = [
        ("Amoxicillin-clavulanate 1.2g IV", "1.2g", "IV", "TDS", "Community-acquired pneumonia",
         "active", adm2,
         [{"time": str(ts(adm2, hours=1)), "note": "First dose"},
          {"time": str(ts(adm2, days=1)), "note": "Continued"},
          {"time": str(ts(adm2, days=2)), "note": "Step-down to oral"}]),
        ("Azithromycin 500mg PO", "500mg", "oral", "Daily", "Atypical coverage",
         "active", adm2,
         [{"time": str(ts(adm2, hours=2)), "note": "Given"},
          {"time": str(ts(adm2, days=1)), "note": "Continued"},
          {"time": str(ts(adm2, days=2)), "note": "Continued"},
          {"time": str(ts(adm2, days=3)), "note": "Course complete"}]),
        ("Metformin 1g PO", "1g", "oral", "BD", "Type 2 Diabetes",
         "active", adm2,
         [{"time": str(ts(adm2, days=1)), "note": "Held Day 0 due to contrast CT — restarted"},
          {"time": str(ts(adm2, days=2)), "note": "Continued"}]),
        ("Enoxaparin 40mg SC", "40mg", "subcutaneous", "Daily", "DVT prophylaxis",
         "active", adm2,
         [{"time": str(ts(adm2, hours=6)), "note": "Given"},
          {"time": str(ts(adm2, days=1)), "note": "Given"},
          {"time": str(ts(adm2, days=2)), "note": "Given"}]),
    ]
    for name, dose, route, freq, ind, status, t, admins in meds2:
        db.add(MedicationRequest(patient_id="pat-002", encounter_id="enc-002",
            timestamp=t, medication_name=name, dose=dose, route=route,
            frequency=freq, indication=ind, status=status, administrations=admins))

    db.add(DiagnosticReport(
        patient_id="pat-002", encounter_id="enc-002",
        timestamp=ts(adm2, hours=1), category="imaging", code="CXR-001",
        display="Chest X-Ray PA",
        status="final",
        conclusion="Right lower lobe consolidation consistent with pneumonia.",
        full_report="""CHEST X-RAY — PA VIEW

Clinical indication: Fever, cough, SOB, SpO2 91%.

Findings:
- Right lower lobe airspace opacity with air bronchograms consistent with consolidation.
- No pleural effusion identified.
- Cardiac silhouette upper limits of normal (CTR 0.52).
- No pneumothorax.
- Trachea midline.

Impression: Right lower lobe pneumonia. Mildly enlarged cardiac silhouette — clinical correlation recommended.

Reported by: Dr. Kevin Tran, Radiologist."""
    ))

    db.add(DiagnosticReport(
        patient_id="pat-002", encounter_id="enc-002",
        timestamp=ts(adm2, days=1, hours=4), category="cardiology", code="ECG-001",
        display="12-Lead ECG",
        status="final",
        conclusion="Sinus tachycardia. No acute ischaemic changes. QTc 432ms.",
        full_report="""ECG REPORT

Rate: 108 bpm
Rhythm: Sinus tachycardia
Axis: Normal
PR interval: 158ms
QRS: 88ms
QTc: 432ms

ST segments: No ST elevation or depression.
T waves: No significant inversion.
No evidence of acute myocardial infarction.
No LVH criteria met.
No bundle branch block.

Impression: Sinus tachycardia, likely reactive. No acute ischaemic changes.

Reported by: Dr. Amy Lee, Cardiologist."""
    ))

    db.add(DiagnosticReport(
        patient_id="pat-002", encounter_id="enc-002",
        timestamp=ts(adm2, days=2, hours=10), category="cardiology", code="ECHO-001",
        display="Transthoracic Echocardiogram",
        status="final",
        conclusion="Mildly reduced LV systolic function (EF 48%). No wall motion abnormalities. Mild diastolic dysfunction.",
        full_report="""TRANSTHORACIC ECHOCARDIOGRAM

Indication: Elevated troponin, raised BNP, mildly enlarged cardiac silhouette on CXR.

LV systolic function: Mildly reduced. EF estimated 48% (Simpson biplane).
LV diastolic function: Grade I diastolic dysfunction (impaired relaxation).
LV wall motion: No regional wall motion abnormalities.
LV dimensions: Mild LV dilatation (LVIDD 56mm).
RV: Normal size and function.
Valves: Mild mitral regurgitation. Aortic valve calcification without significant stenosis.
Pericardium: No effusion.

Impression: Mildly reduced LV systolic function (EF 48%). Likely demand ischaemia in context of sepsis/pneumonia. 
Recommend repeat echo in 6 weeks to confirm recovery.

Reported by: Dr. Amy Lee, Cardiologist."""
    ))

    notes2 = [
        (adm2, "admission", "Dr. Leila Nouri", "Respiratory Physician",
         """ADMISSION NOTE

Patient: Margaret Chen, 71F
Presenting complaint: 4-day history of productive cough, fever, increasing SOB.

History: Productive cough (green sputum), fever 39°C at home, progressive dyspnoea. No chest pain. No haemoptysis.
Background: HTN, T2DM, hyperlipidaemia. Metformin, amlodipine, atorvastatin.

Examination:
- Temp 39.1, HR 108, BP 138/88, RR 24, SpO2 91% on air → improved to 93% on 4L O2
- Chest: Reduced air entry and dullness right base. Bronchial breath sounds RLL.
- CVS: Mild peripheral oedema. Dual heart sounds, no murmur audible clearly due to tachycardia.
- Abdomen: Soft, non-tender.

Impression: Community-acquired pneumonia RLL. Background cardiac monitoring required given elevated troponin and BNP.

Plan:
1. Amoxicillin-clavulanate IV + Azithromycin oral
2. Oxygen therapy — target SpO2 94-98%
3. Cardiac monitoring — ECG, troponin serial, BNP
4. Cardiology review requested
5. Chest X-ray done
6. IV fluids for rehydration
7. Hold Metformin until contrast risk cleared
8. DVT prophylaxis — Enoxaparin"""),
        (ts(adm2, days=1), "progress", "Dr. Leila Nouri", "Respiratory Physician",
         """PROGRESS NOTE — Day 1

Febrile (38.7), HR 104, SpO2 94% on 4L. Cough productive.
Trop rising slightly (0.09). Cardiology review today.
BNP 510 — mildly elevated, likely stress cardiomyopathy vs demand ischaemia.

Plan: Continue antibiotics. Await cardiology review and echocardiogram."""),
        (ts(adm2, days=1, hours=8), "consult", "Dr. Amy Lee", "Cardiologist",
         """CARDIOLOGY CONSULT NOTE

Referred by Dr. Nouri for elevated troponin and BNP in context of pneumonia.

History: 71F, background HTN/T2DM. No prior cardiac history. No exertional chest pain. No prior workup.

Examination: HR 104. Mild peripheral oedema bilaterally. JVP mildly elevated.

Assessment:
Troponin and BNP elevation in context of severe infection. Differential: demand ischaemia (type 2 MI) vs new cardiomyopathy. ECG without acute ischaemic changes.

Plan:
1. Serial troponins (6-hourly x3)
2. Transthoracic echocardiogram tomorrow
3. Continue telemetry monitoring
4. If troponin peaks and falls — demand ischaemia, treat infection
5. If worsening or wall motion abnormality on echo — discuss with interventional cardiology"""),
        (ts(adm2, days=2), "progress", "Dr. Leila Nouri", "Respiratory Physician",
         """PROGRESS NOTE — Day 2

Temperature 38.0 — improving. SpO2 95% on 3L O2 (weaning). HR 96.
CRP 118 (improving), WBC 12.8.
Echocardiogram today: EF 48%, mild diastolic dysfunction — no wall motion abnormality.
Troponin trend: 0.06 → 0.09 → 0.07 — peaking and falling, consistent with demand ischaemia.

Cardiology: No intervention required. Repeat echo in 6 weeks.

Plan: Step-down to oral antibiotics. Continue monitoring. Restart Metformin."""),
        (ts(adm2, days=4), "progress", "Dr. Leila Nouri", "Respiratory Physician",
         """PROGRESS NOTE — Day 4

Afebrile (36.9). HR 80. SpO2 98% on room air.
CRP 28, WBC 7.9. Troponin 0.02 (normalised).
Tolerating oral medications and diet. Mobilising well.

Plan: Discharge tomorrow. Outpatient follow-up. Repeat CXR in 6 weeks."""),
    ]
    for t, ntype, author, role, content in notes2:
        db.add(ClinicalNote(patient_id="pat-002", encounter_id="enc-002",
            timestamp=t, note_type=ntype, author=author, author_role=role, content=content))

    db.add(DischargeSummary(
        patient_id="pat-002", encounter_id="enc-002",
        timestamp=ts(adm2, days=5, hours=10),
        summary_text="""DISCHARGE SUMMARY

Patient: Margaret Chen | DOB: 02/11/1952 | MRN: MRN-002
Admission: 12/03/2024 | Discharge: 17/03/2024
Ward: Respiratory 5A | Consultant: Dr. Leila Nouri

Presenting Complaint: Productive cough, fever, dyspnoea.

Diagnoses:
1. Community-acquired pneumonia — right lower lobe
2. Demand ischaemia (Type 2 MI) in context of sepsis — resolved
3. Mildly reduced LV systolic function (EF 48%)

Treatment:
- IV Amoxicillin-clavulanate → oral step-down + Azithromycin 5-day course
- Oxygen therapy (weaned from 4L to room air by Day 4)
- Cardiology review: serial troponins, echocardiogram — no intervention required

Discharge medications:
1. Amoxicillin-clavulanate 875/125mg BD PO x 5 more days
2. Metformin 1g BD (resumed)
3. Amlodipine 5mg daily (continued)
4. Atorvastatin 40mg nocte (continued)

Follow-up:
- GP in 1 week
- Repeat CXR in 6 weeks
- Repeat echocardiogram in 6 weeks (Dr. Amy Lee)
- HbA1c review with GP (current 7.8%)""",
        structured_data={
            "diagnoses": ["CAP — RLL", "Type 2 MI — resolved", "Mildly reduced LV function EF 48%"],
            "los_days": 5,
            "peak_wbc": 18.2,
            "peak_crp": 188,
            "peak_troponin": 0.09,
            "discharge_medications": ["Amoxicillin-clavulanate 875/125mg BD x5d", "Metformin 1g BD", "Amlodipine 5mg daily", "Atorvastatin 40mg nocte"],
            "complications": "Demand ischaemia — resolved"
        },
        generated_by="manual"
    ))

    # ─────────────────────────────────────────
    # PATIENT 3 — Orthopaedic Fracture
    # ─────────────────────────────────────────
    adm3 = datetime(2024, 3, 15, 16, 45)
    p3 = Patient(
        id="pat-003", mrn="MRN-003",
        first_name="Robert", last_name="Nguyen",
        dob="1945-03-22", gender="male", blood_type="B+",
        allergies=["Codeine (nausea)"],
        past_medical_history=["Osteoporosis", "Hypertension", "Mild CKD (eGFR 54)"],
        medication_history=["Alendronate 70mg weekly", "Ramipril 5mg daily", "Aspirin 100mg daily"],
        contact={"phone": "0487654321", "emergency": "Lisa Nguyen (daughter)"}
    )
    db.add(p3)

    e3 = Encounter(
        id="enc-003", patient_id="pat-003",
        admission_date=adm3, discharge_date=ts(adm3, days=5, hours=8),
        status="discharged", primary_diagnosis="Left neck of femur fracture — ORIF performed",
        admission_type="emergency", ward="Orthopaedic Ward 4C",
        attending_physician="Dr. Simon Park"
    )
    db.add(e3)

    vitals3 = [
        ("HR", "heart_rate", adm3, 94, "bpm", "60-100"),
        ("BP_sys", "blood_pressure_systolic", adm3, 148, "mmHg", "90-140"),
        ("Temp", "temperature", adm3, 36.9, "°C", "36.1-37.2"),
        ("SpO2", "oxygen_saturation", adm3, 96, "%", "95-100"),
        ("Pain", "pain_score", adm3, 8, "/10", ""),

        ("HR", "heart_rate", ts(adm3, days=1), 86, "bpm", "60-100"),
        ("BP_sys", "blood_pressure_systolic", ts(adm3, days=1), 142, "mmHg", "90-140"),
        ("SpO2", "oxygen_saturation", ts(adm3, days=1), 97, "%", "95-100"),
        ("Pain", "pain_score", ts(adm3, days=1), 6, "/10", ""),

        ("HR", "heart_rate", ts(adm3, days=2), 80, "bpm", "60-100"),
        ("BP_sys", "blood_pressure_systolic", ts(adm3, days=2), 136, "mmHg", "90-140"),
        ("SpO2", "oxygen_saturation", ts(adm3, days=2), 97, "%", "95-100"),
        ("Pain", "pain_score", ts(adm3, days=2), 4, "/10", ""),

        ("HR", "heart_rate", ts(adm3, days=3), 76, "bpm", "60-100"),
        ("BP_sys", "blood_pressure_systolic", ts(adm3, days=3), 134, "mmHg", "90-140"),
        ("SpO2", "oxygen_saturation", ts(adm3, days=3), 98, "%", "95-100"),
        ("Pain", "pain_score", ts(adm3, days=3), 3, "/10", ""),

        ("HR", "heart_rate", ts(adm3, days=4), 74, "bpm", "60-100"),
        ("BP_sys", "blood_pressure_systolic", ts(adm3, days=4), 132, "mmHg", "90-140"),
        ("Pain", "pain_score", ts(adm3, days=4), 2, "/10", ""),

        ("HR", "heart_rate", ts(adm3, days=5), 72, "bpm", "60-100"),
        ("Pain", "pain_score", ts(adm3, days=5), 2, "/10", ""),
    ]
    for code, display, t, val, unit, ref in vitals3:
        db.add(Observation(patient_id="pat-003", encounter_id="enc-003",
            timestamp=t, category="vitals", code=code, display=display,
            value=val, unit=unit, reference_range=ref))

    labs3 = [
        ("Hgb", "Haemoglobin", adm3, 136.0, "g/L", "130-175"),
        ("WBC", "White Blood Cell Count", adm3, 8.4, "x10^9/L", "4.0-11.0"),
        ("Plt", "Platelets", adm3, 224.0, "x10^9/L", "150-400"),
        ("eGFR", "eGFR", adm3, 52.0, "mL/min/1.73m2", ">60"),
        ("Cr", "Creatinine", adm3, 124.0, "umol/L", "60-110"),
        ("INR", "INR", adm3, 1.1, "", "0.9-1.2"),

        ("Hgb", "Haemoglobin", ts(adm3, days=1), 118.0, "g/L", "130-175"),
        ("WBC", "White Blood Cell Count", ts(adm3, days=1), 10.2, "x10^9/L", "4.0-11.0"),
        ("CRP", "C-Reactive Protein", ts(adm3, days=1), 62.0, "mg/L", "<5"),
        ("Cr", "Creatinine", ts(adm3, days=1), 128.0, "umol/L", "60-110"),

        ("Hgb", "Haemoglobin", ts(adm3, days=2), 114.0, "g/L", "130-175"),
        ("WBC", "White Blood Cell Count", ts(adm3, days=2), 9.8, "x10^9/L", "4.0-11.0"),
        ("CRP", "C-Reactive Protein", ts(adm3, days=2), 88.0, "mg/L", "<5"),

        ("Hgb", "Haemoglobin", ts(adm3, days=3), 116.0, "g/L", "130-175"),
        ("WBC", "White Blood Cell Count", ts(adm3, days=3), 8.6, "x10^9/L", "4.0-11.0"),
        ("CRP", "C-Reactive Protein", ts(adm3, days=3), 44.0, "mg/L", "<5"),

        ("Hgb", "Haemoglobin", ts(adm3, days=4), 118.0, "g/L", "130-175"),
        ("CRP", "C-Reactive Protein", ts(adm3, days=4), 22.0, "mg/L", "<5"),
        ("Cr", "Creatinine", ts(adm3, days=4), 118.0, "umol/L", "60-110"),
    ]
    for code, display, t, val, unit, ref in labs3:
        db.add(Observation(patient_id="pat-003", encounter_id="enc-003",
            timestamp=t, category="labs", code=code, display=display,
            value=val, unit=unit, reference_range=ref))

    meds3 = [
        ("Paracetamol 1g IV", "1g", "IV", "QID", "Post-operative analgesia",
         "active", adm3,
         [{"time": str(ts(adm3, hours=1)), "note": "Given"},
          {"time": str(ts(adm3, hours=7)), "note": "Given"},
          {"time": str(ts(adm3, days=1)), "note": "Switched to oral"}]),
        ("Tramadol 50mg PO PRN", "50mg", "oral", "PRN Q6H", "Moderate pain",
         "active", ts(adm3, days=1),
         [{"time": str(ts(adm3, days=1, hours=4)), "note": "Pain 6/10"},
          {"time": str(ts(adm3, days=2)), "note": "Pain 4/10"}]),
        ("Enoxaparin 40mg SC", "40mg", "subcutaneous", "Daily", "DVT prophylaxis post-ORIF",
         "active", ts(adm3, hours=12),
         [{"time": str(ts(adm3, hours=12)), "note": "First dose post-op"},
          {"time": str(ts(adm3, days=1)), "note": "Given"},
          {"time": str(ts(adm3, days=2)), "note": "Given"},
          {"time": str(ts(adm3, days=3)), "note": "Given"}]),
        ("Ondansetron 4mg IV PRN", "4mg", "IV", "PRN Q8H", "Nausea prophylaxis (codeine allergy)",
         "active", adm3,
         [{"time": str(ts(adm3, days=1, hours=2)), "note": "Given post-op nausea"}]),
        ("Ramipril 5mg PO", "5mg", "oral", "Daily", "Hypertension — continued",
         "active", ts(adm3, days=1),
         [{"time": str(ts(adm3, days=1)), "note": "Resumed post-op"},
          {"time": str(ts(adm3, days=2)), "note": "Continued"}]),
    ]
    for name, dose, route, freq, ind, status, t, admins in meds3:
        db.add(MedicationRequest(patient_id="pat-003", encounter_id="enc-003",
            timestamp=t, medication_name=name, dose=dose, route=route,
            frequency=freq, indication=ind, status=status, administrations=admins))

    db.add(DiagnosticReport(
        patient_id="pat-003", encounter_id="enc-003",
        timestamp=ts(adm3, hours=1), category="imaging", code="XRAY-HIP-001",
        display="X-Ray Left Hip AP and Lateral",
        status="final",
        conclusion="Displaced intracapsular fracture of left neck of femur (Garden IV).",
        full_report="""X-RAY LEFT HIP — AP AND LATERAL VIEWS

Clinical indication: Fall from standing, left hip pain, unable to weight bear.

Findings:
- Displaced intracapsular fracture of the left neck of femur.
- Garden classification IV (complete displacement).
- No acetabular fracture.
- Moderate osteoarthritis changes at the hip joint bilaterally.
- Osteoporotic bone density noted.
- Right hip unremarkable.

Impression: Displaced left neck of femur fracture — Garden IV. Urgent orthopaedic review required.

Reported by: Dr. Kevin Tran, Radiologist."""
    ))

    db.add(DiagnosticReport(
        patient_id="pat-003", encounter_id="enc-003",
        timestamp=ts(adm3, days=3, hours=6), category="imaging", code="XRAY-HIP-002",
        display="X-Ray Left Hip Post-ORIF",
        status="final",
        conclusion="Satisfactory position of femoral nail and screw fixation. No complications.",
        full_report="""POST-OPERATIVE X-RAY LEFT HIP — AP VIEW

Clinical indication: Post-ORIF check.

Findings:
- Intramedullary femoral nail in situ with satisfactory position.
- Lag screw across fracture site in good position.
- Fracture fragments well approximated.
- No hardware failure or loosening.
- No new fractures identified.

Impression: Satisfactory post-operative appearances following ORIF of left NOF fracture.

Reported by: Dr. Kevin Tran, Radiologist."""
    ))

    db.add(Procedure(
        patient_id="pat-003", encounter_id="enc-003",
        timestamp=ts(adm3, days=1, hours=7), code="PROC-ORIF-NOF",
        display="Open Reduction Internal Fixation — Left Neck of Femur",
        performer="Dr. Simon Park (Orthopaedic Surgeon), Dr. Hayley Moss (Anaesthetist)",
        status="completed",
        notes="""OPERATIVE NOTE

Procedure: ORIF left neck of femur fracture
Date: Day 1, 07:30

Anaesthesia: Spinal anaesthesia

Patient positioned supine on fracture table.
Traction applied with image intensifier confirmation.
Lateral incision over proximal femur.
Intramedullary nail inserted with fluoroscopic guidance.
Lag screw advanced across fracture site.
Satisfactory position confirmed on AP and lateral screening.

Estimated blood loss: 180mL
Complications: None
Duration: 75 minutes

Post-op: No weight bearing left leg until physio review. DVT prophylaxis — Enoxaparin.
Ramipril held intra-op, restart Day 1 post-op."""
    ))

    notes3 = [
        (adm3, "admission", "Dr. Simon Park", "Orthopaedic Surgeon",
         """ADMISSION NOTE

Patient: Robert Nguyen, 78M
Presenting complaint: Fall from standing in garden. Left hip pain, unable to weight bear.

History: Tripped on garden step. Left hip pain immediate. Unable to stand. Ambulance brought in.
Background: Osteoporosis (on alendronate), HTN, mild CKD. Aspirin 100mg daily.

Examination:
- HR 94, BP 148/86, SpO2 96%
- Pain 8/10 left hip.
- Left leg: shortened and externally rotated.
- Marked groin tenderness.
- Neurovascular intact distally.

X-ray: Garden IV left NOF fracture.

Plan:
1. Analgesia: IV Paracetamol. Avoid codeine (allergy: nausea).
2. Hold Aspirin pre-operatively
3. Orthopaedic list tomorrow — ORIF left NOF
4. Anaesthetic review tonight
5. Pre-op bloods, ECG, group and hold
6. DVT prophylaxis post-op
7. Renal team aware — mild CKD"""),
        (ts(adm3, days=1), "progress", "Dr. Simon Park", "Orthopaedic Surgeon",
         """PRE-OPERATIVE NOTE — Day 1

Patient stable overnight. Pain managed with IV paracetamol, pain now 6/10.
Bloods: Hgb 136, INR 1.1, Cr 124 (baseline CKD).
ECG: Normal sinus rhythm.
Cleared by anaesthesia for spinal.

Plan: ORIF left NOF today 07:30. Consented and marked."""),
        (ts(adm3, days=2), "progress", "Dr. Simon Park", "Orthopaedic Surgeon",
         """POST-OPERATIVE NOTE — Day 2

Uncomplicated ORIF performed yesterday. Spinal anaesthesia. 
Overnight well. Minimal nausea (treated with Ondansetron — codeine not used).
Pain 4/10 — oral paracetamol and PRN tramadol.
Hgb 114 post-op (expected drop). No transfusion required.

Physio reviewed: Commenced weight-of-leg mobilisation with walking frame.

Plan: Continue mobilisation. Resume Ramipril. Continue Enoxaparin."""),
        (ts(adm3, days=3), "progress", "Dr. Simon Park", "Orthopaedic Surgeon",
         """PROGRESS NOTE — Day 3

Pain 3/10 at rest. Mobilising with physio — 10 metres with frame.
Post-op X-ray: satisfactory fixation.
CRP 44 (improving), WBC normalising.
Renal: Cr 128 — stable, monitoring.

Plan: Increase mobilisation. OT home assessment referral."""),
        (ts(adm3, days=4), "progress", "Dr. Simon Park", "Orthopaedic Surgeon",
         """PROGRESS NOTE — Day 4

Mobilising 20m with frame independently. Pain 2/10.
Hgb 118 — stable. CRP 22. Cr 118.

OT home assessment: home modifications recommended (grab rails, shower chair).
Plan: Discharge tomorrow pending physio clearance. Outpatient rehab referral."""),
        (ts(adm3, days=2, hours=4), "progress", "Jessica Lowe", "Physiotherapist",
         """PHYSIOTHERAPY NOTE — Day 2 post-op

Initial post-op physiotherapy review.
Patient alert and cooperative. Pain 4/10 with movement.
Commenced sitting over edge of bed. Transferred to chair.
Weight-of-leg mobilisation with walking frame — 5 metres.
Hip precautions discussed. No hip flexion >90 degrees.

Plan: Twice daily physiotherapy. Progress mobilisation as tolerated."""),
        (ts(adm3, days=3, hours=10), "progress", "Jessica Lowe", "Physiotherapist",
         """PHYSIOTHERAPY NOTE — Day 3

Mobilising 10 metres with walking frame, supervision.
Stair practice commenced — managed 4 steps with rail.
Pain 3/10. Compliant with hip precautions.

Discharge goal: 20 metres with frame independently + safe home environment."""),
    ]
    for t, ntype, author, role, content in notes3:
        db.add(ClinicalNote(patient_id="pat-003", encounter_id="enc-003",
            timestamp=t, note_type=ntype, author=author, author_role=role, content=content))

    db.add(DischargeSummary(
        patient_id="pat-003", encounter_id="enc-003",
        timestamp=ts(adm3, days=5, hours=7),
        summary_text="""DISCHARGE SUMMARY

Patient: Robert Nguyen | DOB: 22/03/1945 | MRN: MRN-003
Admission: 15/03/2024 | Discharge: 20/03/2024
Ward: Orthopaedic 4C | Consultant: Dr. Simon Park

Presenting Complaint: Fall from standing, left hip pain, unable to weight bear.

Diagnosis: Displaced left neck of femur fracture (Garden IV) in context of osteoporosis.

Treatment:
- ORIF left neck of femur (16/03/2024) — uncomplicated
- Analgesia: IV paracetamol → oral, tramadol PRN (codeine avoided — allergy)
- DVT prophylaxis: Enoxaparin 40mg daily
- Physiotherapy commenced Day 2 post-op

Discharge medications:
1. Paracetamol 1g QID PRN oral
2. Tramadol 50mg PO PRN Q6H (max 7 days, then cease)
3. Enoxaparin 40mg SC daily x 28 days total (continue at home)
4. Ramipril 5mg daily (resumed)
5. Alendronate 70mg weekly (resume next Monday)
6. Aspirin 100mg daily (resumed)

Follow-up:
- Orthopaedic clinic 2 weeks
- GP in 1 week — wound check, renal function review
- Outpatient physiotherapy 3x per week
- Bone density review — DEXA scan pending
- Home modifications: grab rails installed, shower chair obtained""",
        structured_data={
            "diagnosis": "Left NOF fracture Garden IV",
            "procedure": "ORIF left NOF",
            "los_days": 5,
            "complications": None,
            "post_op_hgb_nadir": 114,
            "discharge_mobility": "20m with walking frame",
            "discharge_medications": ["Paracetamol 1g QID PRN", "Tramadol 50mg PRN x7d", "Enoxaparin 40mg x28d", "Ramipril 5mg daily", "Alendronate 70mg weekly", "Aspirin 100mg daily"]
        },
        generated_by="manual"
    ))

    db.commit()
    print("Seeding complete. 3 patients loaded.")
    db.close()

if __name__ == "__main__":
    seed()
