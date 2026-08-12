from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Event, User, RoleEnum
from schemas import EventCreate, EventResponse
from dependencies import RoleChecker
import services

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

@router.get("/tmdb/search")
def search_tmdb_movies(query: str, current_user: User = Depends(allow_organizador)):
    return services.search_movies(query)