# ADR-004: FastAPI over Django

## Status
Accepted

## Context
Choosing a backend framework is critical for the long-term maintainability, performance, and developer experience of the Enterprise Knowledge Assistant.

## Decision
We have selected **FastAPI** as the primary backend framework.

## Alternatives Considered
1. **Django:** A robust, "batteries-included" framework. Excellent for traditional CRUD apps, but its synchronous nature by default and overhead make it less ideal for high-performance AI applications.
2. **Flask:** Simple and flexible, but lacks the built-in async support and automatic documentation features of FastAPI.
3. **Go (Gin/Echo):** Extremely fast, but the AI ecosystem (LangChain, LlamaIndex, OpenAI SDKs) is significantly more mature and developer-friendly in Python.

## Rationale
- **Performance:** Built on Starlette and Pydantic, FastAPI is one of the fastest Python frameworks available, rivaling Go and Node.js in some benchmarks.
- **Asynchronous Support:** Natively supports `async/await`, which is crucial for handling multiple concurrent LLM API calls and I/O-bound operations in the RAG pipeline.
- **Developer Productivity:** Automatic OpenAPI (Swagger) documentation and type hinting via Pydantic reduce bugs and improve collaboration with frontend teams.
- **AI Ecosystem:** Most AI/ML libraries are Python-first. FastAPI integrates seamlessly with LangChain, LlamaIndex, and various embedding/LLM providers.

## Consequences

### Positive
- **Rapid Development:** Auto-generated docs and type safety speed up the development cycle.
- **Scalability:** Handles high concurrency efficiently.
- **Modern Standards:** Uses the latest Python features (Type hints, AsyncIO).

### Negative
- **Less "Built-in":** Unlike Django, we need to choose and integrate third-party libraries for things like Migrations (Alembic) and Admin Dashboards.
- **Learning Curve:** Developers familiar only with synchronous Python may need time to adapt to asynchronous patterns.
