from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.models import Event, User, RoleEnum
from app.schemas.schemas import EventCreate, EventResponse
from app.core.dependencies import RoleChecker
from app.services.services import search_movies
from uuid import UUID

router = APIRouter(prefix="/events", tags=["Events"])

allow_organizador = RoleChecker([RoleEnum.ORGANIZADOR])

@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(
    event_data: EventCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(allow_organizador)
):
    new_event = Event(
        organizer_id=current_user.id,
        **event_data.model_dump()
    )
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    return new_event

@router.get("/", response_model=List[EventResponse])
def list_events(db: Session = Depends(get_db)):
    return db.query(Event).all()

@router.get("/{id}", response_model=EventResponse)
def get_event(id: UUID, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == id).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento não encontrado."
        )
        
    return event

@router.get("/tmdb/search")
def search_tmdb_movies(query: str, current_user: User = Depends(allow_organizador)):
    return search_movies(query)