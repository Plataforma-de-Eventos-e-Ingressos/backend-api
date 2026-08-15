from app.core.database import SessionLocal
from app.models.models import User, Event, RoleEnum
import bcrypt
from datetime import datetime, timedelta, timezone

def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password=pwd_bytes, salt=salt)
    return hashed_password.decode('utf-8')

def run_seed():
    db = SessionLocal()

    try:
        if db.query(User).first():
            return
        
        organizer = User(
            name="Organizador",
            email="organizador@email.com",
            password_hash=get_password_hash("admin"),
            role=RoleEnum.ORGANIZADOR
        )

        client1 = User(
            name="Cliente 1",
            email="cliente@email.com",
            password_hash=get_password_hash("admin"),
            role=RoleEnum.CLIENTE
        )

        client2 = User(
            name="Cliente 2",
            email="cliente2@email.com",
            password_hash=get_password_hash("admin"),
            role=RoleEnum.CLIENTE
        )

        administrative = User(
            name="Portaria",
            email="portaria@email.com",
            password_hash=get_password_hash("admin"),
            role=RoleEnum.PORTARIA
        )

        db.add_all([organizer, client1, client2, administrative])
        db.commit()

        db.refresh(organizer) 

        event = Event(
            organizer_id=organizer.id,
            title="Evento de Teste",
            event_datetime=datetime.now(timezone.utc) + timedelta(days=30),
            location="Local de Teste",
            price=100.0,
            total_capacity=100
        )   

        db.add(event)
        db.commit()
        print("Seed concluído")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_seed()
