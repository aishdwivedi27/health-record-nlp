# Quick Fix: "Order a new X-ray" Should Create Order

## Problem
When doctor says "order a new x ray":
- ❌ System doesn't create an order
- ❌ Just says "submit through ordering system"
- ❌ No order is made in database

## Solution
Detect "order", "request", "arrange" keywords and automatically create orders.

## Implementation

**File: `backend/app/routers/nlp_query.py`**

Add this function at the TOP (before other functions):

```python
def detect_and_parse_order(question: str) -> dict:
    """Detect if user is trying to ORDER something"""
    
    order_keywords = ['order', 'request', 'arrange', 'need', 'book', 'schedule', 'get']
    order_types = {
        'xray': ['xray', 'x-ray', 'x ray', 'radiograph', 'chest x', 'hip x', 'pelvis x'],
        'blood_work': ['blood', 'blood work', 'blood test', 'labs', 'lab work', 'bloodwork'],
        'ct_scan': ['ct', 'ct scan', 'cat scan', 'ct imaging'],
        'ultrasound': ['ultrasound', 'echo', 'echocardiogram'],
        'mri': ['mri', 'magnetic resonance'],
        'ecg': ['ecg', 'ekg', 'electrocardiogram'],
        'endoscopy': ['endoscopy'],
        'cardiology_consult': ['cardiology', 'cardiologist', 'cardiac'],
        'neurology_consult': ['neurology', 'neurologist'],
        'pulmonology_consult': ['pulmonology', 'pulmonologist']
    }
    
    question_lower = question.lower()
    
    # Check if order keywords present
    is_order = any(kw in question_lower for kw in order_keywords)
    
    if not is_order:
        return {"is_order": False}
    
    # Find order type
    detected_type = None
    for order_type, keywords in order_types.items():
        if any(keyword in question_lower for keyword in keywords):
            detected_type = order_type
            break
    
    return {
        "is_order": True,
        "order_type": detected_type,
        "full_question": question
    }
```

Now add this to the START of `nlp_query()` function (right after `start_time = datetime.utcnow()`):

```python
# FIRST: Check if this is an ORDER request
order_info = detect_and_parse_order(request.question)

if order_info["is_order"]:
    if order_info["order_type"]:
        # Create order in database
        order_id = str(uuid.uuid4())
        order_type = order_info["order_type"]
        
        try:
            from sqlalchemy import text
            insert_query = text("""
                INSERT INTO orders (id, patient_id, order_type, description, requested_by, status, created_at)
                VALUES (:id, :patient_id, :order_type, :description, :requested_by, :status, :created_at)
            """)
            
            db.execute(insert_query, {
                "id": order_id,
                "patient_id": request.patient_id,
                "order_type": order_type,
                "description": request.question,
                "requested_by": "AI Assistant",
                "status": "pending",
                "created_at": datetime.utcnow()
            })
            db.commit()
            
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return QueryResponse(
                patient_id=request.patient_id,
                question=request.question,
                intent={"type": "order", "order_type": order_type},
                structured_data={
                    "order_created": True,
                    "order_id": order_id,
                    "order_type": order_type,
                    "status": "PENDING"
                },
                narrative_summary=f"✅ ORDER CREATED for {order_type.replace('_', ' ').title()}\n\nOrder ID: {order_id}\nStatus: PENDING - Awaiting approval\n\nThe order has been submitted to the ordering system.",
                execution_time_ms=execution_time
            )
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return QueryResponse(
                patient_id=request.patient_id,
                question=request.question,
                intent={"type": "order", "error": True},
                structured_data={"error": str(e)},
                narrative_summary=f"❌ Error creating order: {str(e)}",
                execution_time_ms=execution_time
            )
    else:
        # Order detected but type unclear
        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        return QueryResponse(
            patient_id=request.patient_id,
            question=request.question,
            intent={"type": "order", "unclear": True},
            structured_data={"needs_clarification": True},
            narrative_summary="I understand you want to order something, but I need clarification.\n\nWhat would you like to order?\n\n📋 Available orders:\n• X-ray\n• Blood work\n• CT scan\n• Ultrasound\n• MRI\n• ECG\n• Cardiology consult\n• Neurology consult\n• Pulmonology consult",
            execution_time_ms=execution_time
        )

# If NOT an order, continue with regular query processing...
```

Don't forget the imports at the top of the file:
```python
import uuid
from sqlalchemy import text
```

## Testing

Test with these commands:

```
Doctor: "order a new x ray"
System: ✅ ORDER CREATED
        Order ID: [uuid]
        Status: PENDING
        Message: "ORDER CREATED for X-ray"

Doctor: "request blood work"
System: ✅ ORDER CREATED
        Order ID: [uuid]
        Status: PENDING

Doctor: "get a ct scan"
System: ✅ ORDER CREATED
        Order ID: [uuid]
        Status: PENDING

Doctor: "arrange cardiology consult"
System: ✅ ORDER CREATED
        Order ID: [uuid]
        Status: PENDING

Doctor: "order something"
System: ❌ Needs clarification
        "What would you like to order? X-ray, Blood work, CT scan..."
```

## Result

✅ "order x ray" → Creates order immediately
✅ "request blood work" → Creates order
✅ "arrange cardiology consult" → Creates order
✅ Order appears in database with PENDING status
✅ Order can be tracked in Orders tab
✅ Clear confirmation message to doctor

**Doctors can now order tests and consultations directly through chat!**
