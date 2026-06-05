# ADR-001: Use pgvector for Vector Storage

## Status
Accepted

## Context
The project requires a storage solution for high-dimensional vector embeddings generated from document chunks. These vectors are used for semantic similarity search during the retrieval phase of the RAG pipeline.

## Decision
We have decided to use **PostgreSQL with the `pgvector` extension** as our primary vector database.

## Alternatives Considered
1. **Pinecone:** A managed vector database. While highly scalable and easy to use, it introduces external dependency, higher costs for enterprise scale, and potential data sovereignty issues.
2. **Weaviate / Qdrant:** Dedicated open-source vector databases. They offer excellent performance and advanced features like hybrid search out of the box, but require managing a separate database cluster and infrastructure.
3. **FAISS:** A library for efficient similarity search. It is extremely fast but lacks the persistence, transactional guarantees, and relational data integration of a full database.

## Consequences

### Positive
- **Unified Data Store:** We can store relational metadata (users, documents, permissions) and vector embeddings in the same database. This simplifies the architecture and ensures ACID compliance across all data types.
- **Cost-Effective:** Leverages existing PostgreSQL infrastructure without additional licensing fees for managed vector services.
- **Relational Filtering:** Allows for highly efficient pre-filtering or post-filtering of search results using standard SQL `WHERE` clauses (e.g., filtering by `user_id` or `tenant_id` before performing the vector search).
- **Tooling:** Benefits from the mature PostgreSQL ecosystem (backups, monitoring, security).

### Negative
- **Scaling Complexity:** While `pgvector` is highly performant for millions of vectors, extremely large datasets (billions of vectors) might eventually require horizontal scaling or specialized sharding strategies that dedicated vector DBs might handle more natively.
- **Index Management:** Requires manual tuning of HNSW or IVFFlat indexes to maintain search performance as the dataset grows.
