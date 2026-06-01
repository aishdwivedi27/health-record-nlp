from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.database import get_db
from datetime import datetime, timedelta
import json
import uuid
from app.routers.nlp_query import get_client, execute_query
from sqlalchemy import text

router = APIRouter(prefix="/ai/nlp", tags=["nlp_extended"])


class ChatHistoryRequest(BaseModel):
    patient_id: str


class ChatHistoryResponse(BaseModel):
    id: str
    timestamp: datetime
    question: str
    response_narrative: str
    execution_time_ms: float


class OrderRequest(BaseModel):
    patient_id: str
    order_type: str  # xray, blood_work, ct_scan, ultrasound, etc.
    description: str
    notes: Optional[str] = None


class OrderResponse(BaseModel):
    id: str
    patient_id: str
    order_type: str
    description: str
    status: str
    created_at: datetime


@router.get("/chat-history/{patient_id}")
def get_chat_history(patient_id: str, days: int = 30, db: Session = Depends(get_db)):
    """Get chat history for patient grouped by date"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    query_str = text("""
        SELECT id, timestamp, question, response_narrative, execution_time_ms
        FROM chat_messages
        WHERE patient_id = :patient_id AND timestamp >= :cutoff_date
        ORDER BY timestamp DESC
    """)
    
    result = db.execute(query_str, {"patient_id": patient_id, "cutoff_date": cutoff_date})
    rows = result.fetchall()
    
    # Group by date
    history_by_date = {}
    for row in rows:
        date_key = row[1].strftime("%Y-%m-%d")  # timestamp
        if date_key not in history_by_date:
            history_by_date[date_key] = []
        
        history_by_date[date_key].append({
            "id": row[0],
            "timestamp": row[1].isoformat(),
            "question": row[2],
            "response": row[3][:200] + "..." if len(row[3]) > 200 else row[3],
            "execution_time_ms": row[4]
        })
    
    return {
        "patient_id": patient_id,
        "history_by_date": history_by_date,
        "total_messages": sum(len(msgs) for msgs in history_by_date.values())
    }


@router.post("/create-order")
def create_order(request: OrderRequest, db: Session = Depends(get_db)):
    """Create a new medical order/request"""
    
    order_id = str(uuid.uuid4())
    
    # Validate order type
    valid_types = ["xray", "blood_work", "ct_scan", "ultrasound", "mri", "ecg", "endoscopy", "biopsy"]
    if request.order_type.lower() not in valid_types:
        return {
            "error": f"Invalid order type. Valid types: {', '.join(valid_types)}",
            "available_orders": valid_types
        }
    
    insert_query = text("""
        INSERT INTO orders (id, patient_id, order_type, description, requested_by, status, created_at, notes)
        VALUES (:id, :patient_id, :order_type, :description, :requested_by, :status, :created_at, :notes)
    """)
    
    db.execute(insert_query, {
        "id": order_id,
        "patient_id": request.patient_id,
        "order_type": request.order_type.lower(),
        "description": request.description,
        "requested_by": "AI Assistant",
        "status": "pending",
        "created_at": datetime.utcnow(),
        "notes": request.notes
    })
    db.commit()
    
    return {
        "success": True,
        "order_id": order_id,
        "order_type": request.order_type,
        "status": "pending",
        "message": f"Order created for {request.order_type}. Awaiting approval."
    }


@router.get("/pending-orders/{patient_id}")
def get_pending_orders(patient_id: str, db: Session = Depends(get_db)):
    """Get pending orders for a patient"""
    
    query_str = text("""
        SELECT id, order_type, description, created_at, status
        FROM orders
        WHERE patient_id = :patient_id AND status = 'pending'
        ORDER BY created_at DESC
    """)
    
    result = db.execute(query_str, {"patient_id": patient_id})
    rows = result.fetchall()
    
    orders = [
        {
            "id": row[0],
            "type": row[1],
            "description": row[2],
            "requested": row[3].isoformat(),
            "status": row[4]
        }
        for row in rows
    ]
    
    return {
        "patient_id": patient_id,
        "pending_orders": orders,
        "count": len(orders)
    }


@router.post("/clarify-question")
def clarify_question(question: str, patient_id: str, db: Session = Depends(get_db)):
    """Ask clarifying questions for ambiguous requests"""
    
    client = get_client()
    
    clarify_prompt = f"""
    A doctor asked: "{question}"
    
    This question is ambiguous or could mean multiple things.
    
    Ask 2-3 clarifying questions to understand what they want.
    Format as a list with bullet points.
    
    Examples of ambiguous questions:
    - "Show me imaging" → Which type? (Xray, CT, MRI, Ultrasound?)
    - "Latest report" → What kind? (Blood, Imaging, Procedure notes?)
    - "Check vitals" → Latest? Trend? Compare? Specific vitals?
    - "Lab report" → All labs? Specific tests? Blood or other?
    
    Be conversational and helpful. Suggest examples.
    """
    
    response = client.messages.create(
        model="claude-opus-4-1",
        max_tokens=300,
        messages=[{"role": "user", "content": clarify_prompt}]
    )
    
    return {
        "question": question,
        "is_ambiguous": True,
        "clarification": response.content[0].text,
        "suggestions": [
            "Please specify which type of report/test",
            "Would you like the latest or a comparison?",
            "Should I search all results or recent ones?"
        ]
    }
