<h1 align="center">YOQLA - AI-Powered Document Intelligence Platform</h1>
<p align="center" markdown=1>
  <i>Production-ready RAG (Retrieval-Augmented Generation) system built with FastAPI</i>
</p>

<p align="center">
  <a href="">
      <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  </a>
  <a href="https://fastapi.tiangolo.com">
      <img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi" alt="FastAPI">
  </a>
  <a href="https://docs.pydantic.dev/2.4/">
      <img src="https://img.shields.io/badge/Pydantic-E92063?logo=pydantic&logoColor=fff&style=for-the-badge" alt="Pydantic">
  </a>
  <a href="https://www.postgresql.org">
      <img src="https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL">
  </a>
  <a href="https://github.com/pgvector/pgvector">
      <img src="https://img.shields.io/badge/pgvector-336791?style=for-the-badge&logo=postgresql&logoColor=white" alt="pgvector">
  </a>
  <a href="https://redis.io">
      <img src="https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=fff&style=for-the-badge" alt="Redis">
  </a>
  <a href="https://min.io">
      <img src="https://img.shields.io/badge/MinIO-C72E49?logo=minio&logoColor=fff&style=for-the-badge" alt="MinIO">
  </a>
  <a href="https://docs.docker.com/compose/">
      <img src="https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=fff&style=for-the-badge" alt="Docker">
  </a>
</p>

---

## 📖 About YOQLA

**YOQLA** is a production-ready document intelligence platform that combines advanced RAG (Retrieval-Augmented Generation) capabilities with a robust FastAPI backend. Upload your documents, ask questions, and get accurate answers powered by AI.

Built with:
- **FastAPI** - Modern Python web framework
- **PostgreSQL + pgvector** - Vector database for similarity search
- **Google Gemini** - LLM for embeddings and text generation
- **MinIO** - S3-compatible object storage
- **Redis + ARQ** - Background job processing
- **Docker Compose** - Easy deployment

---

## ✨ Key Features

### 🤖 RAG System
- **Multi-tenant Architecture** - Isolated workspaces for different users
- **Document Processing** - Support for PDF, DOCX, TXT, MD, CSV files
- **Smart Chunking** - Token-based text splitting with overlap (800 tokens, 150 overlap)
- **Vector Embeddings** - Text-embedding-004 for 768-dimensional vectors
- **Semantic Search** - Cosine similarity with PostgreSQL array operations
- **Context-Aware Responses** - Powered by Google Gemini 2.5 Flash
- **Background Processing** - Async document processing with ARQ
- **File Storage** - MinIO/S3 integration for document storage

### 🔐 Authentication & Security
- **Dual Authentication** - JWT tokens for management, API keys for queries
- **Workspace Isolation** - Complete data separation between workspaces
- **Secure API Keys** - SHA-256 hashed with prefix display
- **Rate Limiting** - Per-tier quota management
- **Session Management** - Cookie-based refresh tokens

### 🚀 Platform Features
- **Fully Async** - Built with async/await throughout
- **Redis Caching** - Server and client-side caching
- **Job Queues** - ARQ integration for background tasks
- **Admin Panel** - Modern web-based admin interface
- **API Documentation** - Auto-generated OpenAPI docs
- **Database Migrations** - Alembic for schema management
- **CRUD Operations** - Efficient queries with FastCRUD
- **Pagination** - Built-in offset and cursor pagination

---

## 📋 Table of Contents

