import pytest

def test_create_event_generates_seats(client, test_organizer_token):
    """Testa se a criação de um evento com lugar marcado gera os assentos corretamente."""
    org_headers = {"Authorization": f"Bearer {test_organizer_token}"}
    
    payload = {
        "title": "Especial de Comédia",
        "event_datetime": "2026-10-10T20:00:00",
        "location": "Teatro Central",
        "price": 80.00,
        "total_capacity": 6,          
        "description": "Teste",      
        "has_assigned_seats": True,
        "rows_count": 2,
        "seats_per_row": 3
    }
    
    response = client.post("/events/", json=payload, headers=org_headers)
    assert response.status_code == 201
    event_id = response.json()["id"]

    seats_response = client.get(f"/events/{event_id}/seats")
    assert seats_response.status_code == 200
    
    seats = seats_response.json()
    assert len(seats) == 6
    
    b3 = next((s for s in seats if s["row"] == "B" and s["number"] == 3), None)
    assert b3 is not None
    assert b3["status"] == "available"

def test_reserve_assigned_seats_success(client, test_organizer_token, test_client_token):
    """Testa a compra simultânea de múltiplos assentos."""
    org_headers = {"Authorization": f"Bearer {test_organizer_token}"}
    client_headers = {"Authorization": f"Bearer {test_client_token}"}
    
    event_payload = {
        "title": "Show VIP",
        "event_datetime": "2026-11-15T21:00:00",
        "location": "Casa de Shows",
        "price": 150.00,
        "total_capacity": 10,  
        "description": "Teste", 
        "has_assigned_seats": True,
        "rows_count": 2,
        "seats_per_row": 5
    }
    ev_res = client.post("/events/", json=event_payload, headers=org_headers)
    assert ev_res.status_code == 201
    event_id = ev_res.json()["id"]

    seats = client.get(f"/events/{event_id}/seats").json()
    seat_a1 = next(s for s in seats if s["row"] == "A" and s["number"] == 1)
    seat_b2 = next(s for s in seats if s["row"] == "B" and s["number"] == 2)

    reserve_payload = {
        "event_id": event_id,
        "seat_ids": [seat_a1["id"], seat_b2["id"]]
    }
    res_response = client.post("/tickets/reserve", json=reserve_payload, headers=client_headers)
    
    assert res_response.status_code == 201
    tickets = res_response.json()
    assert len(tickets) == 2
    
    updated_seats = client.get(f"/events/{event_id}/seats").json()
    up_a1 = next(s for s in updated_seats if s["id"] == seat_a1["id"])
    assert up_a1["status"] == "reserved"


def test_reserve_already_booked_seat_fails(client, test_organizer_token, test_client_token):
    """Garante que a trava do banco funciona: ninguém pode comprar um assento ocupado."""
    org_headers = {"Authorization": f"Bearer {test_organizer_token}"}
    client_headers = {"Authorization": f"Bearer {test_client_token}"}

    ev_res = client.post("/events/", json={
        "title": "Show Disputado",
        "event_datetime": "2026-12-01T20:00:00",
        "location": "Arena",
        "price": 200.00,
        "total_capacity": 2,   
        "description": "Teste", 
        "has_assigned_seats": True,
        "rows_count": 1,
        "seats_per_row": 2
    }, headers=org_headers)
    assert ev_res.status_code == 201
    event_id = ev_res.json()["id"]
    
    seats = client.get(f"/events/{event_id}/seats").json()
    seat_a1_id = next(s["id"] for s in seats if s["row"] == "A" and s["number"] == 1)

    client.post(
        "/tickets/reserve", 
        json={"event_id": event_id, "seat_ids": [seat_a1_id]}, 
        headers=client_headers
    )

    fail_response = client.post(
        "/tickets/reserve", 
        json={"event_id": event_id, "seat_ids": [seat_a1_id]}, 
        headers=client_headers 
    )
    
    assert fail_response.status_code == 409
    assert "reservado" in fail_response.json()["detail"].lower()

def test_cancel_ticket_frees_seat(client, test_organizer_token, test_client_token):
    """Testa se o cancelamento de um ingresso devolve a cadeira para o mapa."""
    org_headers = {"Authorization": f"Bearer {test_organizer_token}"}
    client_headers = {"Authorization": f"Bearer {test_client_token}"}

    ev_res = client.post("/events/", json={
        "title": "Show com Cancelamento",
        "event_datetime": "2026-10-10T20:00:00",
        "location": "Teatro",
        "price": 50.00,
        "total_capacity": 1,    
        "description": "Teste", 
        "has_assigned_seats": True,
        "rows_count": 1,
        "seats_per_row": 1
    }, headers=org_headers)
    assert ev_res.status_code == 201
    event_id = ev_res.json()["id"]
    
    seats = client.get(f"/events/{event_id}/seats").json()
    seat_a1_id = seats[0]["id"]
    
    buy_res = client.post(
        "/tickets/reserve", 
        json={"event_id": event_id, "seat_ids": [seat_a1_id]}, 
        headers=client_headers
    )
    ticket_id = buy_res.json()[0]["id"]

    cancel_res = client.patch(f"/tickets/{ticket_id}/cancel", headers=client_headers)
    assert cancel_res.status_code == 200

    updated_seats = client.get(f"/events/{event_id}/seats").json()
    assert updated_seats[0]["status"] == "available"