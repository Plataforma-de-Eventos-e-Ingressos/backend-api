# ⚙️ Backend API - Elite Tickets

Este repositório contém a API RESTful desenvolvida para a plataforma de eventos e ingressos, parte do desafio técnico **Elite Dev** da **Verzel**.

A API é construída com **Python e FastAPI**, focada em alta performance, tipagem estática e documentação automatizada. Ela gerencia as regras de negócios centrais, como a prevenção de venda duplicada de assentos, a comunicação com a API externa (TMDb/Ticketmaster) e a geração de QR Codes seguros (JWT) para os ingressos.

## 🛠️ Tecnologias Utilizadas

* **Framework:** [FastAPI](https://fastapi.tiangolo.com/)
* **Servidor ASGI:** Uvicorn
* **ORM & Banco de Dados:** SQLAlchemy + PostgreSQL
* **Validação de Dados:** Pydantic

---

## 🚀 Como Executar Localmente (Sem Docker)

*(Para rodar o ecossistema completo com Docker, consulte o repositório de infraestrutura).*

**1. Pré-requisitos:**
* Python 3.10 ou superior.
* Instância do PostgreSQL rodando localmente (ou via Docker).

**2. Passo a Passo:**
Clone o repositório e acesse a pasta:
```bash
git clone https://github.com/Plataforma-de-Eventos-e-Ingressos/backend-api
cd backend-api

```

Crie e ative o ambiente virtual:

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / Mac
python -m venv venv
source venv/bin/activate

```

Instale as dependências:

```bash
pip install -r requirements.txt

```

Inicie o servidor de desenvolvimento:

```bash
uvicorn main:app --reload

```

A API estará disponível em `http://localhost:8000`.

---

## 📖 Documentação da API (Swagger)

O FastAPI gera a documentação interativa automaticamente. Com o servidor rodando, acesse:

* **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

## 🗄️ Estrutura do Banco de Dados

O modelo relacional pode ser visualizado no seguinte [LINK](https://github.com/Plataforma-de-Eventos-e-Ingressos/docs-and-infra/blob/main/documents/data-model.md).


## ⚙️ Variáveis de Ambiente (.env)

Crie um arquivo `.env` na raiz do projeto com base no seguinte modelo:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/verzel_events
SECRET_KEY=sua_chave_secreta_jwt
API_EXTERNAL_KEY=sua_chave_tmdb_ou_ticketmaster
