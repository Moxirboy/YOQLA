# RAG Module Implementation Guide

## ✅ Already Completed

1. ✅ Updated `pyproject.toml` with RAG dependencies
2. ✅ Extended `src/app/core/config.py` with RAG settings
3. ✅ Added MinIO to `docker-compose.yml`
4. ✅ Updated `src/.env` with RAG configuration
5. ✅ MinIO is running at:
   - API: http://localhost:9000
   - Console: http://localhost:9001 (login: minioadmin/minioadmin)

## 📝 Next Steps - Files to Create

Before running migrations, you need to:

1. **Install new dependencies**
2. **Set your Gemini API key**
3. **Create all RAG module files**
4. **Run database migrations**
5. **Test the system**

---

## 1. Install Dependencies

```bash
# Stop containers first
docker compose down

# Install dependencies
uv sync

# Restart containers
docker compose up -d
```

---

## 2. Set Gemini API Key

Get your API key from: https://makersuite.google.com/app/apikey

Then update `src/.env`:
```bash
GEMINI_API_KEY="AIzaSy..."  # Replace with your actual key
```

---

## 3. Enable pgvector Extension

```bash
# Connect to PostgreSQL
docker compose exec db psql -U postgres -d fastapi_db

# In psql, run:
CREATE EXTENSION IF NOT EXISTS vector;

# Exit
\q
```

---

## 4. Create Migration Files

### Create: `src/app/alembic/versions/001_enable_pgvector.py`

Find your latest migration file in `src/app/alembic/versions/` and note its revision ID.

```python
"""enable pgvector extension

Revision ID: 001_pgvector
Revises: <YOUR_LAST_REVISION_HERE>
Create Date: 2025-01-18 00:00:00.000000

"""
from alembic import op

# Replace with your last revision ID
revision = '001_pgvector'
down_revision = '<YOUR_LAST_REVISION_HERE>'  # CHANGE THIS
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')


def downgrade() -> None:
    op.execute('DROP EXTENSION IF EXISTS vector')
```

### Create: `src/app/alembic/versions/002_create_rag_tables.py`

```python
"""create rag tables

Revision ID: 002_rag_tables
Revises: 001_pgvector
Create Date: 2025-01-18 00:00:01.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '002_rag_tables'
down_revision = '001_pgvector'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Workspace
    op.create_table(
        'workspace',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('owner_user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), default=False, nullable=False),
        sa.ForeignKeyConstraint(['owner_user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_workspace_owner_user_id', 'workspace', ['owner_user_id'])
    op.create_index('ix_workspace_is_deleted', 'workspace', ['is_deleted'])

    # ApiKey
    op.create_table(
        'api_key',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workspace_id', sa.Integer(), nullable=False),
        sa.Column('key_hash', sa.String(255), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('rate_limit_quota', sa.Integer(), default=100, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspace.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_api_key_workspace_id', 'api_key', ['workspace_id'])
    op.create_index('ix_api_key_key_hash', 'api_key', ['key_hash'])

    # Document
    op.create_table(
        'document',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workspace_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(500), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('storage_uri', sa.String(1000), nullable=False),
        sa.Column('bytes', sa.Integer(), nullable=False),
        sa.Column('text_bytes', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(20), default='PENDING', nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspace.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_document_workspace_id', 'document', ['workspace_id'])
    op.create_index('ix_document_status', 'document', ['status'])

    # Chunk
    op.create_table(
        'chunk',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('workspace_id', sa.Integer(), nullable=False),
        sa.Column('ordinal', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('token_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['document.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspace.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_chunk_document_id', 'chunk', ['document_id'])
    op.create_index('ix_chunk_workspace_id', 'chunk', ['workspace_id'])
    op.create_index('ix_chunk_metadata', 'chunk', ['metadata'], postgresql_using='gin')

    # Embedding
    op.create_table(
        'embedding',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('chunk_id', sa.Integer(), nullable=False),
        sa.Column('workspace_id', sa.Integer(), nullable=False),
        sa.Column('vector', postgresql.ARRAY(sa.Float()), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('dim', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['chunk_id'], ['chunk.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspace.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_embedding_chunk_id', 'embedding', ['chunk_id'])
    op.create_index('ix_embedding_workspace_id', 'embedding', ['workspace_id'])

    # Vector index - requires pgvector
    op.execute("""
        CREATE INDEX ix_embedding_vector_ivfflat
        ON embedding
        USING ivfflat (vector vector_cosine_ops)
        WITH (lists = 100)
    """)

    # QueryEvent
    op.create_table(
        'query_event',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workspace_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('api_key_id', sa.Integer(), nullable=True),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('used_tokens_prompt', sa.Integer(), nullable=True),
        sa.Column('used_tokens_completion', sa.Integer(), nullable=True),
        sa.Column('model', sa.String(100), nullable=True),
        sa.Column('top_k', sa.Integer(), nullable=True),
        sa.Column('success', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspace.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['api_key_id'], ['api_key.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_query_event_workspace_id', 'query_event', ['workspace_id'])
    op.create_index('ix_query_event_created_at', 'query_event', ['created_at'])


def downgrade() -> None:
    op.drop_table('query_event')
    op.execute('DROP INDEX IF EXISTS ix_embedding_vector_ivfflat')
    op.drop_table('embedding')
    op.drop_table('chunk')
    op.drop_table('document')
    op.drop_table('api_key')
    op.drop_table('workspace')
```

