from database import SessionLocal
from models import User, Event, Ticket
from passlib.context import CryptContext
from datetime import datetime, timedelta

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def run_seed():
    db = SessionLocal()

    try:
        if db.query(User).first():
            return
        
        organizer = User(
            name = "Organizer User",
            email = "organizador@email.com",
            password_hash = get_password_hash("admin"),
            role = RoleEnum.ORGANIZADOR
        )

        client = User(
            name="Cliente",
            email="cliente@email.com",
            password_hash=get_password_hash("admin"),
            role = RoleEnum.CLIENTE
        )

        administrative = User(
            name="Portaria",
            email="portaria@email.com",
            password_hash=get_password_hash("admin"),
            role = RoleEnum.PORTARIA
        )

        db.add_all([organizer, client, administrative])
        db.commit()

        db.refresh(organizer) 

        event = Event(
            organizer_id=organizer.id,
            title="Evento de Teste",
            event_datetime=datetime.utcnow() + timedelta(days=30),
            location="Local de Teste",
            price=100.0,
            total_tickets=100
        )   

        db.add(event)
        db.commit()

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()