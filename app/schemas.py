from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import List, Optional
from datetime import datetime

class RecipientInput(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    course_name: str = Field(..., min_length=2, max_length=150)

class BulkGenerationRequest(BaseModel):
    recipients: List[RecipientInput] = Field(..., min_items=1, max_items=500)

class CertificateResponse(BaseModel):
    id: str
    recipient_name: str
    recipient_email: str
    course_name: str
    status: str
    error_message: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class JobStatusResponse(BaseModel):
    job_id: str = Field(..., validation_alias="id")  # Maps database 'id' to schema 'job_id'
    status: str
    total_recipients: int
    successful_count: int
    failed_count: int
    created_at: datetime
    certificates: List[CertificateResponse] = []
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)