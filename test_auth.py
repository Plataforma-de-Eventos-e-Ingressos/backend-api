"""Testa se a API cria um usuário com sucesso e retorna 201."""
def test_register_user_success(client):
    payload = {
        "name": "Cliente Teste",
        "email": "teste@email.com",
        "password": "senha_super_segura"
    }
    
    response = client.post("/auth/register", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Cliente Teste"
    assert data["email"] == "teste@email.com"
    assert data["role"] == "CLIENTE"
    assert "password" not in data 

"""Testa se a API bloqueia o cadastro de e-mails duplicados."""
def test_register_duplicate_email(client):
    payload = {
        "name": "Cliente Teste",
        "email": "teste@email.com",
        "password": "senha"
    }
    
    client.post("/auth/register", json=payload)
    
    response2 = client.post("/auth/register", json=payload)
    
    assert response2.status_code == 400
    assert response2.json()["detail"] == "Este e-mail já está cadastrado em nossa base."