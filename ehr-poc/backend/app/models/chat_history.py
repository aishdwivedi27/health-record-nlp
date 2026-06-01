from sqlalchemy import Column, String, DateTime, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()


class ChatMessage(Base):
    """Store AI Assistant chat messages"""
    __tablename__ = "chat_messages"
    
    id = Column(String, primary_key=True, index=True)
    patient_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    question = Column(Text)
    response_narrative = Column(Text)
    response_structured = Column(Text)  # JSON
    intent = Column(Text)  # JSON
    execution_time_ms = Column(float)
    

class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Order(Base):
    """Store medical orders/requests"""
    __tablename__ = "orders"
    
    id = Column(String, primary_key=True, index=True)
    patient_id = Column(String, index=True)
    order_type = Column(String)  # xray, blood_work, ct_scan, etc.
    description = Column(Text)
    requested_by = Column(String)  # Doctor name
    status = Column(String, default=OrderStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
