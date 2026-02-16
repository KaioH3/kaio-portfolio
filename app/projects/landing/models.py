"""
Landing Page Pydantic Models
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class LeadCapture(BaseModel):
    """Lead capture form data"""
    nome: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    telefone: str = Field(..., pattern=r"^\+?[1-9]\d{1,14}$")  # E.164 format
    interesse: Optional[str] = None


class LeadResponse(BaseModel):
    """Response after lead capture"""
    status: str
    message: str
    lead_id: Optional[str] = None


class CourseInfo(BaseModel):
    """Course information for template"""
    name: str
    price: str
    price_promo: str
    currency: str
    checkout_url: str
    whatsapp: str
