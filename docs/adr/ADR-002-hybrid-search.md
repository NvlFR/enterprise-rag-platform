# ADR-002: Hybrid Search Strategy

## Status
Accepted

## Context
Standard semantic search (vector search) excels at finding context based on meaning but often fails when users search for specific keywords, product codes, or acronyms that may not be well-represented in the embedding space. To achieve enterprise-grade retrieval quality, we need a more robust approach.

## Decision
We will implement a **Hybrid Search** strategy that combines **Dense Retrieval (Semantic/Vector Search)** and **Sparse Retrieval (Keyword/BM25 Search)**.

## Alternatives Considered
1. **Pure Vector Search:** Simple to implement but lacks precision for keyword-heavy queries.
2. **Pure Keyword Search (Elasticsearch/Solr):** Excellent for keywords but fails to capture semantic intent or handle synonyms well.

## Implementation Details
- **Sparse Component:** Use PostgreSQL full-text search with BM25-like scoring or a dedicated BM25 library to index document chunks.
- **Dense Component:** Use `pgvector` with `text-embedding-3-large` for semantic embeddings.
- **Fusion:** Results from both methods will be combined using **Reciprocal Rank Fusion (RRF)** to produce a single ranked list of candidates.

## Consequences

### Positive
- **Improved Recall:** Captures both semantic intent and exact keyword matches.
- **Better User Experience:** Handles technical jargon, acronyms, and specific identifiers much more effectively.
- **Robustness:** Reduces the "failure modes" of the retrieval system when embeddings don't perfectly capture the query nuances.

### Negative
- **Increased Complexity:** Requires maintaining two types of indexes and implementing a fusion algorithm.
- **Latency:** Performing two searches instead of one adds a small amount of overhead, though this is mitigated by parallelizing the search calls.
