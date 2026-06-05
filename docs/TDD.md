# Technical Design Document (TDD) - EKA

## 1. System Overview
Enterprise Knowledge Assistant (EKA) is a RAG-based platform designed to provide accurate, citation-backed answers from corporate documents. It prioritizes data privacy, scalability, and verifiable accuracy.

## 2. Architecture Components

### Backend (FastAPI)
- **API Layer:** Handles requests, authentication, and orchestration.
- **Service Layer:** Contains business logic for document processing and RAG.
- **Worker Layer:** Background processing using Celery/Redis.

### AI Pipeline
- **Parsing:** `Unstructured` library for complex PDF/DOCX layouts.
- **Embeddings:** `text-embedding-3-large` via OpenAI API.
- **Reranker:** `bge-reranker-v2-m3` hosted on-prem or via API.
- **Generation:** `gpt-4o` or `gemini-1.5-pro`.

## 3. Data Flow

### Ingestion Flow
1. User -> API -> Uploads File.
2. API -> S3 -> Saves File.
3. API -> Celery -> Triggers "Process Task".
4. Worker -> Parser -> Extracts Text/Metadata.
5. Worker -> Embedder -> Generates Vectors.
6. Worker -> PostgreSQL -> Saves Chunks + Vectors.

### Retrieval Flow
1. User -> API -> Sends Question.
2. API -> Retrieval Service -> Rephrases Query.
3. Service -> Vector DB -> Hybrid Search.
4. Service -> Reranker -> Re-ranks results.
5. Service -> LLM -> Generates Answer with Citations.
6. Service -> User -> Returns Final Response.

## 4. Database Schema

### `documents`
- `id` (UUID, PK)
- `title` (String)
- `s3_path` (String)
- `metadata` (JSONB)
- `status` (Enum: processing, completed, error)

### `document_chunks`
- `id` (UUID, PK)
- `document_id` (FK)
- `content` (Text)
- `embedding` (Vector 1536)
- `metadata` (JSONB - page_number, etc.)

## 5. Security Design
- **Authentication:** JWT-based stateless auth.
- **Authorization:** RBAC (Admin, Manager, User).
- **Data Isolation:** Metadata filtering in `pgvector` queries ensures users only retrieve context from documents they have permission to access.
- **Encryption:** AES-256 for documents at rest; TLS 1.3 for all traffic.

## 6. Scalability & Monitoring
- **Horizontal Scaling:** API and Worker pods can scale independently based on CPU/Memory/Queue depth.
- **Database Scaling:** PostgreSQL read-replicas for retrieval-heavy workloads.
- **Observability:**
    - **Logs:** ELK Stack.
    - **Metrics:** Prometheus/Grafana.
    - **Tracing:** Jaeger for RAG pipeline bottlenecks.

## 7. Technology Choices Rationale
- **FastAPI:** High performance, async, type safety.
- **pgvector:** Simplified architecture, relational + vector integration.
- **Next.js:** Modern, SEO-friendly (for landing), React-based.
- **OpenAI/Gemini:** State-of-the-art reasoning and instruction following.
