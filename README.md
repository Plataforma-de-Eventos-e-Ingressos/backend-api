# ⚙️ Backend API - Elite Tickets

Este repositório contém a **API RESTful** da plataforma de eventos e ingressos desenvolvida para o desafio técnico **Elite Dev**, da **Verzel**.

A aplicação foi construída utilizando **Python e FastAPI**, com foco em performance, tipagem, organização arquitetural e documentação automatizada.

A API concentra as principais regras de negócio da plataforma, incluindo:

* 🎟️ Gerenciamento de eventos e ingressos;
* 👤 Autenticação e autorização de usuários;
* 💺 Controle de disponibilidade e reserva de ingressos;
* 🔒 Prevenção de venda duplicada de assentos;
* 🌐 Integração com APIs externas, como **TMDb/Ticketmaster**;
* 📱 Geração e validação de QR Codes seguros;
* 🔐 Utilização de **JWT** para autenticação e segurança dos ingressos;
* 🗄️ Persistência dos dados em PostgreSQL.

---

## 🛠️ Tecnologias Utilizadas

| Tecnologia       | Utilização                             |
| :--------------- | :------------------------------------- |
| **Python 3.10+** | Linguagem principal                    |
| **FastAPI**      | Framework para construção da API REST  |
| **Uvicorn**      | Servidor ASGI                          |
| **SQLAlchemy**   | ORM para acesso ao banco de dados      |
| **PostgreSQL**   | Banco de dados relacional              |
| **Pydantic**     | Validação e serialização de dados      |
| **Alembic**      | Gerenciamento de migrações do banco    |
| **JWT**          | Autenticação e segurança dos ingressos |

---

## 🚀 Como Executar Localmente

> Para executar todo o ecossistema utilizando Docker, consulte o repositório de **Infraestrutura e Documentação**.

### 📋 Pré-requisitos

Antes de iniciar, certifique-se de possuir:

* **Python 3.10 ou superior**;
* **PostgreSQL** em execução localmente ou através do Docker;
* **Git** instalado;
* Uma chave de API para os serviços externos utilizados pelo projeto.

---

### 1. Clone o repositório

```bash
git clone https://github.com/Plataforma-de-Eventos-e-Ingressos/backend-api.git
cd backend-api
```

---

### 2. Crie o ambiente virtual

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

Após a ativação, o terminal deverá indicar que o ambiente virtual está ativo.

---

### 3. Instale as dependências

Com o ambiente virtual ativado:

```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuração das Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto.

Utilize o seguinte modelo:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/verzel_events
SECRET_KEY=sua_chave_secreta_jwt
API_EXTERNAL_KEY=sua_chave_tmdb_ou_ticketmaster
```

### Variáveis disponíveis

| Variável           | Descrição                                         |
| :----------------- | :------------------------------------------------ |
| `DATABASE_URL`     | URL de conexão com o PostgreSQL                   |
| `SECRET_KEY`       | Chave utilizada para assinatura dos tokens JWT    |
| `API_EXTERNAL_KEY` | Chave de autenticação utilizada nas APIs externas |

> ⚠️ **Importante:** nunca versione o arquivo `.env` ou exponha chaves e credenciais reais no repositório.

Recomenda-se adicionar o arquivo ao `.gitignore`:

```gitignore
.env
venv/
__pycache__/
```

---

## 🗄️ Migrações do Banco de Dados

O projeto utiliza **Alembic** para controlar a evolução do schema do banco de dados.

Antes de iniciar a API pela primeira vez, certifique-se de que:

1. O PostgreSQL está em execução;
2. O banco de dados configurado em `DATABASE_URL` existe;
3. O ambiente virtual está ativado;
4. As dependências foram instaladas.

### Aplicar as migrações

Execute na raiz do projeto:

```bash
alembic upgrade head
```

Esse comando aplica todas as migrações pendentes e cria/atualiza as tabelas necessárias.

### Criar uma nova migração

Caso os modelos do SQLAlchemy sejam alterados, uma nova migração pode ser gerada automaticamente:

```bash
alembic revision --autogenerate -m "descricao_da_alteracao"
```

