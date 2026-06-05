# GEMINI.md

## Project Overview

**Enterprise Knowledge Assistant (EKA)** is a production-grade **Retrieval-Augmented Generation (RAG)** platform. It enables organizations to ingest internal documents (PDFs, SOPs, FAQs) and turn them into a searchable, citation-backed AI expert.

- **Purpose:** Centralized "Single Source of Truth" for enterprise data.
- **Backend:** FastAPI (Python 3.10+), Pydantic, SQLAlchemy.
- **Frontend:** Next.js (TypeScript), Tailwind CSS.
- **Database:** PostgreSQL with `pgvector` extension.
- **Infrastructure:** Docker, Redis (Caching/Tasks), Celery, S3/MinIO.
- **AI/ML:** OpenAI GPT-4o / Gemini Pro, LangChain, RAGAS (Evaluation).

## Architecture

The project follows a decoupled architecture:
- **Backend (`/backend`):** Modular FastAPI structure (`api`, `core`, `models`, `schemas`, `services`).
- **Frontend (`/frontend`):** Next.js App Router with Tailwind CSS.
- **RAG Pipeline:** Document Upload -> Parsing -> Chunking -> Embedding -> Vector Storage (`pgvector`) -> Hybrid Search -> Reranking -> LLM Generation.

## Building and Running

*Note: The project is in the early stages of initialization (TASK-001). Commands are based on the planned Makefile.*

### Backend Setup
1. Navigate to `backend/`.
2. Install dependencies: `make install`.
3. Run migrations: `alembic upgrade head` (Planned).
4. Start the server: `uvicorn app.main:app --reload`.

### Frontend Setup
1. Navigate to `frontend/`.
2. Install dependencies: `npm install`.
3. Start development server: `npm run dev`.

### Docker
- Start all services: `docker-compose up --build`.

## Development Conventions

- **Linting & Formatting:** Use `ruff` for Python files. Run `make lint` and `make format`.
- **Pre-commit Hooks:** Managed by `pre-commit`. Ensure they are installed (`pre-commit install`).
- **Dependency Management:**
  - Backend: `pyproject.toml` (standardized via TASK-001).
  - Frontend: `package.json`.
- **API Versioning:** All endpoints are prefixed with `/api/v1`.
- **Naming:** Follow standard PEP 8 for Python and CamelCase for React components.
- **Testing:**
  - Use `pytest` for backend unit and integration tests.
  - Implement RAGAS for evaluating RAG pipeline quality (Faithfulness, Relevance, Precision).
  - Target Hallucination Rate: < 5%.

## Key Directories

- `backend/`: FastAPI source code and logic.
- `frontend/`: Next.js web application.
- `docs/`: Technical specifications, PRD, TDD, and ADRs.
- `tasks/`: Project management and task tracking.
- `tests/`: End-to-end and integration test suites.

## Documentation Index

- [PRD](./docs/PRD.md): Product Requirements.
- [TDD](./docs/TDD.md): Technical Design.
- [Architecture](./docs/architecture.md): System diagrams and flow.
- [API Spec](./docs/api-spec.md): REST API endpoints.
- [ADRs](./docs/adr/): Architectural Decision Records.
- [RAG Evaluation](./docs/rag-evaluation.md): Evaluation methodology.
