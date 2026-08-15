import uuid
import pytest
from app.models.models import Event, Ticket, TicketStatus
from datetime import datetime
from fastapi import status

# --- FUNÇÃO AUXILIAR ---

def create_mock_general_event(db_session, organizer_id, capacity=2):
    """Cria um evento de Lotação Geral (pista) no banco em memória."""
    event = Event(
        id=uuid.uuid4(),
        title="Evento Teste de Ingressos (Pista)",
        event_datetime=datetime(2026, 12, 31, 20, 0, 0),
        location="Teatro Teste",
        total_capacity=capacity, 
        price=100.00,
        description="Descrição de teste",
        organizer_id=organizer_id,
        has_assigned_seats=False # Explicitamente sem lugar marcado
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)
    return event


# --- TESTES DE RESERVA (LOTAÇÃO GERAL) ---

def test_reserve_ticket_success(client, db_session, test_client_token, test_organizer_user):
    """Testa se a reserva de um ingresso livre ocorre com sucesso."""
    event = create_mock_general_event(db_session, test_organizer_user.id)
    
    payload = {
        "event_id": str(event.id),
        "quantity": 1
    }
    
    response = client.post("/tickets/reserve", json=payload, headers={"Authorization": f"Bearer {test_client_token}"})
    
    assert response.status_code == 201
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    
    ticket = data[0]
    assert ticket["event_id"] == str(event.id)
    assert ticket["seat"] is None
    assert "qr_token" in ticket
    assert ticket["status"] == "RESERVED"

def test_reserve_ticket_sold_out(client, db_session, test_client_token, test_organizer_user):
    """Testa a trava de capacidade máxima do evento (Erro 400)."""
    event = create_mock_general_event(db_session, test_organizer_user.id, capacity=1)
    
    # Cliente compra o único ingresso disponível
    client.post("/tickets/reserve", json={"event_id": str(event.id), "quantity": 1}, headers={"Authorization": f"Bearer {test_client_token}"})
    
    # Tenta comprar mais um ingresso e deve falhar
    response = client.post("/tickets/reserve", json={"event_id": str(event.id), "quantity": 1}, headers={"Authorization": f"Bearer {test_client_token}"})
    
    assert response.status_code == 400
    assert "Não há ingressos suficientes" in response.json()["detail"]

def test_reserve_ticket_event_not_found(client, test_client_token):
    """Testa tentativa de reserva em um evento que não existe (Erro 404)."""
    payload = {
        "event_id": str(uuid.uuid4()),
        "quantity": 1
    }
    
    response = client.post("/tickets/reserve", json=payload, headers={"Authorization": f"Bearer {test_client_token}"})
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Evento não encontrado."


# --- TESTES DE LISTAGEM ---

def test_get_my_tickets_empty(client, test_client_token):
    """Testa se um usuário que ainda não comprou nada recebe uma lista vazia."""
    response = client.get("/tickets/me", headers={"Authorization": f"Bearer {test_client_token}"})
    
    assert response.status_code == 200
    assert response.json() == []

def test_get_my_tickets_success(client, db_session, test_client_token, test_organizer_user):
    """Testa se a rota retorna os ingressos com os dados do evento embutidos."""
    event = create_mock_general_event(db_session, test_organizer_user.id)
    
    client.post("/tickets/reserve", json={"event_id": str(event.id), "quantity": 1}, headers={"Authorization": f"Bearer {test_client_token}"})
    
    response = client.get("/tickets/me", headers={"Authorization": f"Bearer {test_client_token}"})
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) == 1
    ticket = data[0]
    assert ticket["event_id"] == str(event.id)
    assert "qr_token" in ticket
    assert "event" in ticket
    assert ticket["event"]["title"] == "Evento Teste de Ingressos (Pista)"

def test_get_my_tickets_unauthorized(client):
    """Testa se a rota é protegida e bloqueia acesso sem token."""
    response = client.get("/tickets/me")
    assert response.status_code == 401


# --- TESTES DE CANCELAMENTO, PAGAMENTO E VALIDAÇÃO ---
# (Usando os fixtures do conftest.py)

def test_cancel_ticket_success(client, db_session, test_client_token, test_event, test_ticket):
    capacity_before = test_event.total_capacity

    response = client.patch(
        f"/tickets/{test_ticket.id}/cancel",
        headers={"Authorization": f"Bearer {test_client_token}"}
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Ingresso cancelado com sucesso"

    db_session.refresh(test_ticket)
    db_session.refresh(test_event)

    assert test_ticket.status == "CANCELLED"
    assert test_event.total_capacity == capacity_before + 1

def test_cancel_ticket_forbidden_other_user(client, test_organizer_token, test_ticket):
    response = client.patch(
        f"/tickets/{test_ticket.id}/cancel",
        headers={"Authorization": f"Bearer {test_organizer_token}"}
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_simulate_payment_success(client, db_session, test_client_token, test_ticket):
    test_ticket.status = "RESERVED"
    db_session.commit()

    response = client.post(
        f"/tickets/{test_ticket.id}/pay",
        headers={"Authorization": f"Bearer {test_client_token}"}
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Pagamento simulado com sucesso!"

    db_session.refresh(test_ticket)
    assert test_ticket.status == "PAID"
    assert test_ticket.qr_token is not None


def test_validate_ticket_success(client, db_session, test_client_token, test_ticket):
    test_ticket.status = "PAID"
    test_ticket.qr_token = "hash_valido_123"
    db_session.commit()

    response = client.post(
        "/tickets/validate",
        headers={"Authorization": f"Bearer {test_client_token}"},
        json={"qr_token": "hash_valido_123"}
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Ingresso válido com sucesso!"
    
    db_session.refresh(test_ticket)
    assert test_ticket.status == "VALIDATED"


def test_validate_ticket_not_found(client, test_client_token):
    response = client.post(
        "/tickets/validate",
        headers={"Authorization": f"Bearer {test_client_token}"},
        json={"qr_token": "token_inventado_ou_errado"}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_validate_ticket_already_used(client, db_session, test_client_token, test_ticket):
    test_ticket.status = "VALIDATED"
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
    test_ticket.status = "RESERVED"
    test_ticket.qr_token = "hash_valido_123"
    db_session.commit()

    response = client.post(
        "/tickets/validate",
        headers={"Authorization": f"Bearer {test_client_token}"},
        json={"qr_token": "hash_valido_123"}
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_validate_ticket_cancelled(client, db_session, test_client_token, test_ticket):
    test_ticket.status = "CANCELLED"
    test_ticket.qr_token = "hash_valido_123"
    db_session.commit()

    response = client.post(
        "/tickets/validate",
        headers={"Authorization": f"Bearer {test_client_token}"},
        json={"qr_token": "hash_valido_123"}
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST