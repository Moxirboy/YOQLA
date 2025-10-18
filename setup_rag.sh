#!/bin/bash
# Setup script for RAG module - creates all necessary files and directories

set -e

echo "🚀 Setting up RAG module for FastAPI boilerplate..."

# Create directories
echo "📁 Creating directory structure..."
mkdir -p src/app/models/rag
mkdir -p src/app/schemas/rag
mkdir -p src/app/crud
mkdir -p src/app/services
mkdir -p src/app/rag
mkdir -p src/app/api/v1
mkdir -p public/widget
mkdir -p tests

# Update .env
echo "📝 Updating .env file..."
cat >> src/.env << 'EOF'

# ------------- RAG / Gemini Settings -------------
GEMINI_API_KEY="your-gemini-api-key-here"
GEMINI_MODEL="gemini-1.5-pro"
GEMINI_TEMPERATURE=0.1
GEMINI_MAX_OUTPUT_TOKENS=2048

# ------------- Embeddings -------------
EMBEDDING_PROVIDER="text-embedding-004"
EMBEDDING_DIM=768
EMBEDDING_BATCH_SIZE=100

# ------------- RAG Parameters -------------
RAG_CHUNK_SIZE=800
RAG_CHUNK_OVERLAP=150
RAG_TOP_K=5
RAG_SCORE_THRESHOLD=0.3
RAG_MAX_TOKENS=4000

# ------------- Storage (S3/R2) -------------
STORAGE_PROVIDER="s3"
STORAGE_BUCKET="rag-documents"
STORAGE_REGION="us-east-1"
STORAGE_ACCESS_KEY="your-access-key"
STORAGE_SECRET_KEY="your-secret-key"
STORAGE_ENDPOINT_URL=""

# ------------- Upload Restrictions -------------
MAX_UPLOAD_BYTES=52428800
ENABLE_VIRUS_SCAN=false
EOF

echo "✅ Setup script created. Files will be generated next."
echo ""
echo "⚠️  IMPORTANT NEXT STEPS:"
echo "1. Install dependencies: uv sync"
echo "2. Set GEMINI_API_KEY in src/.env"
echo "3. Set Storage credentials in src/.env"
echo "4. Enable pgvector: psql -d your_db -c 'CREATE EXTENSION IF NOT EXISTS vector;'"
echo "5. Run migrations: cd src && uv run alembic upgrade head"
echo "6. Start ARQ worker: uv run arq src.app.core.worker.settings.WorkerSettings"
echo ""
echo "📚 See README-RAG.md for complete documentation"