1. [Quick Start](#-quick-start)
2. [RAG System](#-rag-system)
   - [How It Works](#how-it-works)
   - [API Endpoints](#api-endpoints)
3. [Configuration](#-configuration)
4. [Architecture](#-architecture)
5. [Development](#-development)
6. [Deployment](#-deployment)
7. [API Reference](#-api-reference)
8. [Contributing](#-contributing)

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Google Gemini API Key ([Get one here](https://ai.google.dev/))

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/Moxirboy/YOQLA.git
cd YOQLA
```

2. **Create environment file**
```bash
cp src/.env.example src/.env
```

3. **Configure your API keys** in `src/.env`:
```env
# LLM Configuration
LLM_API_KEY="your-gemini-api-key-here"
LLM_MODEL="gemini-2.5-flash"

# Database
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="postgres"
POSTGRES_SERVER="db"
POSTGRES_DB="fastapi_db"

# MinIO Storage
STORAGE_BUCKET="rag-documents"
STORAGE_ENDPOINT_URL="http://minio:9000"
```

4. **Start the application**
```bash
docker compose up -d
```

5. **Access the application**
- API Docs: http://localhost:8000/docs
- Admin Panel: http://localhost:8000/admin
- MinIO Console: http://localhost:9001

### First Steps

1. **Create a user** via `/api/v1/users/signup`
2. **Login** at `/api/v1/login` to get your JWT token
3. **Create a workspace** via `/api/v1/rag/workspaces`
4. **Generate an API key** for your workspace
5. **Upload documents** and start querying!

---

## 🧠 RAG System

### How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                     Document Upload                          │
│  PDF/DOCX/TXT/MD/CSV → MinIO Storage → Processing Queue     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  Background Processing                       │
│  1. Parse Document (extract text)                           │
│  2. Chunk Text (800 tokens, 150 overlap)                    │
│  3. Generate Embeddings (text-embedding-004)                │
│  4. Store Vectors (PostgreSQL + pgvector)                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Query Processing                          │
│  1. User Query → Generate Query Embedding                   │
│  2. Similarity Search (cosine similarity)                   │
│  3. Retrieve Top-K Chunks (ranked by relevance)             │
│  4. Generate Answer (Gemini with context)                   │
│  5. Return Response with Citations                          │
└─────────────────────────────────────────────────────────────┘
```

### API Endpoints

#### Workspace Management
```http
POST   /api/v1/rag/workspaces           # Create workspace
GET    /api/v1/rag/workspaces           # List workspaces
GET    /api/v1/rag/workspaces/{id}      # Get workspace details
PATCH  /api/v1/rag/workspaces/{id}      # Update workspace
DELETE /api/v1/rag/workspaces/{id}      # Delete workspace
```

#### API Key Management
```http
POST   /api/v1/rag/workspaces/{id}/keys     # Create API key
GET    /api/v1/rag/workspaces/{id}/keys     # List API keys
DELETE /api/v1/rag/workspaces/{id}/keys/{key_id}  # Delete API key
```

#### Document Management
```http
POST   /api/v1/rag/workspaces/{id}/documents      # Upload documents
GET    /api/v1/rag/workspaces/{id}/documents      # List documents
DELETE /api/v1/rag/workspaces/{id}/documents/{doc_id}  # Delete document
```

#### Query Endpoint
```http
POST   /api/v1/rag/query                 # Query RAG system
```

**Query Request:**
```json
{
  "query": "What does the RAG system use for text generation?",
  "top_k": 5,
  "score_threshold": 0.3
}
```

**Query Response:**
```json
{
  "answer": "The RAG system uses Google Gemini 2.5 Flash for text generation...",
  "chunks": [
    {
      "content": "The RAG system uses Google Gemini for text generation...",
      "score": 0.763,
      "document_id": 1,
      "document_filename": "documentation.txt",
      "chunk_index": 0
    }
  ],
  "query": "What does the RAG system use for text generation?",
  "latency_ms": 1234,
  "model": "gemini-2.5-flash"
}
```

#### System Endpoints
```http
GET    /api/v1/rag/health               # Health check
GET    /api/v1/rag/test-llm             # Test LLM connection
GET    /api/v1/rag/config               # Get RAG configuration
```

### Usage Example

```bash
# 1. Create workspace
curl -X POST http://localhost:8000/api/v1/rag/workspaces \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Workspace", "description": "Test workspace"}'

# 2. Create API key
curl -X POST http://localhost:8000/api/v1/rag/workspaces/1/keys \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Production Key", "rate_limit_quota": 1000}'

# 3. Upload document
curl -X POST http://localhost:8000/api/v1/rag/workspaces/1/documents \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "files=@document.pdf"

# 4. Query the system
curl -X POST http://localhost:8000/api/v1/rag/query \
  -H "X-API-Key: rag_your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is this document about?",
    "top_k": 5,
    "score_threshold": 0.3
  }'
```

---

## ⚙️ Configuration

### Environment Variables

#### Core Settings
```env
# Application
APP_NAME="YOQLA"
APP_DESCRIPTION="AI-Powered Document Intelligence Platform"
ENVIRONMENT="local"  # local, staging, production

# Database
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="your_secure_password"
POSTGRES_SERVER="db"
POSTGRES_PORT=5432
POSTGRES_DB="fastapi_db"

# Authentication
SECRET_KEY="your-secret-key-here"  # Generate with: openssl rand -hex 32
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

#### RAG Configuration
```env
# LLM Settings
LLM_API_KEY="your-gemini-api-key"
LLM_MODEL="gemini-2.5-flash"
LLM_TEMPERATURE=0.1
LLM_MAX_OUTPUT_TOKENS=2048

# Embeddings
EMBEDDING_PROVIDER="text-embedding-004"
EMBEDDING_DIM=768
EMBEDDING_BATCH_SIZE=100

# RAG Parameters
RAG_CHUNK_SIZE=800
RAG_CHUNK_OVERLAP=150
RAG_TOP_K=5
RAG_SCORE_THRESHOLD=0.3
RAG_MAX_TOKENS=4000

# Storage (MinIO)
STORAGE_PROVIDER="s3"
STORAGE_BUCKET="rag-documents"
STORAGE_REGION="us-east-1"
STORAGE_ACCESS_KEY="minioadmin"
STORAGE_SECRET_KEY="minioadmin"
STORAGE_ENDPOINT_URL="http://minio:9000"

# Upload Restrictions
MAX_UPLOAD_BYTES=52428800  # 50MB
```

#### Redis & Caching
```env
# Redis Cache
REDIS_CACHE_HOST="redis"
REDIS_CACHE_PORT=6379

# Redis Queue (ARQ)
REDIS_QUEUE_HOST="redis"
REDIS_QUEUE_PORT=6379

# Redis Rate Limiting
REDIS_RATE_LIMIT_HOST="redis"
REDIS_RATE_LIMIT_PORT=6379

# Client-Side Cache
CLIENT_CACHE_MAX_AGE=30
```

---

## 🏗️ Architecture

### Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Backend** | FastAPI | Async web framework |
| **Database** | PostgreSQL 16 + pgvector | Data storage + vector search |
| **LLM** | Google Gemini 2.5 Flash | Text generation |
| **Embeddings** | text-embedding-004 | Vector embeddings (768-dim) |
| **Storage** | MinIO | S3-compatible object storage |
| **Cache** | Redis | Caching & session storage |
| **Queue** | ARQ | Background job processing |
| **ORM** | SQLAlchemy 2.0 | Database ORM |
| **Validation** | Pydantic V2 | Data validation |
| **Migrations** | Alembic | Schema migrations |

### Database Schema

```
workspaces (multi-tenant isolation)
├── id, name, user_id, created_at, updated_at
├── is_active, description
└── relationships: api_keys, documents, embeddings, query_events

api_keys (authentication)
├── id, workspace_id, name, key_hash, key_prefix, key
├── created_at, updated_at, is_active, last_used_at
└── rate_limit_quota

documents (uploaded files)
├── id, workspace_id, filename, file_size, mime_type
├── storage_uri, status, error_message, total_chunks
├── metadata (JSONB), uploaded_by, created_at, updated_at
└── relationships: chunks

chunks (text segments)
├── id, document_id, chunk_index, content
├── token_count, metadata (JSONB)
├── created_at
└── relationships: embedding

embeddings (vector storage)
├── id, chunk_id, workspace_id, embedding (ARRAY)
├── model, created_at
└── indexed for similarity search

query_events (usage tracking)
├── id, workspace_id, api_key_id, query, response
├── top_k, score_threshold, retrieved_chunks
├── latency_ms, created_at
```

### Project Structure

```
YOQLA/
├── src/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── rag.py              # RAG endpoints
│   │   │   ├── users.py            # User management
│   │   │   ├── login.py            # Authentication
│   │   │   └── ...
│   │   ├── models/rag/
│   │   │   ├── workspace.py        # Workspace model
│   │   │   ├── api_key.py          # API key model
│   │   │   ├── document.py         # Document model
│   │   │   ├── chunk.py            # Chunk model
│   │   │   ├── embedding.py        # Embedding model
│   │   │   └── query_event.py      # Query event model
│   │   ├── schemas/rag/
│   │   │   ├── workspace.py        # Workspace schemas
│   │   │   ├── api_key.py          # API key schemas
│   │   │   ├── document.py         # Document schemas
│   │   │   └── query.py            # Query schemas
│   │   ├── rag/
│   │   │   ├── chunking.py         # Text chunking logic
│   │   │   ├── embeddings.py       # Embedding generation
│   │   │   ├── retrieval.py        # Similarity search
│   │   │   ├── generation.py       # Answer generation
│   │   │   └── tasks.py            # Background tasks
│   │   ├── services/
│   │   │   ├── storage.py          # MinIO integration
│   │   │   └── parse.py            # Document parsing
│   │   ├── crud/
│   │   │   ├── crud_workspaces.py
│   │   │   ├── crud_api_keys.py
│   │   │   └── crud_documents.py
│   │   └── core/
│   │       ├── config.py           # Configuration
│   │       ├── db/database.py      # Database setup
│   │       └── worker/             # ARQ worker
│   ├── migrations/                 # Alembic migrations
│   └── .env                        # Configuration
├── docker-compose.yml
├── Dockerfile
└── README.md
```

---

## 💻 Development

### Local Development Setup

1. **Install dependencies** (without Docker):
```bash
pip install uv
uv sync
```

2. **Run services**:
```bash
# PostgreSQL
docker run -d -p 5432:5432 --name postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_DB=fastapi_db \
  pgvector/pgvector:pg16

# Redis
docker run -d -p 6379:6379 --name redis redis:alpine

# MinIO
docker run -d -p 9000:9000 -p 9001:9001 --name minio \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  minio/minio server /data --console-address ":9001"
```

3. **Enable pgvector**:
```bash
docker exec -it postgres psql -U postgres -d fastapi_db \
  -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

4. **Run migrations**:
```bash
cd src
uv run alembic upgrade head
```

5. **Create first user**:
```bash
uv run python -m src.scripts.create_first_superuser
```

6. **Start the application**:
```bash
# API Server
uv run uvicorn src.app.main:app --reload

# Worker (in another terminal)
uv run arq src.app.core.worker.settings.WorkerSettings
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/app --cov-report=html

# Run specific test
uv run pytest tests/test_user.py -v
```

### Database Migrations

```bash
# Create migration
cd src
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback
uv run alembic downgrade -1
```

---

## 🚀 Deployment

### Production with Docker Compose

1. **Update docker-compose.yml** to use Gunicorn:
```yaml
web:
  command: gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

2. **Set environment to production**:
```env
ENVIRONMENT="production"
```

3. **Start services**:
```bash
docker compose up -d
```

### NGINX Reverse Proxy

Uncomment the NGINX service in `docker-compose.yml` and configure `default.conf`:

```nginx
upstream yoqla_backend {
    server web:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://yoqla_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Environment Variables for Production

```env
ENVIRONMENT="production"
SECRET_KEY="generate-strong-secret-key"
POSTGRES_PASSWORD="strong-database-password"
STORAGE_ACCESS_KEY="strong-minio-access-key"
STORAGE_SECRET_KEY="strong-minio-secret-key"
```

---

## 📚 API Reference

### Authentication

**Login**
```http
POST /api/v1/login
Content-Type: application/x-www-form-urlencoded

username=user&password=pass

Response: 200 OK
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

**Using JWT Token**
```http
Authorization: Bearer eyJ...
```

**Using API Key**
```http
X-API-Key: rag_your_api_key_here
```

### Complete Workflow

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# 1. Login
login = requests.post(f"{BASE_URL}/login", data={
    "username": "user",
    "password": "password"
})
token = login.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 2. Create workspace
workspace = requests.post(
    f"{BASE_URL}/rag/workspaces",
    headers=headers,
    json={"name": "My Workspace", "description": "Test"}
).json()

workspace_id = workspace["id"]

# 3. Create API key
api_key = requests.post(
    f"{BASE_URL}/rag/workspaces/{workspace_id}/keys",
    headers=headers,
    json={"name": "Production", "rate_limit_quota": 1000}
).json()

rag_key = api_key["key"]

# 4. Upload document
files = {"files": open("document.pdf", "rb")}
upload = requests.post(
    f"{BASE_URL}/rag/workspaces/{workspace_id}/documents",
    headers=headers,
    files=files
).json()

# 5. Query (using API key)
query = requests.post(
    f"{BASE_URL}/rag/query",
    headers={"X-API-Key": rag_key},
    json={
        "query": "What is this document about?",
        "top_k": 5,
        "score_threshold": 0.3
    }
).json()

print(query["answer"])
```

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Add tests for new features
- Update documentation
- Use type hints
- Write descriptive commit messages

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

---

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Based on [FastAPI Boilerplate](https://github.com/benavlabs/FastAPI-boilerplate)
- Powered by [Google Gemini](https://ai.google.dev/)
- Vector search with [pgvector](https://github.com/pgvector/pgvector)

---

## 📞 Contact

**Moxirboy** - [GitHub Profile](https://github.com/Moxirboy)

**Project Link**: [https://github.com/Moxirboy/YOQLA](https://github.com/Moxirboy/YOQLA)

---

<p align="center">Made with ❤️ by Moxirboy</p>
<p align="center">
  <a href="https://github.com/Moxirboy/YOQLA">⭐ Star this repository if you find it helpful!</a>
</p>
