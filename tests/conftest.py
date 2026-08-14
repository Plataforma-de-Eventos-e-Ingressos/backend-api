import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app

from app.models.models import User, RoleEnum, Event, Ticket
from app.routers.auth import get_password_hash, create_access_token
import uuid
from datetime import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

"""Cria as tabelas antes de cada teste e destrói depois."""
@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

"""Cria um cliente de teste que substitui o banco real pelo banco em memória."""
@pytest.fixture(scope="function")
def client(db_session):
   
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c

@pytest.fixture
def test_client_user(db_session):
    user = User(
        id=uuid.uuid4(),
        email="cliente@teste.com",
        password_hash=get_password_hash("123456"),
        role=RoleEnum.CLIENTE
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_client_token(test_client_user):
    return create_access_token(data={"sub": str(test_client_user.id), "role": test_client_user.role.value})

@pytest.fixture
def test_organizer_user(db_session):
    user = User(
        id=uuid.uuid4(),
        name="Organizador Teste", 
        email="organizador@teste.com",
        password_hash=get_password_hash("123456"),
        role=RoleEnum.ORGANIZADOR
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_organizer_token(test_organizer_user):
    return create_access_token(data={"sub": str(test_organizer_user.id), "role": test_organizer_user.role.value})

@pytest.fixture
def test_event(db_session, test_organizer_user):
    event = Event(
        id=uuid.uuid4(),
        organizer_id=test_organizer_user.id,
        title="Evento de Teste",
        event_datetime=datetime(2026, 12, 31, 20, 0),
        location="Local Teste",
        price=50.0,
        total_capacity=10
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)
    return event

@pytest.fixture
def test_client_user(db_session):
    user = User(
        id=uuid.uuid4(),
        name="Cliente Teste", 
        email="cliente@teste.com",
        password_hash=get_password_hash("123456"),
        role=RoleEnum.CLIENTE
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_ticket(db_session, test_client_user, test_event):
    ticket = Ticket(
        id=uuid.uuid4(),
        client_id=test_client_user.id,
        event_id=test_event.id,
        status="PAID",
        qr_token="fake-qr-token-123"
    )
    db_session.add(ticket)
    db_session.commit()
    db_session.refresh(ticket)
    return ticket