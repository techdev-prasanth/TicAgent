from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

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
    id : int
    is_active : bool
    create_ad : datetime
    updated_at : datetime


    class Config:
        model_config = True


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





    






