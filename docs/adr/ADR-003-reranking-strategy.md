# ADR-003: Reranking Strategy

## Status
Accepted

## Context
Initial retrieval from a vector database (Bi-Encoders) is fast but can be imprecise, especially when the "Top-K" results contain irrelevant noise that can confuse the LLM during generation. To maximize the "Faithfulness" and "Relevance" of the answers, we need a secondary validation step.

## Decision
We will implement a **Cross-Encoder Reranking** step after the initial retrieval.

## Alternatives Considered
1. **Increase Top-K:** Simply sending more chunks to the LLM. This increases latency significantly, hits context window limits, and often leads to the "lost in the middle" phenomenon where LLMs ignore context in the middle of a large prompt.
2. **LLM-based Reranking:** Using a cheaper LLM (like GPT-3.5) to filter chunks. While effective, it is much slower and more expensive than specialized reranker models.

## Implementation Details
- **Model:** Use a lightweight Cross-Encoder model such as `bge-reranker-v2-m3`.
- **Workflow:**
    1. Retrieve Top 20-50 candidates using Hybrid Search.
    2. Pass the Query + Candidate pair through the Reranker.
    3. Select the Top 5 results with the highest scores for the final prompt.

## Consequences

### Positive
- **Higher Precision:** Significantly improves the quality of the context provided to the LLM.
- **Reduced Hallucination:** By ensuring only highly relevant chunks are included, the LLM is less likely to generate incorrect information based on noisy retrieval.
- **Token Efficiency:** Allows us to send fewer, higher-quality tokens to the LLM, potentially reducing costs and improving generation speed.

### Negative
- **Latency Overhead:** Adds 100-300ms to the overall request time depending on the model and hardware (GPU vs. CPU).
- **Compute Requirements:** Rerankers are more computationally intensive than Bi-Encoders and ideally require GPU acceleration in production.
