# ADD THESE FUNCTIONS TO backend/app/routers/nlp_query.py

# ============================================================
# FUNCTION 1: Find Latest Across All Data Types
# ============================================================

def find_latest_across_all_types(patient_id, db):
    """Find the ACTUAL latest item across ALL data types by comparing timestamps"""
    
    all_items = []
    
    # Get latest DiagnosticReport (imaging)
    try:
        latest_diagnostic = db.query(DiagnosticReport).filter(
            DiagnosticReport.patient_id == patient_id
        ).order_by(DiagnosticReport.timestamp.desc()).first()
        
        if latest_diagnostic:
            all_items.append({
                'timestamp': latest_diagnostic.timestamp,
                'type': 'diagnostic_report',
                'data': latest_diagnostic,
                'display': f"{latest_diagnostic.display}"
            })
    except Exception as e:
        print(f"Error querying diagnostic reports: {e}")
    
    # Get latest Lab Observation
    try:
        latest_lab = db.query(Observation).filter(
            Observation.patient_id == patient_id,
            Observation.type == 'lab'
        ).order_by(Observation.timestamp.desc()).first()
        
        if latest_lab:
            all_items.append({
                'timestamp': latest_lab.timestamp,
                'type': 'lab_observation',
                'data': latest_lab,
                'display': f"Blood: {latest_lab.display}"
            })
    except Exception as e:
        print(f"Error querying lab observations: {e}")
    
    # Get latest Vital Observation
    try:
        latest_vital = db.query(Observation).filter(
            Observation.patient_id == patient_id,
            Observation.type == 'vital'
        ).order_by(Observation.timestamp.desc()).first()
        
        if latest_vital:
            all_items.append({
                'timestamp': latest_vital.timestamp,
                'type': 'vital_observation',
                'data': latest_vital,
                'display': f"Vital: {latest_vital.display}"
            })
    except Exception as e:
        print(f"Error querying vital observations: {e}")
    
    # Get latest Clinical Note
    try:
        latest_note = db.query(ClinicalNote).filter(
            ClinicalNote.patient_id == patient_id
        ).order_by(ClinicalNote.timestamp.desc()).first()
        
        if latest_note:
            all_items.append({
                'timestamp': latest_note.timestamp,
                'type': 'clinical_note',
                'data': latest_note,
                'display': f"Note: {latest_note.subject}"
            })
    except Exception as e:
        print(f"Error querying clinical notes: {e}")
    
    # Sort by timestamp DESC and return the ACTUAL latest
    if all_items:
        all_items.sort(key=lambda x: x['timestamp'], reverse=True)
        return all_items[0]  # Most recent item
    
    return None


# ============================================================
# FUNCTION 2: Format Latest Item Response
# ============================================================

def format_latest_response(latest_item, patient_id):
    """Format the response for the latest item"""
    
    if not latest_item:
        return {
            "error": "No reports found",
            "patient_id": patient_id
        }
    
    item_type = latest_item['type']
    data = latest_item['data']
    
    if item_type == 'diagnostic_report':
        return {
            "patient_id": patient_id,
            "data_type": "diagnostic_report",
            "diagnostic_reports": [{
                "id": data.id,
                "timestamp": data.timestamp.isoformat(),
                "category": data.category,
                "display": data.display,
                "findings": data.findings,
                "conclusion": data.conclusion,
                "status": data.status
            }],
            "metadata": {
                "note": "Latest across ALL data types (imaging, blood, vitals, notes)"
            }
        }
    
    elif item_type in ['lab_observation', 'vital_observation']:
        return {
            "patient_id": patient_id,
            "data_type": "observation",
            "observation_type": item_type.replace('_observation', ''),
            "lab_observations": [{
                "id": data.id,
                "timestamp": data.timestamp.isoformat(),
                "test_name": data.display,
                "value": data.value,
                "unit": data.unit,
                "reference_range": data.reference_range,
                "status": data.status
            }],
            "metadata": {
                "note": "Latest across ALL data types (imaging, blood, vitals, notes)"
            }
        }
    
    elif item_type == 'clinical_note':
        return {
            "patient_id": patient_id,
            "data_type": "clinical_note",
            "notes": [{
                "id": data.id,
                "timestamp": data.timestamp.isoformat(),
                "subject": data.subject,
                "content": data.content[:500] + "..." if len(data.content) > 500 else data.content,
                "author": data.author
            }],
            "metadata": {
                "note": "Latest across ALL data types (imaging, blood, vitals, notes)"
            }
        }


