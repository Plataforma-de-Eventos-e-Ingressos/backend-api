from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from uuid import UUID
from app.models.models import RoleEnum

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
    description: Optional[str] = None

class EventCreate(EventBase):
    pass
class EventResponse(EventBase):
    id: UUID
    organizer_id: UUID
    description: Optional[str] = None

    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
class UserResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    role: RoleEnum

    class Config:
        from_attributes = True

class TicketCreate(BaseModel):
    event_id: UUID
    seat: Optional[str] = None