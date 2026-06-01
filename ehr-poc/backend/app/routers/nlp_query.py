from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Any, Optional, List
from app.database import get_db
from app.models.models import (
    Patient, Encounter, Observation, Medication, DiagnosticReport, 
    Procedure, ClinicalNote, DischargeSummary
)
from datetime import datetime, timedelta
import json
import os
from anthropic import Anthropic

router = APIRouter(prefix="/ai/nlp", tags=["nlp_query"])

# Lazy initialization of Anthropic client
_client = None

def get_client():
    """Get or create Anthropic client with API key from environment"""
    global _client
    if _client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable not set. "
                "Please create a .env file in the backend directory with: "
                "ANTHROPIC_API_KEY=sk-ant-your-key-here"
            )
        try:
            _client = Anthropic(api_key=api_key)
        except Exception as e:
            raise RuntimeError(
                f"Failed to initialize Anthropic client: {str(e)}. "
                f"Please ensure your API key is valid and anthropic package is up to date. "
                f"Try: pip install --upgrade anthropic"
            )
    return _client


class QueryRequest(BaseModel):
    patient_id: str
    question: str


class QueryResponse(BaseModel):
    patient_id: str
    question: str
    intent: dict
    structured_data: Any
    narrative_summary: str
    execution_time_ms: float


def extract_intent(question: str) -> dict:
    """
    Use Claude to extract intent from natural language query.
    Returns intent structure: {data_type, action, filters, time_range}
    """
    client = get_client()
    
    intent_prompt = f"""
    Analyze this doctor's question about a patient's EHR and extract the intent.
    
    Question: "{question}"
    
    Return ONLY valid JSON (no markdown, no explanation):
    {{
        "data_types": ["observation", "medication", "diagnostic_report", "clinical_note", "procedure", "encounter"],
        "primary_data_type": "one of the above",
        "action": "retrieve|compare|summarize|filter|latest|count",
        "report_type": null or specific type like "blood", "xray", "ct", "lab",
        "medication_status": null or "active|inactive|all",
        "observation_types": null or ["vital", "lab", "imaging"],
        "time_range": {{
            "days_back": number or null,
            "specific_date": "YYYY-MM-DD" or null,
            "comparison_count": number or null
        }},
        "entities": ["identified entities from question"],
        "confidence": 0.0-1.0
    }}
    
    Examples:
    - "Is there a latest blood report?" → {{"primary_data_type": "diagnostic_report", "action": "latest", "report_type": "blood", "time_range": {{"days_back": 30}}}}
    - "Compare last 2 blood reports" → {{"primary_data_type": "diagnostic_report", "action": "compare", "report_type": "blood", "time_range": {{"comparison_count": 2}}}}
    - "What medications are active?" → {{"primary_data_type": "medication", "action": "filter", "medication_status": "active"}}
    - "Latest vitals" → {{"primary_data_type": "observation", "action": "latest", "observation_types": ["vital"]}}
    - "Summarize clinical notes" → {{"primary_data_type": "clinical_note", "action": "summarize"}}
    """
    
    response = client.messages.create(
        model="claude-opus-4-1",
        max_tokens=500,
        messages=[{"role": "user", "content": intent_prompt}]
    )
    
    try:
        intent_json = response.content[0].text.strip()
        # Remove markdown code blocks if present
        if intent_json.startswith("```"):
            intent_json = intent_json.split("```")[1]
            if intent_json.startswith("json"):
                intent_json = intent_json[4:]
        intent_json = intent_json.strip()
        return json.loads(intent_json)
    except:
        return {
            "primary_data_type": "diagnostic_report",
            "action": "retrieve",
            "confidence": 0.3
        }


