from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from uuid import UUID
import string
from app.core.database import get_db
from app.models.models import Event, User, RoleEnum, Ticket, TicketStatus, Seat
from app.schemas.schemas import EventCreate, EventUpdate, EventResponse 
from app.core.dependencies import RoleChecker
from app.services.services import search_movies

router = APIRouter(prefix="/events", tags=["Events"])

allow_organizador = RoleChecker([RoleEnum.ORGANIZADOR])

def generate_seats_for_event(db: Session, event_id: UUID, rows_count: int, seats_per_row: int):
    alphabet = string.ascii_uppercase # A, B, C...
    
    rows_count = min(rows_count, len(alphabet)) 
    
    for r in range(rows_count):
        row_letter = alphabet[r]
        for seat_num in range(1, seats_per_row + 1):
            db_seat = Seat(
                event_id=event_id,
                row=row_letter,
                number=seat_num,
                status="available"
            )
            db.add(db_seat)
    db.commit()

@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(
    event_data: EventCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(allow_organizador)
):
    event_dict = event_data.model_dump()
    
    rows_count = event_dict.pop("rows_count", None)
    seats_per_row = event_dict.pop("seats_per_row", None)

    if event_dict.get("has_assigned_seats") and rows_count and seats_per_row:
        event_dict["total_capacity"] = rows_count * seats_per_row

    new_event = Event(
        organizer_id=current_user.id,
        **event_dict
    )
    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    if new_event.has_assigned_seats and rows_count and seats_per_row:
        generate_seats_for_event(db, new_event.id, rows_count, seats_per_row)

    return new_event

@router.get("/", response_model=List[EventResponse])
def list_events(
    search: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    query = db.query(Event)
    
    if search:
        query = query.filter(Event.title.ilike(f"%{search}%"))
        
    return query.all()

@router.get("/{id}", response_model=EventResponse)
def get_event(id: UUID, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == id).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento não encontrado."
        )
        
    return event

@router.put("/{id}", response_model=EventResponse)
def update_event(
    id: UUID,
    event_data: EventUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_organizador)
):
    event = db.query(Event).filter(Event.id == id).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento não encontrado."
        )
    
    if event.organizer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode editar os seus próprios eventos."
        )

    update_data = event_data.model_dump(exclude_unset=True)
    update_data.pop("rows_count", None)
    update_data.pop("seats_per_row", None)
    
    for key, value in update_data.items():
        setattr(event, key, value)

    db.commit()
    db.refresh(event)
    return event

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_organizador)
):
    event = db.query(Event).filter(Event.id == id).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento não encontrado."
        )
    
    if event.organizer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode deletar os seus próprios eventos."
        )

    tickets_sold = db.query(Ticket).filter(
        Ticket.event_id == id,
        Ticket.status != TicketStatus.CANCELLED
    ).count() 

    if tickets_sold > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Não é possível deletar este evento pois ainda existem ingressos ativos."
        )

    db.delete(event)
    db.commit()
    return None

@router.get("/tmdb/search")
def search_tmdb_movies(query: str, current_user: User = Depends(allow_organizador)):
    return search_movies(query)

@router.get("/{event_id}/seats")
def get_event_seats(event_id: UUID, db: Session = Depends(get_db)):
    seats = db.query(Seat).filter(Seat.event_id == event_id).all()
    if not seats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhum assento encontrado para este evento ou evento inválido."
        )
    return seats