Depois de revisar a migração gerada, aplique-a com:

```bash
alembic upgrade head
```

---

## ▶️ Iniciando a API

Com o ambiente virtual ativado, as dependências instaladas, as variáveis configuradas e as migrações aplicadas, execute:

```bash
uvicorn main:app --reload
```

A API estará disponível em:

```text
http://localhost:8000
```

O parâmetro `--reload` habilita o recarregamento automático do servidor durante o desenvolvimento.

---

## 📖 Documentação da API

Por utilizar FastAPI, a documentação interativa da API é gerada automaticamente.

Com o servidor em execução, acesse:

### Swagger UI

`http://localhost:8000/docs`

### ReDoc

`http://localhost:8000/redoc`

O **Swagger UI** permite visualizar os endpoints disponíveis, seus parâmetros, schemas e também realizar requisições diretamente pelo navegador.

---

## 🗄️ Estrutura do Banco de Dados

O modelo relacional da aplicação está documentado no repositório de infraestrutura.

Acesse o [modelo de dados](https://github.com/Plataforma-de-Eventos-e-Ingressos/docs-and-infra/blob/main/documents/data-model.md) para visualizar as entidades e seus relacionamentos.

---

## 🔐 Segurança

A API possui mecanismos para proteger os principais fluxos do sistema, incluindo:

* Autenticação baseada em **JWT**;
* Validação de permissões de acordo com o papel do usuário;
* QR Codes associados aos ingressos;
* Validação de ingressos na entrada do evento;
* Controle de concorrência para evitar a venda duplicada de ingressos;
* Persistência transacional das operações críticas.

A lógica de concorrência é especialmente importante no fluxo de compra, garantindo que duas requisições simultâneas não consigam adquirir o mesmo ingresso.

---

## 🌐 Integrações Externas

A API possui integração com serviços externos de catálogo de eventos e conteúdos.

Entre as integrações utilizadas estão:

* **TMDb** — obtenção de informações relacionadas a filmes e conteúdos;
* **Ticketmaster** — integração com informações de eventos e ingressos.

As credenciais necessárias devem ser configuradas através das variáveis de ambiente.

---

## 📁 Execução com Docker

Para executar o ecossistema completo — incluindo **PostgreSQL, Back-end e Front-end** — consulte o repositório:

**docs-and-infra**

A infraestrutura centralizada fornece o `docker-compose.yml` responsável pela orquestração do ambiente local.

---

## 🧪 Fluxo Recomendado para Desenvolvimento

Uma execução típica do projeto pode seguir os seguintes passos:

```text
1. Clonar o repositório
        ↓
2. Criar o ambiente virtual
        ↓
3. Instalar as dependências
        ↓
4. Configurar o arquivo .env
        ↓
5. Iniciar o PostgreSQL
        ↓
6. Executar as migrações do Alembic
        ↓
7. Iniciar a API com Uvicorn
        ↓
8. Acessar o Swagger
```

---

## 📌 Resumo dos Principais Comandos

| Ação                   | Comando                                          |
| :--------------------- | :----------------------------------------------- |
| Criar ambiente virtual | `python -m venv venv`                            |
| Ativar no Linux/macOS  | `source venv/bin/activate`                       |
| Ativar no Windows      | `venv\Scripts\activate`                          |
| Instalar dependências  | `pip install -r requirements.txt`                |
| Aplicar migrações      | `alembic upgrade head`                           |
| Criar migração         | `alembic revision --autogenerate -m "descricao"` |
| Iniciar API            | `uvicorn main:app --reload`                      |

---

## 📚 Links Úteis

* [FastAPI](https://fastapi.tiangolo.com/)
* [SQLAlchemy](https://www.sqlalchemy.org/)
* [Alembic](https://alembic.sqlalchemy.org/)
* [Pydantic](https://docs.pydantic.dev/)
* [PostgreSQL](https://www.postgresql.org/)
* [Uvicorn](https://www.uvicorn.org/)

---

## 👨‍💻 Desenvolvedor

Desenvolvido por **Robson do Amaral Diógenes** como parte do desafio técnico **Elite Dev - Verzel**.