def execute_query(patient_id: str, intent: dict, db: Session) -> dict:
    """
    Execute database queries based on extracted intent.
    Returns structured data matching the intent.
    """
    
    results = {
        "patient": {},
        "data": {},
        "metadata": {
            "data_type": intent.get("primary_data_type"),
            "action": intent.get("action"),
            "record_count": 0
        }
    }
    
    # Get patient info
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        return {"error": "Patient not found"}
    
    results["patient"] = {
        "id": patient.id,
        "name": f"{patient.first_name} {patient.last_name}",
        "mrn": patient.mrn,
        "dob": patient.dob
    }
    
    data_type = intent.get("primary_data_type")
    action = intent.get("action")
    time_range = intent.get("time_range", {})
    days_back = time_range.get("days_back") or 90  # Ensure it's never None
    
    cutoff_date = datetime.utcnow() - timedelta(days=int(days_back))
    
    # DIAGNOSTIC REPORTS (Blood, Xray, etc.)
    if data_type == "diagnostic_report":
        report_type = intent.get("report_type")
        
        # First try DiagnosticReport
        query = db.query(DiagnosticReport).filter(
            DiagnosticReport.patient_id == patient_id,
            DiagnosticReport.timestamp >= cutoff_date
        ).order_by(DiagnosticReport.timestamp.desc())
        
        if report_type:
            query = query.filter(DiagnosticReport.category.ilike(f"%{report_type}%"))
        
        reports = query.all()
        
        # If no DiagnosticReports found and looking for blood/lab work, search Observations instead
        if len(reports) == 0 and report_type and report_type.lower() in ["blood", "lab", "labs", "bloodwork", "blood work"]:
            obs_query = db.query(Observation).filter(
                Observation.patient_id == patient_id,
                Observation.timestamp >= cutoff_date,
                Observation.type.in_(["lab", "vital"])
            ).order_by(Observation.timestamp.desc())
            
            observations = obs_query.all()
            
            if action == "latest":
                # Get latest of each test type
                by_display = {}
                for obs in observations:
                    if obs.display not in by_display:
                        by_display[obs.display] = obs
                observations = list(by_display.values())[:5]  # Limit to 5 latest tests
            elif action == "compare":
                count = time_range.get("comparison_count", 2)
                observations = observations[:count]
            
            results["data"]["lab_observations"] = [
                {
                    "id": o.id,
                    "timestamp": o.timestamp.isoformat(),
                    "test_name": o.display,
                    "value": o.value,
                    "unit": o.unit,
                    "type": o.type,
                    "status": o.status
                }
                for o in observations
            ]
            results["metadata"]["record_count"] = len(observations)
            results["metadata"]["data_source"] = "lab_observations"
        else:
            # Use DiagnosticReports
            if action == "latest":
                reports = reports[:1]
            elif action == "compare":
                count = time_range.get("comparison_count", 2)
                reports = reports[:count]
            
            results["data"]["diagnostic_reports"] = [
                {
                    "id": r.id,
                    "timestamp": r.timestamp.isoformat(),
                    "category": r.category,
                    "type": r.display,
                    "findings": r.findings,
                    "conclusion": r.conclusion,
                    "status": r.status
                }
                for r in reports
            ]
            results["metadata"]["record_count"] = len(reports)
            results["metadata"]["data_source"] = "diagnostic_reports"
    
    # MEDICATIONS
    elif data_type == "medication":
        query = db.query(Medication).filter(
            Medication.patient_id == patient_id
        ).order_by(Medication.timestamp.desc())
        
        med_status = intent.get("medication_status")
        if med_status and med_status != "all":
            query = query.filter(Medication.status == med_status)
        
        medications = query.all()
        
        # Group by status for clarity
        active_meds = [m for m in medications if m.status == "active"]
        inactive_meds = [m for m in medications if m.status == "inactive"]
        
        results["data"]["medications"] = {
            "active": [
                {
                    "id": m.id,
                    "name": m.name,
                    "dose": m.dose,
                    "route": m.route,
                    "frequency": m.frequency,
                    "indication": m.indication,
                    "started": m.timestamp.isoformat()
                }
                for m in active_meds
            ],
            "inactive": [
                {
                    "id": m.id,
                    "name": m.name,
                    "dose": m.dose,
                    "route": m.route,
                    "frequency": m.frequency,
                    "indication": m.indication,
                    "status_as_of": m.timestamp.isoformat()
                }
                for m in inactive_meds
            ]
        }
        results["metadata"]["record_count"] = len(medications)
    
    # OBSERVATIONS (Vitals, Labs)
    elif data_type == "observation":
        query = db.query(Observation).filter(
            Observation.patient_id == patient_id,
            Observation.timestamp >= cutoff_date
        ).order_by(Observation.timestamp.desc())
        
        obs_types = intent.get("observation_types")
        if obs_types:
            query = query.filter(Observation.type.in_(obs_types))
        
        observations = query.all()
        
        if action == "latest":
            # Get latest of each type
            by_type = {}
            for obs in observations:
                if obs.type not in by_type:
                    by_type[obs.type] = obs
            observations = list(by_type.values())
        
        results["data"]["observations"] = [
            {
                "id": o.id,
                "timestamp": o.timestamp.isoformat(),
                "type": o.type,
                "display": o.display,
                "value": o.value,
                "value_string": o.value_string,
                "unit": o.unit,
                "status": o.status
            }
            for o in observations
        ]
        results["metadata"]["record_count"] = len(observations)
    
    # CLINICAL NOTES
    elif data_type == "clinical_note":
        notes = db.query(ClinicalNote).filter(
            ClinicalNote.patient_id == patient_id
        ).order_by(ClinicalNote.timestamp.desc()).all()
        
        results["data"]["clinical_notes"] = [
            {
                "id": n.id,
                "timestamp": n.timestamp.isoformat(),
                "type": n.type,
                "author": n.author,
                "subject": n.subject,
                "content": n.content
            }
            for n in notes
        ]
        results["metadata"]["record_count"] = len(notes)
    
    # PROCEDURES
    elif data_type == "procedure":
        procedures = db.query(Procedure).filter(
            Procedure.patient_id == patient_id,
            Procedure.timestamp >= cutoff_date
        ).order_by(Procedure.timestamp.desc()).all()
        
        results["data"]["procedures"] = [
            {
                "id": p.id,
                "timestamp": p.timestamp.isoformat(),
                "type": p.display,
                "performer": p.performer,
                "notes": p.notes,
                "status": p.status
            }
            for p in procedures
        ]
        results["metadata"]["record_count"] = len(procedures)
    
    return results


def create_order_from_request(patient_id: str, question: str, db: Session) -> Optional[dict]:
    """Create an order if user is requesting one"""
    try:
        from app.system_prompt_loader import detect_order_request
    except ImportError:
        return None
    
    import uuid
    from sqlalchemy import text
    
    order_info = detect_order_request(question)
    
    if not order_info["is_order"]:
        return None
    
    if not order_info["order_type"]:
        return {
            "is_order": True,
            "needs_clarification": True,
            "message": "I understand you want to order something. Which type?\n\n📋 Available orders:\n• X-ray\n• Blood work\n• CT scan\n• Ultrasound\n• MRI\n• ECG\n• Cardiology consult\n• Neurology consult\n• Pulmonology consult"
        }
    
    order_id = str(uuid.uuid4())
    order_type = order_info["order_type"]
    question_lower = question.lower()
    
    if any(word in question_lower for word in ["same", "last", "previous", "repeat", "again"]):
        description = f"Reorder: {order_type.replace('_', ' ').title()} (same as last order)"
    else:
        description = question
    
    try:
        insert_query = text("""
            INSERT INTO orders (id, patient_id, order_type, description, requested_by, status, created_at)
            VALUES (:id, :patient_id, :order_type, :description, :requested_by, :status, :created_at)
        """)
        
        db.execute(insert_query, {
            "id": order_id,
            "patient_id": patient_id,
            "order_type": order_type,
            "description": description,
            "requested_by": "AI Assistant",
            "status": "pending",
            "created_at": datetime.utcnow()
        })
        db.commit()
        
        return {
            "is_order": True,
            "order_created": True,
            "order_id": order_id,
            "order_type": order_type,
            "status": "PENDING",
            "message": f"✅ ORDER CREATED: {order_type.replace('_', ' ').title()}\n\nOrder ID: {order_id}\nStatus: PENDING - Awaiting approval"
        }
    except Exception as e:
        print(f"Error creating order: {e}")
        return {
            "is_order": True,
            "order_created": False,
            "error": str(e)
        }


def generate_narrative_summary(question: str, structured_data: dict, intent: dict) -> str:
    """
    Use Claude to generate a natural language summary of the results.
    """
    client = get_client()
    
    summary_prompt = f"""
    A doctor asked: "{question}"
    
    Here's the structured EHR data retrieved:
    {json.dumps(structured_data, indent=2, default=str)}
    
    Intent extracted: {json.dumps(intent, indent=2)}
    
    Generate a concise, clinically appropriate summary for the doctor. Include:
    1. Direct answer to their question
    2. Key clinical findings
    3. Any relevant timestamps or comparisons
    4. Actionable insights if appropriate
    
    Keep it brief (2-4 sentences max) but complete.
    """
    
    response = client.messages.create(
        model="claude-opus-4-1",
        max_tokens=300,
        messages=[{"role": "user", "content": summary_prompt}]
    )
    
    return response.content[0].text.strip()


