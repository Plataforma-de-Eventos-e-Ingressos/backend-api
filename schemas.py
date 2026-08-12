from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from uuid import UUID

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class EventBase(BaseModel):
    title: str
    event_datetime: datetime
    location: str
    price: float
    total_capacity: int
    external_api_id: Optional[str] = None

class EventCreate(EventBase):
    pass
class EventResponse(EventBase):
    id: UUID
    organizer_id: UUID

    class Config:
        from_attributes = True
