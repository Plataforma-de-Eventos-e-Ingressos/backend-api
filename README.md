# ⚙️ Backend API - Plataforma de Eventos & Ingressos

Este repositório contém a **API RESTful** da plataforma de eventos e ingressos desenvolvida para o desafio técnico **Elite Dev**, da **Verzel**.

Construída com **Python e FastAPI**, esta aplicação foca em performance, tipagem rigorosa, arquitetura limpa e na resolução do problema de concorrência na venda de ingressos (*Double Booking*).

---

## 🌟 Destaques da Solução

### 🔒 Prevenção de Venda Duplicada (*Double Booking*)

Utilização de **Row-Level Locks** (`with_for_update` / `SELECT FOR UPDATE`) no PostgreSQL para garantir que transações concorrentes aguardem a liberação da linha.

Caso o assento já esteja reservado, a API retorna **`409 Conflict`**.

### 🌐 Integração com API Externa

Integração com a API do **TMDb** para busca e autocompletar informações relacionadas a eventos, filmes e shows.

### 🛡️ Segurança e QR Code

Geração de tokens de ingresso criptografados utilizando **JWT**, protegendo os ingressos contra falsificação e permitindo sua validação na portaria.

### 💺 Matemática de Assentos Blindada

O Back-end não confia no payload enviado pelo Front-end para calcular a capacidade de eventos com assentos marcados.

A capacidade é automaticamente calculada a partir de:

```text
linhas × cadeiras
```

Esse cálculo é realizado no Back-end no momento da criação do evento, evitando manipulações da capacidade através de requisições modificadas.

---

## 🛠️ Tecnologias Utilizadas

| Tecnologia       | Utilização                            |
| ---------------- | ------------------------------------- |
| **Python 3.10+** | Linguagem principal                   |
| **FastAPI**      | Framework para construção da API REST |
| **Uvicorn**      | Servidor ASGI                         |
| **SQLAlchemy**   | ORM para modelagem e acesso ao banco  |
| **PostgreSQL**   | Banco de dados relacional             |
| **Alembic**      | Gerenciamento de migrações do banco   |
| **Pytest**       | Suíte de testes automatizados         |

---

## 🚀 Como Executar Localmente

> 💡 **Dica:** Para executar todo o ecossistema com Docker, consulte o repositório central **[docs-e-infra](link-do-repo-infra)**.

Caso deseje executar a API de forma isolada para desenvolvimento:

### 1. Clone o repositório

```bash
git clone https://github.com/SuaOrganizacao/backend-api.git
cd backend-api
```

### 2. Crie e ative o ambiente virtual

#### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

#### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/verzel_events
SECRET_KEY=sua_chave_secreta_jwt_super_segura
API_EXTERNAL_KEY=sua_chave_da_api_do_tmdb
```

> **Importante:** substitua os valores de exemplo pelas credenciais reais do ambiente de desenvolvimento.

### 5. Execute as migrações do banco de dados

Com o PostgreSQL em execução, execute:

```bash
alembic upgrade head
```

Esse comando aplica todas as migrações existentes e cria a estrutura necessária para a aplicação.

### 6. Inicie a API

```bash
uvicorn main:app --reload
```

A API estará disponível em:

```text
http://localhost:8000
```

---

## 🧪 Dados de Teste (Seed)

Para facilitar a avaliação, o projeto inclui um script que popula o banco de dados com os cenários necessários, incluindo:

* Organizador;
* Clientes;
* Portaria;
* Evento ativo;
* Dados necessários para testar o fluxo de compra.

Com o banco de dados configurado, execute:

```bash
python seed.py
```

### Credenciais

| Perfil      | E-mail                  | Senha   | Papel no Sistema                                  |
| ----------- | ----------------------- | ------- | ------------------------------------------------- |
| Organizador | `organizador@email.com` | `admin` | Gestão e criação de eventos                       |
| Cliente     | `cliente@email.com`     | `admin` | Compra de ingressos                               |
| Portaria    | `portaria@email.com`    | `admin` | Validação de QR Codes na entrada                  |

---

## 🚦 Testes Automatizados

Para garantir a confiabilidade das regras de negócio, o projeto conta com uma suíte de testes automatizados utilizando **Pytest**.

Para executar todos os testes:

```bash
pytest -v
```

Os testes cobrem cenários críticos, incluindo:

* Prevenção de venda duplicada de assentos;
* Retorno de **`409 Conflict`** quando o mesmo assento já está reservado;
* Concorrência entre diferentes clientes tentando adquirir o mesmo assento;
* Cancelamento de ingressos;
* Devolução de ingressos ao estoque;
* Restrições para exclusão de eventos que já possuem ingressos vendidos;
* Retorno de **`400 Bad Request`** em operações que violam as regras de negócio.

### Teste de concorrência

Um dos cenários principais é:

```text
test_reserve_already_booked_seat_fails
```

Esse teste garante que uma tentativa de reservar um assento já ocupado seja rejeitada corretamente, evitando o problema de **Double Booking**.

---

## 📖 Documentação Interativa da API

A API possui documentação automática gerada pelo **FastAPI**.

Com o servidor em execução:

```bash
uvicorn main:app --reload
```

acesse:

### Swagger UI

```text
http://localhost:8000/docs
```

### ReDoc

```text
http://localhost:8000/redoc
```

A documentação permite visualizar os endpoints, modelos de requisição e resposta e testar as operações diretamente pelo navegador.

---

## 👨‍💻 Desenvolvedor

Desenvolvido por **Robson do Amaral Diógenes**.
