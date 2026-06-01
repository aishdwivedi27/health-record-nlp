# Synthetic FHIR EHR PoC

A local proof-of-concept EHR system with synthetic clinical data, FHIR-inspired APIs, and an AI discharge summary endpoint.

## Stack

- **Backend**: FastAPI + SQLAlchemy + SQLite
- **Frontend**: React (Vite) + Recharts
- **Data**: 3 synthetic inpatients with realistic 4–5 day clinical progressions

## Quick start

```bash
docker-compose up --build
```

- Frontend: http://localhost:5173
- Backend API docs: http://localhost:8000/docs

---

## Patients

| MRN | Patient | Diagnosis |
|---|---|---|
| MRN-001001 | James Harrington, 28M | Acute appendicitis → laparoscopic appendectomy |
| MRN-001002 | Margaret Okonkwo, 72F | Community-acquired pneumonia + cardiac workup (Type 2 MI) |
| MRN-001003 | Robert Stanton, 83M | Right subcapital neck of femur fracture → hemiarthroplasty |

---

## API reference

### Core

```bash
# List all patients
curl http://localhost:8000/patients

# Get one patient
curl http://localhost:8000/patients/{id}

# Full chronological timeline
curl http://localhost:8000/patients/{id}/timeline

# Observations (vitals + labs)
curl "http://localhost:8000/observations?patientId={id}"

# Medications
curl "http://localhost:8000/medications?patientId={id}"

# Diagnostic reports
curl "http://localhost:8000/reports?patientId={id}"
```

### AI-facing

```bash
# Full longitudinal bundle for LLM
curl http://localhost:8000/ai/patient-context/{patientId}

# Discharge-ready summarisation bundle
curl http://localhost:8000/ai/discharge-ready/{encounterId}

# Store an AI-generated discharge summary
curl -X POST http://localhost:8000/ai/discharge-summary \
  -H "Content-Type: application/json" \
  -d '{
    "patientId": "...",
    "encounterId": "...",
    "summaryText": "Patient admitted with...",
    "structuredData": {"diagnosis": "..."}
  }'
```

---

## Using the AI discharge summary (UI)

1. Open a patient in the frontend
2. Go to the **Discharge Summary** tab
3. Click **Load discharge bundle**
4. Click **Generate AI summary** — calls the Anthropic API directly from the browser

> The Claude API key is handled via the built-in proxy in Claude.ai artifacts. In standalone use, set your own key in the fetch headers.

---

## Re-seeding

The database auto-seeds on first startup. To re-seed manually:

```bash
docker-compose exec backend python -m app.seed.seed_data
```

---

## Data quality notes

- Lab trends match clinical trajectory (e.g. CRP peaks post-op then falls)
- Medications match diagnoses and patient allergies (Penicillin allergy → cefazolin, no amoxicillin)
- Warfarin held pre-operatively with Vitamin K reversal, INR tracked to therapeutic range
- Troponin rise in Patient 2 follows Type 2 MI pattern, not ACS
- Renal dosing applied in Patient 3 (enoxaparin reduced for CrCl 38)
