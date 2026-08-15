from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional, List
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

class EventCreate(BaseModel):
    title: str
    event_datetime: datetime
    location: str
    price: float
    total_capacity: int
    description: Optional[str] = None
    poster_url: Optional[str] = None
    has_assigned_seats: bool = False
    rows_count: Optional[int] = None  
    seats_per_row: Optional[int] = None

class EventUpdate(BaseModel):
    title: Optional[str] = None
    event_datetime: Optional[datetime] = None
    location: Optional[str] = None
    price: Optional[float] = None
    total_capacity: Optional[int] = None
    description: Optional[str] = None
    poster_url: Optional[str] = None
class EventResponse(EventBase):
    id: UUID
    title: str
    event_datetime: datetime
    location: str
    price: float
    total_capacity: int
    description: Optional[str] = None
    poster_url: Optional[str] = None
    has_assigned_seats: bool

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
    quantity: Optional[int] = 1 
    seat_ids: Optional[List[UUID]] = [] 
    seat: Optional[str] = None

class TicketResponse(BaseModel):
    id: UUID
    event_id: UUID
    seat: Optional[str] = None
    status: str
    qr_token: str
    event: EventResponse  # Traz os dados do evento embutidos (nome, data, local)

    model_config = ConfigDict(from_attributes=True)

class TicketValidateSchema(BaseModel):
    qr_token: str