import uuid
import pytest
from app.models.models import Event, Ticket
from datetime import datetime
from app.routers.auth import create_access_token  # Importa sua função geradora de token

@pytest.fixture
def auth_headers():
    """Gera um token JWT válido simulando um usuário logado para os testes."""
    fake_user_id = str(uuid.uuid4())
    token = create_access_token(data={"sub": fake_user_id, "role": "CLIENTE"})
    return {"Authorization": f"Bearer {token}"}

def create_mock_event(db_session, capacity=2):
    """Cria um evento no banco em memória para os testes rodarem em cima."""
    event = Event(
        id=uuid.uuid4(),
        title="Evento Teste de Ingressos",
        event_datetime=datetime(2026, 12, 31, 20, 0, 0),
        location="Teatro Teste",
        total_capacity=capacity, 
        price=100.00,
        description="Descrição de teste"
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)
    return event


def test_reserve_ticket_success(client, db_session, auth_headers):
    """Testa se a reserva de um assento livre ocorre com sucesso."""
    event = create_mock_event(db_session)
    
    payload = {
        "event_id": str(event.id),
        "seat": "A-01"
    }
    
    response = client.post("/tickets/reserve", json=payload, headers=auth_headers)
    
    assert response.status_code == 201
    data = response.json()
    assert data["event_id"] == str(event.id)
    assert data["seat"] == "A-01"
    assert "qr_token" in data
    assert data["status"] == "RESERVED"

def test_reserve_ticket_double_booking(client, db_session, auth_headers):
    """Testa a trava de assento já reservado (Conflito 409)."""
    event = create_mock_event(db_session)
    
    payload = {
        "event_id": str(event.id),
        "seat": "B-15"
    }
    
    client.post("/tickets/reserve", json=payload, headers=auth_headers)
    
    response = client.post("/tickets/reserve", json=payload, headers=auth_headers)
    
    assert response.status_code == 409
    assert response.json()["detail"] == "O assento B-15 já está reservado."

def test_reserve_ticket_sold_out(client, db_session, auth_headers):
    """Testa a trava de capacidade máxima do evento (Erro 400)."""
    event = create_mock_event(db_session, capacity=1)
    
    payload_1 = {"event_id": str(event.id), "seat": "A-01"}
    payload_2 = {"event_id": str(event.id), "seat": "A-02"}
    
    client.post("/tickets/reserve", json=payload_1, headers=auth_headers)
    
    response = client.post("/tickets/reserve", json=payload_2, headers=auth_headers)
    
    assert response.status_code == 400
    assert response.json()["detail"] == "Os ingressos para este evento estão esgotados."

def test_reserve_ticket_event_not_found(client, auth_headers):
    """Testa tentativa de reserva em um evento que não existe (Erro 404)."""
    payload = {
        "event_id": str(uuid.uuid4()),
        "seat": "C-10"
    }
    
    response = client.post("/tickets/reserve", json=payload, headers=auth_headers)
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Evento não encontrado."