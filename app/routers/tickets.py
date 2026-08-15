import uuid
import hashlib
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
import jwt
from jwt.exceptions import InvalidTokenError
from typing import List
from app.models.models import User, Seat
from app.core.dependencies import get_current_user
from app.core.database import get_db
from app.models.models import Event, Ticket, TicketStatus
from app.schemas.schemas import TicketCreate, TicketResponse, TicketValidateSchema
from dotenv import load_dotenv
import os

load_dotenv()


SECRET_KEY = os.getenv("SECRET_KEY", "chave_secreta_para_uso_local")
ALGORITHM = "HS256"

router = APIRouter(prefix="/tickets", tags=["tickets"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

@router.post("/reserve", response_model=List[TicketResponse], status_code=status.HTTP_201_CREATED)
def reserve_ticket(
    ticket_data: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_id = current_user.id
    event = db.query(Event).filter(Event.id == ticket_data.event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Evento não encontrado.")

    created_tickets = []

    if event.has_assigned_seats:
        if not ticket_data.seat_ids or len(ticket_data.seat_ids) == 0:
            raise HTTPException(status_code=400, detail="Este evento exige a seleção de assentos no mapa.")
        
        seats = db.query(Seat).filter(Seat.id.in_(ticket_data.seat_ids)).with_for_update().all()
        
        if len(seats) != len(ticket_data.seat_ids):
            raise HTTPException(status_code=400, detail="Um ou mais assentos são inválidos ou não existem.")
            
        for seat in seats:
            if seat.status != "available":
                raise HTTPException(status_code=409, detail=f"O assento {seat.row}{seat.number} acabou de ser reservado por outra pessoa.")
            if seat.event_id != event.id:
                raise HTTPException(status_code=400, detail=f"O assento {seat.row}{seat.number} não pertence a este evento.")
                
        for seat in seats:
            seat.status = "reserved"
            
            raw_token = f"{event.id}-{user_id}-{uuid.uuid4()}"
            qr_hash = hashlib.sha256(raw_token.encode()).hexdigest()
            
            new_ticket = Ticket(
                event_id=event.id,
                client_id=user_id,
                seat=f"{seat.row}{seat.number}",
                status=TicketStatus.RESERVED,
                qr_token=qr_hash
            )
            db.add(new_ticket)
            created_tickets.append(new_ticket)

    else:
        quantity = ticket_data.quantity or 1
        tickets_sold = db.query(Ticket).filter(
            Ticket.event_id == event.id,
            Ticket.status != TicketStatus.CANCELLED
        ).count()
        
        if tickets_sold + quantity > event.total_capacity:
            raise HTTPException(status_code=400, detail="Não há ingressos suficientes disponíveis.")

        for _ in range(quantity):
            raw_token = f"{event.id}-{user_id}-{uuid.uuid4()}"
            qr_hash = hashlib.sha256(raw_token.encode()).hexdigest()
            
            new_ticket = Ticket(
                event_id=event.id,
                client_id=user_id,
                seat=None, # Lotação geral não tem assento
                status=TicketStatus.RESERVED,
                qr_token=qr_hash
            )
            db.add(new_ticket)
            created_tickets.append(new_ticket)

    db.commit()
    for t in created_tickets:
        db.refresh(t)

    return created_tickets

@router.get("/me", response_model=List[TicketResponse])
def get_my_tickets(
    db: Session = Depends(get_db),
    current_user: uuid.UUID = Depends(get_current_user)
):
    user_id = current_user.id
    tickets = db.query(Ticket)\
        .options(joinedload(Ticket.event))\
        .filter(Ticket.client_id == user_id)\
        .all()
    
    valid_tickets = []
    for t in tickets:
        if t.event_id is not None and t.event is not None:
            valid_tickets.append(t)
        else:
            print(f"Ticket com erro encontrado (id: {t.id}), pulando da resposta.")
            
    return valid_tickets

@router.patch("/{ticket_id}/cancel", status_code=status.HTTP_200_OK)
def cancel_ticket(
    ticket_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ingresso não encontrado.")
    if ticket.client_id != current_user.id:
        raise HTTPException(status_code=403, detail="Você não tem permissão para cancelar este ingresso.")
    if ticket.status == "CANCELLED":
        raise HTTPException(status_code=400, detail="Este ingresso já está cancelado.")

    event = db.query(Event).filter(Event.id == ticket.event_id).first()
    ticket.status = "CANCELLED"
    
    if event and not event.has_assigned_seats:
        event.total_capacity += 1
    
    if event and event.has_assigned_seats and ticket.seat:
        row_letter = ticket.seat[0]
        seat_num = int(ticket.seat[1:])
        
        seat = db.query(Seat).filter(Seat.event_id == event.id, Seat.row == row_letter, Seat.number == seat_num).first()
        if seat:
            seat.status = "available"
        
    db.commit()
    db.refresh(ticket)
    
    return {"message": "Ingresso cancelado com sucesso"}

@router.post("/{ticket_id}/pay", status_code=status.HTTP_200_OK)
def simulate_payment(
    ticket_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ingresso não encontrado.")
        
    if ticket.client_id != current_user.id:
        raise HTTPException(status_code=403, detail="Você não tem permissão para pagar este ingresso.")
        
    if ticket.status == TicketStatus.PAID:
        raise HTTPException(status_code=400, detail="Este ingresso já está pago.")
        
    if ticket.status == TicketStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Não é possível pagar um ingresso cancelado.")

    if not ticket.qr_token:
        raw_token = f"{ticket.event_id}-{ticket.client_id}-{uuid.uuid4()}"
        ticket.qr_token = hashlib.sha256(raw_token.encode()).hexdigest()

    ticket.status = TicketStatus.PAID
    
    db.commit()
    db.refresh(ticket)
    
    return {
        "message": "Pagamento simulado com sucesso!",
        "ticket_id": ticket.id,
        "status": ticket.status,
        "qr_token": ticket.qr_token
    }

@router.post("/validate", status_code=status.HTTP_200_OK)
def validate_ticket(
    validation_data: TicketValidateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = db.query(Ticket).filter(Ticket.qr_token == validation_data.qr_token).first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ingresso inválido ou não encontrado.")
        
    if ticket.status == TicketStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Este ingresso foi cancelado.")
        
    if ticket.status == TicketStatus.VALIDATED:
        raise HTTPException(status_code=409, detail="Atenção: Este ingresso já foi utilizado (Dupla validação)!")
        
    if ticket.status != TicketStatus.PAID:
        raise HTTPException(status_code=400, detail="Este ingresso ainda não foi pago.")
    
    ticket.status = TicketStatus.VALIDATED
    db.commit()
    
    return {
        "message": "Ingresso válido com sucesso!",
        "event_title": ticket.event.title,
        "seat": ticket.seat or "Pista",
        "client_id": str(ticket.client_id)
    }