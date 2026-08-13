import uuid
import hashlib
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import func
import jwt
from jwt.exceptions import InvalidTokenError

from app.core.database import get_db
from app.models.models import Event, Ticket, TicketStatus
from app.schemas.schemas import TicketCreate
from dotenv import load_dotenv
import os

load_dotenv()


SECRET_KEY = os.getenv("SECRET_KEY", "chave_secreta_para_uso_local")
ALGORITHM = "HS256"

router = APIRouter(prefix="/tickets", tags=["tickets"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_current_user_id(token: str = Depends(oauth2_scheme)):
    """Decodifica o token JWT enviado pelo React e retorna o ID do usuário logado"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")
        return uuid.UUID(user_id)
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido ou expirado")


@router.post("/reserve", status_code=status.HTTP_201_CREATED)
def reserve_ticket(
    ticket_data: TicketCreate,
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id)
):
    event_id = ticket_data.event_id
    if isinstance(event_id, str):
        event_id = uuid.UUID(event_id)
        
    seat = ticket_data.seat
    
    client_id = user_id 

    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Evento não encontrado.")

    tickets_sold = db.query(func.count(Ticket.id)).filter(Ticket.event_id == event_id).scalar()
    if tickets_sold >= event.total_capacity:
        raise HTTPException(status_code=400, detail="Os ingressos para este evento estão esgotados.")

    if seat:
        existing_seat = db.query(Ticket).filter(Ticket.event_id == event_id, Ticket.seat == seat).first()
        if existing_seat:
            raise HTTPException(status_code=409, detail=f"O assento {seat} já está reservado.")

    raw_token = f"{event_id}-{client_id}-{uuid.uuid4()}"
    qr_hash = hashlib.sha256(raw_token.encode()).hexdigest()

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