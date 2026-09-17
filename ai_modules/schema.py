from pydantic import BaseModel, Field , ConfigDict
from typing import List, Optional
from datetime import datetime
import uuid

#Account & Login
#Billing & Payments
#Refund & Cancellation
#Technical Problem
#Bug / Error
#Performance
#Data Problem
#Integration / API
#Email / Notification
# Product / Feature
# Feature Request
# Security
# Order / Service
# How-to / General Inquiry
# Service Outage
from enum import Enum

class TicketCategorySchema(BaseModel):
    """ categories for the customer ticket"""
    name : str = Field(description="Ticket category")
    code : str = Field(description="Ticket categoyry's code ex: BILLING_ISSUE")
    description : Optional[str] = Field(None,example="Handles invoice and payments")


class TicketCategoryResponse(TicketCategorySchema):
    id : uuid.UUID
    created_at : Optional[datetime] | None
    updated_at : Optional[datetime] | None
    model_config = ConfigDict(from_attributes=True)


class TicketPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"



class TicketSentiment(str, Enum):
    POSITIVE = "Positive"
    NEUTRAL = "Neutral"
    FRUSTRATED = "Frustrated"
    ANGRY = "Angry"


class TicketCreate(BaseModel):
    customer_id: str = Field(example="CUST-1042",description="it denotes the customer's id")
    customer_message: str = Field(example="I was double charged for my subscription",description="customers questions")
    category_code: str = Field(example="BILLING_PAYMENT")
    consent_given: bool = Field(True, description="Customer consent for LLM processing")





class TicketClassfication(BaseModel):
    category_code : str = Field(description="Selected category code from the allowed list")
    priority : TicketPriority = Field(description="Assessed priority level based on customer message urgency")
    sentiment : TicketSentiment = Field(description="Customer emotion/sentiment detected in the message")
    description : str = Field(description="Brief explanation for the assigned classification, priority, and sentiment")



class CustomerMessage(BaseModel):
    message : str = Field(description="it contains customer message")
