# EKA Backend

FastAPI-based backend for Enterprise Knowledge Assistant.

## Features
- Document Ingestion (PDF, DOCX, TXT)
- RAG Pipeline with Hybrid Search
- Citations and Source Verification
- JWT Authentication & RBAC

## Getting Started

### Prerequisites
- Python 3.10+
- PostgreSQL with `pgvector`
- Redis

### Setup
From the root directory:
```bash
make install
```

### Running the server
```bash
source .venv/bin/activate
uvicorn backend.app.main:app --reload
```

## Structure
- `app/api/`: API endpoints
- `app/core/`: Configuration, security, and logging
- `app/models/`: Database models (SQLAlchemy)
- `app/schemas/`: Pydantic models for validation
- `app/services/`: Business logic (RAG, document processing)
- `tests/`: Unit and integration tests
