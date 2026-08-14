import uuid
import pytest
from app.models.models import Event, Ticket
from datetime import datetime
from app.routers.auth import create_access_token 
from fastapi import status

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
        description="Descrição de teste",
        organizer_id=uuid.uuid4()
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

def test_get_my_tickets_empty(client, auth_headers):
    """Testa se um usuário que ainda não comprou nada recebe uma lista vazia."""
    response = client.get("/tickets/me", headers=auth_headers)
    
    assert response.status_code == 200
    assert response.json() == []

def test_get_my_tickets_success(client, db_session, auth_headers):
    """Testa se a rota retorna os ingressos com os dados do evento embutidos."""
    # 1. Cria um evento de teste
    event = create_mock_event(db_session)
    
    # 2. Faz uma compra usando o token do usuário de teste
    reserve_payload = {
        "event_id": str(event.id),
        "seat": "Camarote-01"
    }
    client.post("/tickets/reserve", json=reserve_payload, headers=auth_headers)
    
    # 3. Consulta a lista de ingressos do usuário
    response = client.get("/tickets/me", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    # Validações
    assert len(data) == 1
    ticket = data[0]
    assert ticket["seat"] == "Camarote-01"
    assert ticket["event_id"] == str(event.id)
    assert "qr_token" in ticket
    
    # Verifica o 'joinedload': Os dados do evento devem ter vindo junto!
    assert "event" in ticket
    assert ticket["event"]["title"] == "Evento Teste de Ingressos"
    assert ticket["event"]["total_capacity"] == 2

def test_get_my_tickets_unauthorized(client):
    """Testa se a rota é protegida e bloqueia acesso sem token."""
    response = client.get("/tickets/me")
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

def test_cancel_ticket_success(client, db_session, test_client_token, test_event, test_ticket):
    """
    Testa se um cliente consegue cancelar o próprio ingresso com sucesso,
    atualizando o status para CANCELLED e devolvendo a vaga para o evento.
    """
    capacity_before = test_event.total_capacity

    response = client.patch(
        f"/tickets/{test_ticket.id}/cancel",
        headers={"Authorization": f"Bearer {test_client_token}"}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message"] == "Ingresso cancelado com sucesso"

    db_session.refresh(test_ticket)
    db_session.refresh(test_event)

    assert test_ticket.status == "CANCELLED"
    assert test_event.total_capacity == capacity_before + 1

def test_cancel_ticket_forbidden_other_user(client, db_session, test_organizer_token, test_ticket):
    """
    Testa se um usuário diferente (ou organizador) é impedido de cancelar 
    um ingresso que não lhe pertence.
    """
    response = client.patch(
        f"/tickets/{test_ticket.id}/cancel",
        headers={"Authorization": f"Bearer {test_organizer_token}"}
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_simulate_payment_success(client, db_session, test_client_token, test_ticket):
    """
    Testa se o cliente consegue simular o pagamento de um ingresso reservado,
    mudando o status para PAID e gerando o QR Code.
    """
    test_ticket.status = "RESERVED"
    db_session.commit()

    response = client.post(
        f"/tickets/{test_ticket.id}/pay",
        headers={"Authorization": f"Bearer {test_client_token}"}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message"] == "Pagamento simulado com sucesso!"

    db_session.refresh(test_ticket)
    assert test_ticket.status == "PAID"
    assert test_ticket.qr_token is not None

def test_validate_ticket_success(client, db_session, test_client_token, test_ticket):
    """Testa a validação de um ingresso pago e válido (Caminho Feliz)."""
    # Prepara o cenário: Ingresso pago e com um QR Token
    test_ticket.status = "PAID"
    test_ticket.qr_token = "hash_valido_123"
    db_session.commit()

    response = client.post(
        "/tickets/validate",
        headers={"Authorization": f"Bearer {test_client_token}"},
        json={"qr_token": "hash_valido_123"}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message"] == "Ingresso válido com sucesso!"
    
    db_session.refresh(test_ticket)
    assert test_ticket.status == "VALIDATED"


def test_validate_ticket_not_found(client, test_client_token):
    """Testa a tentativa de validar um QR Code que não existe."""
    response = client.post(
        "/tickets/validate",
        headers={"Authorization": f"Bearer {test_client_token}"},
        json={"qr_token": "token_inventado_ou_errado"}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Ingresso inválido ou não encontrado."


def test_validate_ticket_already_used(client, db_session, test_client_token, test_ticket):
    """Testa a tentativa de dupla validação (ingresso já utilizado)."""
    test_ticket.status = "VALIDATED" # Já passou pela portaria
    test_ticket.qr_token = "hash_valido_123"
    db_session.commit()

    response = client.post(
        "/tickets/validate",
        headers={"Authorization": f"Bearer {test_client_token}"},
        json={"qr_token": "hash_valido_123"}
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert "já foi utilizado" in response.json()["detail"]


def test_validate_ticket_unpaid(client, db_session, test_client_token, test_ticket):
    """Testa a tentativa de validar um ingresso apenas reservado (não pago)."""
    test_ticket.status = "RESERVED"
    test_ticket.qr_token = "hash_valido_123"
    db_session.commit()

    response = client.post(
        "/tickets/validate",
        headers={"Authorization": f"Bearer {test_client_token}"},
        json={"qr_token": "hash_valido_123"}
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "ainda não foi pago" in response.json()["detail"]


def test_validate_ticket_cancelled(client, db_session, test_client_token, test_ticket):
    """Testa a tentativa de validar um ingresso que foi cancelado."""
    test_ticket.status = "CANCELLED"
    test_ticket.qr_token = "hash_valido_123"
    db_session.commit()

    response = client.post(
        "/tickets/validate",
        headers={"Authorization": f"Bearer {test_client_token}"},
        json={"qr_token": "hash_valido_123"}
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "foi cancelado" in response.json()["detail"]