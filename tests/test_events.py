import uuid
import pytest
from datetime import datetime
from app.models.models import Event, User, RoleEnum, Ticket
from app.routers.auth import create_access_token

# --- FIXTURES DE USUÁRIOS E AUTENTICAÇÃO ---

@pytest.fixture
def org_user(db_session):
    """Cria um usuário ORGANIZADOR no banco de testes."""
    user = User(
        id=uuid.uuid4(),
        name="Organizador Teste",
        email="org@teste.com",
        password_hash="hashed_password",
        role=RoleEnum.ORGANIZADOR
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def another_org_user(db_session):
    """Cria um segundo ORGANIZADOR para testar travas de edição/deleção de terceiros."""
    user = User(
        id=uuid.uuid4(),
        name="Outro Organizador",
        email="outro@teste.com",
        password_hash="hashed_password",
        role=RoleEnum.ORGANIZADOR
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def client_user(db_session):
    """Cria um usuário CLIENTE no banco de testes."""
    user = User(
        id=uuid.uuid4(),
        name="Cliente Teste",
        email="cliente@teste.com",
        password_hash="hashed_password",
        role=RoleEnum.CLIENTE
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def org_headers(org_user):
    token = create_access_token(data={"sub": str(org_user.id), "role": org_user.role.value})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def another_org_headers(another_org_user):
    token = create_access_token(data={"sub": str(another_org_user.id), "role": another_org_user.role.value})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def client_headers(client_user):
    token = create_access_token(data={"sub": str(client_user.id), "role": client_user.role.value})
    return {"Authorization": f"Bearer {token}"}

# --- FUNÇÃO AUXILIAR ---

def create_mock_event(db_session, organizer_id):
    """Cria um evento vinculado a um organizador específico."""
    event = Event(
        id=uuid.uuid4(),
        organizer_id=organizer_id,
        title="Show de Teste",
        event_datetime=datetime(2026, 12, 31, 20, 0, 0),
        location="Teatro Central",
        total_capacity=100,
        price=50.00,
        description="Descrição incrível do show"
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)
    return event


# --- TESTES DE CRIAÇÃO (POST) ---

def test_create_event_success(client, org_headers):
    payload = {
        "title": "Festival de Inverno",
        "event_datetime": "2026-07-20T18:00:00",
        "location": "Parque da Cidade",
        "price": 120.00,
        "total_capacity": 500,
        "description": "Maior festival do ano"
    }
    response = client.post("/events/", json=payload, headers=org_headers)
    
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert "id" in data

def test_create_event_forbidden_for_client(client, client_headers):
    """Garante que um usuário com role CLIENTE receba 403 (Forbidden)."""
    payload = {
        "title": "Evento Hacker",
        "event_datetime": "2026-07-20T18:00:00",
        "location": "Internet",
        "price": 0.0,
        "total_capacity": 10
    }
    response = client.post("/events/", json=payload, headers=client_headers)
    assert response.status_code in [401, 403] # Depende de como o RoleChecker levanta o erro


# --- TESTES DE LEITURA (GET) ---

def test_list_events(client, db_session, org_user):
    create_mock_event(db_session, org_user.id)
    response = client.get("/events/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0

def test_get_event_success(client, db_session, org_user):
    event = create_mock_event(db_session, org_user.id)
    response = client.get(f"/events/{event.id}")
    assert response.status_code == 200
    assert response.json()["title"] == event.title


# --- TESTES DE ATUALIZAÇÃO (PUT) ---

def test_update_event_success(client, db_session, org_user, org_headers):
    event = create_mock_event(db_session, org_user.id)
    payload = {"price": 75.00, "title": "Show Atualizado"}
    
    response = client.put(f"/events/{event.id}", json=payload, headers=org_headers)
    assert response.status_code == 200
    assert response.json()["price"] == 75.00
    assert response.json()["title"] == "Show Atualizado"

def test_update_event_forbidden_other_org(client, db_session, org_user, another_org_headers):
    """Garante que o Organizador 2 não consegue editar o evento do Organizador 1."""
    event = create_mock_event(db_session, org_user.id)
    payload = {"title": "Hackeado!"}
    
    response = client.put(f"/events/{event.id}", json=payload, headers=another_org_headers)
    assert response.status_code == 403
    assert "próprios eventos" in response.json()["detail"]


# --- TESTES DE DELEÇÃO (DELETE) ---

def test_delete_event_success(client, db_session, org_user, org_headers):
    event = create_mock_event(db_session, org_user.id)
    
    response = client.delete(f"/events/{event.id}", headers=org_headers)
    assert response.status_code == 204
    
    # Verifica se realmente sumiu do banco
    check = client.get(f"/events/{event.id}")
    assert check.status_code == 404

def test_delete_event_with_sold_tickets(client, db_session, org_user, client_user, org_headers):
    """Garante que a trava de exclusão funciona se já houver ingressos vendidos."""
    event = create_mock_event(db_session, org_user.id)
    
    # Simula a venda de um ingresso
    ticket = Ticket(
        event_id=event.id,
        client_id=client_user.id,
        seat="A-01",
        qr_token="hash_teste_qr_code"
    )
    db_session.add(ticket)
    db_session.commit()
    
    response = client.delete(f"/events/{event.id}", headers=org_headers)
    assert response.status_code == 400
    assert "Não é possível deletar este evento" in response.json()["detail"]