@router.post("/query", response_model=QueryResponse)
def nlp_query(request: QueryRequest, db: Session = Depends(get_db)):
    """
    Natural Language Query endpoint.
    
    Takes a doctor's question and patient_id, extracts intent,
    executes optimized database queries, and returns both
    structured data and a narrative summary.
    """
    
    start_time = datetime.utcnow()
    
    # STEP 1: Check if this is an ORDER request (before intent extraction)
    order_result = create_order_from_request(request.patient_id, request.question, db)
    
    if order_result:
        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        if order_result.get("order_created"):
            return QueryResponse(
                patient_id=request.patient_id,
                question=request.question,
                intent={"type": "order", "order_type": order_result.get("order_type")},
                structured_data={"order_id": order_result.get("order_id"), "status": "PENDING"},
                narrative_summary=order_result.get("message"),
                execution_time_ms=execution_time
            )
        elif order_result.get("needs_clarification"):
            return QueryResponse(
                patient_id=request.patient_id,
                question=request.question,
                intent={"type": "order", "unclear": True},
                structured_data={"needs_clarification": True},
                narrative_summary=order_result.get("message"),
                execution_time_ms=execution_time
            )
    
    # STEP 2: Check if asking for "latest" without specifying type (AMBIGUOUS)
    question_lower = request.question.lower()
    
    # Check if asking for "latest" anything
    is_asking_latest = any(word in question_lower for word in ["latest", "recent", "most recent", "last"])
    
    # Check if they specified a type explicitly
    has_type = any(type_name in question_lower for type_name in ["blood", "xray", "x-ray", "imaging", "vital", "note", "ct", "mri", "ultrasound", "lab"])
    
    # If asking for "latest" but no specific type = AMBIGUOUS (regardless of singular/plural)
    if is_asking_latest and not has_type and any(word in question_lower for word in ["report", "reports", "test", "tests", "result", "results", "findings"]):
        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        return QueryResponse(
            patient_id=request.patient_id,
            question=request.question,
            intent={"type": "query", "data_type": "ambiguous", "action": "clarify"},
            structured_data={"ambiguous": True},
            narrative_summary="""I need clarification: Which report are you looking for?

📋 Available options:
• Blood reports (Labs) - Blood tests, lab values
• Imaging reports (X-ray, CT, MRI) - Diagnostic imaging
• Vital signs (BP, HR, Temperature) - Patient vitals
• Clinical notes (Doctor's notes) - Medical notes""",
            execution_time_ms=execution_time
        )
    
    # STEP 3: Extract intent using Claude for regular queries
    intent = extract_intent(request.question)
    
    # Execute query based on intent
    structured_data = execute_query(request.patient_id, intent, db)
    
    if "error" in structured_data:
        return QueryResponse(
            patient_id=request.patient_id,
            question=request.question,
            intent=intent,
            structured_data={"error": structured_data["error"]},
            narrative_summary=f"Error: {structured_data['error']}",
            execution_time_ms=0
        )
    
    # Generate narrative summary
    narrative = generate_narrative_summary(
        request.question,
        structured_data,
        intent
    )
    
    execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
    
    return QueryResponse(
        patient_id=request.patient_id,
        question=request.question,
        intent=intent,
        structured_data=structured_data,
        narrative_summary=narrative,
        execution_time_ms=execution_time
    )


@router.get("/sample-queries")
def get_sample_queries():
    """Return example questions doctors can ask."""
    return {
        "examples": [
            "Is there a latest blood report available?",
            "Show me the most recent X-ray report",
            "Compare the last 2 blood reports",
            "What active medications does the patient have?",
            "What are the closed medications and their dosages?",
            "What are the patient's latest vital signs?",
            "Summarize the clinical notes from latest to earliest",
            "What procedures have been performed recently?",
            "Show me all lab results from the past month",
            "Is there any imaging available in the last 3 months?",
            "List all current medications with their dosages and frequencies",
            "What was the patient's temperature trend over the last week?"
        ]
    }
