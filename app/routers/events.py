from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.models.models import Event, User, RoleEnum, Ticket # Adicionado Ticket
from app.schemas.schemas import EventCreate, EventUpdate, EventResponse # Adicionado EventUpdate
from app.core.dependencies import RoleChecker
from app.services.services import search_movies

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
    
    # Trava: Só o dono do evento pode editá-lo
    if event.organizer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode editar os seus próprios eventos."
        )

    # Atualiza apenas os campos enviados (ignora os nulos)
    update_data = event_data.model_dump(exclude_unset=True)
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

    tickets_sold = db.query(func.count(Ticket.id)).filter(Ticket.event_id == id).scalar()
    if tickets_sold > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Não é possível deletar este evento pois já existem ingressos reservados/vendidos."
        )

    db.delete(event)
    db.commit()
    return None

@router.get("/tmdb/search")
def search_tmdb_movies(query: str, current_user: User = Depends(allow_organizador)):
    return search_movies(query)