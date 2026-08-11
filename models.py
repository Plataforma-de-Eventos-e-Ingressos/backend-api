import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from database import Base

# --- ENUMS ---
class RoleEnum(str, enum.Enum):
    ORGANIZADOR = "ORGANIZADOR"
    CLIENTE = "CLIENTE"
    PORTARIA = "PORTARIA"

class TicketStatus(str, enum.Enum):
    RESERVED = "RESERVED"
    PAID = "PAID"
    VALIDATED = "VALIDATED"
    CANCELLED = "CANCELLED"

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    events = relationship("Event", back_populates="organizer")
    tickets = relationship("Ticket", back_populates="client")


class Event(Base):
    __tablename__ = "events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organizer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    external_api_id = Column(String, nullable=True)
    title = Column(String, nullable=False)
    event_datetime = Column(DateTime, nullable=False)
    location = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    total_capacity = Column(Integer, nullable=False)

    organizer = relationship("User", back_populates="events")
    tickets = relationship("Ticket", back_populates="event")


class Ticket(Base):
    __tablename__ = "tickets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"))
    client_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    seat = Column(String, nullable=True) 
    status = Column(Enum(TicketStatus), default=TicketStatus.RESERVED)
    qr_token = Column(String, unique=True, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    event = relationship("Event", back_populates="tickets")
    client = relationship("User", back_populates="tickets")