# FINAL COMPLETE NLP QUERY IMPLEMENTATION
# Add these imports at the top of the file
import re
import uuid
from sqlalchemy import text

# Add this function BEFORE the nlp_query endpoint

def quick_order_detect_and_create(question: str, patient_id: str, db) -> dict:
    """Quick order detection and creation with word boundaries"""
    question_lower = question.lower()
    
    order_keywords = ["order", "reorder", "request", "arrange", "book", "schedule", "get", "repeat", "remake", "redo", "need"]
    order_type_map = {
        'xray': ["xray", "x-ray", "x ray", "chest x", "radiograph"],
        'blood_work': ["blood", "blood work", "blood test", "labs"],
        'ct_scan': ["ct", "ct scan", "cat scan"],
        'ultrasound': ["ultrasound", "echo"],
        'mri': ["mri", "magnetic"],
        'ecg': ["ecg", "ekg"],
        'cardiology_consult': ["cardiology", "cardiologist"],
    }
    
    # Word boundary check
    is_order = False
    for kw in order_keywords:
        pattern = rf'\b{kw}\b'
        if re.search(pattern, question_lower):
            is_order = True
            break
    
    if not is_order:
        return None
    
    # Find type
    order_type = None
    for otype, type_keywords in order_type_map.items():
        if any(keyword in question_lower for keyword in type_keywords):
            order_type = otype
            break
    
    if not order_type:
        return {"is_order": True, "needs_clarification": True}
    
    # Create order
    order_id = str(uuid.uuid4())
    try:
        insert_query = text("""
            INSERT INTO orders (id, patient_id, order_type, description, requested_by, status, created_at)
            VALUES (:id, :patient_id, :order_type, :description, :requested_by, :status, :created_at)
        """)
        
        db.execute(insert_query, {
            "id": order_id,
            "patient_id": patient_id,
            "order_type": order_type,
            "description": question,
            "requested_by": "AI Assistant",
            "status": "pending",
            "created_at": datetime.utcnow()
        })
        db.commit()
        
        return {
            "order_created": True,
            "order_id": order_id,
            "order_type": order_type
        }
    except Exception as e:
        print(f"Error creating order: {e}")
        return None

# REPLACE THE ENTIRE nlp_query() ENDPOINT WITH THIS:

@router.post("/query", response_model=QueryResponse)
def nlp_query(request: QueryRequest, db: Session = Depends(get_db)):
    """
    Complete NLP query endpoint with:
    1. Order detection & creation
    2. Ambiguity detection
    3. Intent extraction with system prompt
    4. Query execution
    """
    
    start_time = datetime.utcnow()
    question_lower = request.question.lower()
    
    # ============================================================
    # STEP 1: QUICK ORDER DETECTION (word boundary safe)
    # ============================================================
    order_result = quick_order_detect_and_create(request.question, request.patient_id, db)
    
    if order_result and order_result.get("order_created"):
        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        return QueryResponse(
            patient_id=request.patient_id,
            question=request.question,
            intent={"type": "order", "order_type": order_result["order_type"]},
            structured_data={"order_id": order_result["order_id"], "status": "PENDING"},
            narrative_summary=f"✅ ORDER CREATED: {order_result['order_type'].replace('_', ' ').title()}\n\nOrder ID: {order_result['order_id']}\nStatus: PENDING - Awaiting approval",
            execution_time_ms=execution_time
        )
    
    if order_result and order_result.get("needs_clarification"):
        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        return QueryResponse(
            patient_id=request.patient_id,
            question=request.question,
            intent={"type": "order", "unclear": True},
            structured_data={"needs_clarification": True},
            narrative_summary="I understand you want to order something. Which type?\n\n📋 Available orders:\n• X-ray\n• Blood work\n• CT scan\n• Ultrasound\n• MRI\n• ECG\n• Cardiology consult\n• Neurology consult\n• Pulmonology consult",
            execution_time_ms=0
        )
    
    # ============================================================
    # STEP 2: CHECK FOR AMBIGUOUS "LATEST" QUERY
    # ============================================================
    is_asking_latest = any(word in question_lower for word in ["latest", "recent", "most recent"])
    has_type = any(type_name in question_lower for type_name in ["blood", "xray", "imaging", "vital", "note", "ct", "mri"])
    is_asking_for_report = any(word in question_lower for word in ["report", "reports", "test", "tests", "result", "results"])
    
    if is_asking_latest and not has_type and is_asking_for_report:
        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        return QueryResponse(
            patient_id=request.patient_id,
            question=request.question,
            intent={"type": "query", "data_type": "ambiguous"},
            structured_data={"ambiguous": True},
            narrative_summary="""I need clarification: Which report are you looking for?

📋 Available options:
• Blood reports (Labs) - Blood tests, lab values
• Imaging reports (X-ray, CT, MRI) - Diagnostic imaging
• Vital signs (BP, HR, Temperature) - Patient vitals
• Clinical notes (Doctor's notes) - Medical notes""",
            execution_time_ms=execution_time
        )
    
    # ============================================================
    # STEP 3: EXTRACT INTENT WITH SYSTEM PROMPT
    # ============================================================
    intent = extract_intent(request.question)
    
    # ============================================================
    # STEP 4: EXECUTE QUERY
    # ============================================================
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
    narrative = generate_narrative_summary(request.question, structured_data, intent)
    
    execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
    
    return QueryResponse(
        patient_id=request.patient_id,
        question=request.question,
        intent=intent,
        structured_data=structured_data,
        narrative_summary=narrative,
        execution_time_ms=execution_time
    )

# UPDATE extract_intent() - REPLACE ENTIRE FUNCTION WITH THIS:

def extract_intent(question: str) -> dict:
    """Extract intent using Claude WITH system prompt and caching"""
    client = get_client()
    
    from app.system_prompt_loader import build_system_prompt_for_claude
    system_prompt = build_system_prompt_for_claude()
    
    user_message = f"""User question: "{question}"

Respond ONLY with JSON:
{{
  "is_ambiguous": true/false,
  "clarification_needed": "If ambiguous, what to ask",
  "primary_data_type": "diagnostic_report|medication|observation|clinical_note",
  "action": "retrieve|compare|summarize",
  "report_type": "blood|xray|ct|vital|note",
  "time_range": {{"days_back": 30}},
  "confidence": 0.9
}}"""
    
    try:
        response = client.messages.create(
            model="claude-opus-4-1",
            max_tokens=500,
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"}  # ENABLE PROMPT CACHING
                }
            ],
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        
        response_text = response.content[0].text.strip()
        
        # Strip markdown code blocks
        response_text = response_text.replace("```json", "").replace("```", "").strip()
        
        try:
            intent = json.loads(response_text)
        except json.JSONDecodeError:
            intent = {
                "is_ambiguous": True,
                "clarification_needed": response_text,
                "primary_data_type": "ambiguous"
            }
        
        return intent
        
    except Exception as e:
        print(f"Error extracting intent: {e}")
        return {"error": str(e), "primary_data_type": "unknown"}