---

## 5. Run Migrations

```bash
# From project root
docker compose exec web uv run alembic upgrade head
```

---

## 6. Initialize MinIO Bucket

Create a Python script to initialize the MinIO bucket:

### Create: `src/scripts/init_minio.py`

```python
"""Initialize MinIO bucket for RAG documents"""

import asyncio
from app.services.storage import storage_service


async def main():
    """Create the RAG documents bucket in MinIO"""
    try:
        # Check if bucket exists
        if not storage_service.client.head_bucket(Bucket=storage_service.bucket):
            # Create bucket
            storage_service.client.create_bucket(Bucket=storage_service.bucket)
            print(f"✅ Created bucket: {storage_service.bucket}")
        else:
            print(f"✅ Bucket already exists: {storage_service.bucket}")
    except Exception as e:
        # Bucket doesn't exist, create it
        try:
            storage_service.client.create_bucket(Bucket=storage_service.bucket)
            print(f"✅ Created bucket: {storage_service.bucket}")
        except Exception as create_error:
            print(f"❌ Error creating bucket: {create_error}")


if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```bash
docker compose exec web python -m src.scripts.init_minio
```

---

## 7. Complete File Structure

You now need to create these files. I'll provide a downloadable script that creates all of them:

```
src/app/
├── models/rag/
│   ├── __init__.py
│   ├── workspace.py
│   ├── api_key.py
│   ├── document.py
│   ├── chunk.py
│   ├── embedding.py
│   └── query_event.py
├── schemas/rag/
│   ├── __init__.py
│   ├── workspace.py
│   ├── api_key.py
│   ├── document.py
│   └── query.py
├── crud/
│   ├── crud_workspaces.py
│   ├── crud_api_keys.py
│   ├── crud_documents.py
│   ├── crud_chunks.py
│   ├── crud_embeddings.py
│   └── crud_query_events.py
├── services/
│   ├── storage.py
│   └── parse.py
├── rag/
│   ├── chunking.py
│   ├── embeddings.py
│   ├── retrieval.py
│   ├── generation.py
│   └── tasks.py
└── api/v1/
    └── rag.py
```

---

## 8. Quick Test Commands

After creating all files and running migrations:

```bash
# 1. Create a user
curl -X POST "http://localhost:8000/api/v1/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "name":"Test User",
    "username":"testuser",
    "email":"test@test.com",
    "password":"test123"
  }'

# 2. Login
curl -X POST "http://localhost:8000/api/v1/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=test123"

# Save the access_token from response

# 3. Create workspace
curl -X POST "http://localhost:8000/api/v1/rag/workspaces" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"My Workspace"}'

# 4. Access MinIO Console
# Open http://localhost:9001
# Login: minioadmin / minioadmin
```

---

## 9. Next: Create All Code Files

I'll create a script that generates all necessary files. Run:

```bash
chmod +x create_rag_files.sh
./create_rag_files.sh
```

Then you can test the complete RAG system!

---

## Troubleshooting

### MinIO Connection Issues
```bash
# Check MinIO logs
docker compose logs minio

# Restart MinIO
docker compose restart minio
```

### Database Issues
```bash
# Check if pgvector is enabled
docker compose exec db psql -U postgres -d fastapi_db -c "SELECT * FROM pg_extension WHERE extname='vector';"
```

### Worker Not Processing
```bash
# Check worker logs
docker compose logs worker

# Restart worker
docker compose restart worker
```

---

## Resources

- **MinIO Console**: http://localhost:9001
- **API Docs**: http://localhost:8000/docs
- **Gemini API**: https://makersuite.google.com/app/apikey
- **pgvector**: https://github.com/pgvector/pgvector

---

Continue to the next step: Creating all code files...
