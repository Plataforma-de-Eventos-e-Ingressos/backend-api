import uuid
import hashlib
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.schemas.schemas import TicketCreate

from app.core.database import get_db
from app.models.models import Event, Ticket, TicketStatus, RoleEnum
from app.core.dependencies import get_current_user 

router = APIRouter(prefix="/tickets", tags=["tickets"])

@router.post("/reserve", status_code=status.HTTP_201_CREATED)
def reserve_ticket(
    ticket_data: TicketCreate, # Agora usando o Pydantic para validação
    db: Session = Depends(get_db),
):
    # 1. Extração e garantia do tipo UUID
    event_id = ticket_data.event_id
    
    # Se por algum motivo ainda for uma string, forçamos a conversão para objeto UUID
    if isinstance(event_id, str):
        event_id = uuid.UUID(event_id)
        
    seat = ticket_data.seat
    client_id = uuid.uuid4() # Simulação do usuário logado (já é um objeto UUID)
    
    # 2. Busca do Evento (agora com um objeto UUID real)
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento não encontrado."
        )

    # 3. Trava de Capacidade Total
    tickets_sold = db.query(func.count(Ticket.id)).filter(Ticket.event_id == event_id).scalar()
    if tickets_sold >= event.total_capacity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Os ingressos para este evento estão esgotados."
        )

    # 4. Trava de Assento Marcado
    if seat:
        existing_seat = db.query(Ticket).filter(
            Ticket.event_id == event_id, 
            Ticket.seat == seat
        ).first()
        
        if existing_seat:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"O assento {seat} já está reservado."
            )

    # 5. Geração do QR Token
    raw_token = f"{event_id}-{client_id}-{uuid.uuid4()}"
    qr_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    # 6. Criação do Ingresso
    new_ticket = Ticket(
        event_id=event_id,
        client_id=client_id,
        seat=seat,
        status=TicketStatus.RESERVED,
        qr_token=qr_hash
    )

    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)

    return new_ticket