# ============================================================
# FUNCTION 3: Handle Order Creation in nlp_query endpoint
# ============================================================

# At the START of the nlp_query() function, add this BEFORE intent extraction:

def create_order_from_request(patient_id, question, db):
    """Create an order if user is requesting one"""
    from app.system_prompt_loader import detect_order_request
    import uuid
    from sqlalchemy import text
    
    order_info = detect_order_request(question)
    
    if not order_info["is_order"]:
        return None  # Not an order request
    
    if not order_info["order_type"]:
        # Order detected but type unclear - need clarification
        return {
            "is_order": True,
            "needs_clarification": True,
            "message": "I understand you want to order something, but I need clarification.\n\n📋 Available orders:\n• X-ray\n• Blood work\n• CT scan\n• Ultrasound\n• MRI\n• ECG\n• Cardiology consult\n• Neurology consult\n• Pulmonology consult"
        }
    
    # Create the order
    order_id = str(uuid.uuid4())
    order_type = order_info["order_type"]
    
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
            "is_order": True,
            "order_created": True,
            "order_id": order_id,
            "order_type": order_type,
            "status": "PENDING",
            "message": f"✅ ORDER CREATED for {order_type.replace('_', ' ').title()}\n\nOrder ID: {order_id}\nStatus: PENDING - Awaiting approval"
        }
    except Exception as e:
        return {
            "is_order": True,
            "order_created": False,
            "error": str(e)
        }


# ============================================================
# USAGE IN nlp_query() endpoint:
# ============================================================

"""
@router.post("/query", response_model=QueryResponse)
def nlp_query(request: QueryRequest, db: Session = Depends(get_db)):
    start_time = datetime.utcnow()
    
    # STEP 1: Check if this is an ORDER request
    order_result = create_order_from_request(request.patient_id, request.question, db)
    
    if order_result:
        if order_result.get("order_created"):
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return QueryResponse(
                patient_id=request.patient_id,
                question=request.question,
                intent={"type": "order", "order_type": order_result["order_type"]},
                structured_data={"order_id": order_result["order_id"], "status": "PENDING"},
                narrative_summary=order_result["message"],
                execution_time_ms=execution_time
            )
        elif order_result.get("needs_clarification"):
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return QueryResponse(
                patient_id=request.patient_id,
                question=request.question,
                intent={"type": "order", "unclear": True},
                structured_data={"needs_clarification": True},
                narrative_summary=order_result["message"],
                execution_time_ms=execution_time
            )
    
    # STEP 2: Check if this is a "LATEST" query across all types
    from app.system_prompt_loader import detect_latest_query
    
    if detect_latest_query(request.question):
        latest = find_latest_across_all_types(request.patient_id, db)
        if latest:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            structured_data = format_latest_response(latest, request.patient_id)
            
            return QueryResponse(
                patient_id=request.patient_id,
                question=request.question,
                intent={"type": "query", "data_type": "latest_across_all"},
                structured_data=structured_data,
                narrative_summary=generate_narrative_summary(request.question, structured_data, {"type": "latest"}),
                execution_time_ms=execution_time
            )
    
    # STEP 3: Regular intent extraction for other queries
    intent = extract_intent(request.question)
    structured_data = execute_query(request.patient_id, intent, db)
    
    # ... rest of function
"""
