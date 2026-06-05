# 🗺️ Product Roadmap: Enterprise Knowledge Assistant (EKA)

## 🎯 Vision Statement
To empower every enterprise with a secure, private, and highly intelligent "organizational brain" that transforms fragmented data into actionable knowledge, accelerating decision-making and productivity through state-of-the-art RAG technology.

---

## 📈 Roadmap Overview

| Phase | Focus | Status |
| :--- | :--- | :--- |
| **Phase 1: Foundation** | MVP, Basic RAG, PDF Support | ✅ Completed |
| **Phase 2: Enterprise Readiness** | Security, Scalability, Connectors | 🏃 In Progress |
| **Phase 3: Advanced Intelligence** | Agentic RAG, Knowledge Graphs | 📅 Q3 2026 |
| **Phase 4: Ecosystem Expansion** | Multi-modal, Edge AI, Mobile | 📅 Q4 2026 |

---

## 🏗️ Phase 1: Foundation (MVP)
*Goal: Establish a functional end-to-end RAG pipeline.*

- [x] **Core API Infrastructure:** FastAPI backend with JWT authentication.
- [x] **Document Ingestion:** Support for PDF and TXT file uploads.
- [x] **Vector Storage:** PostgreSQL + `pgvector` implementation.
- [x] **Basic RAG Pipeline:** Naive retrieval + GPT-4o integration.
- [x] **Citation System:** Verifiable source tracking (page & paragraph).
- [x] **Chat UI:** Modern React-based conversational interface.

---

## 🔐 Phase 2: Enterprise Readiness
*Goal: Make the system robust for production corporate environments.*

- [ ] **Hybrid Search Integration:** Combine Dense Vector Search with BM25 Keyword Search.
- [ ] **Advanced Security (RBAC):** Role-Based Access Control to restrict document access by department.
- [ ] **Document Connectors (v1):**
    - [ ] Google Drive Connector
    - [ ] SharePoint / OneDrive Integration
    - [ ] Notion Integration
- [ ] **Reranking Layer:** Implement Cross-Encoders (BGE-Reranker) for improved retrieval precision.
- [ ] **Analytics Dashboard:** Monitor query frequency, token costs, and user satisfaction.
- [ ] **Async Processing:** Scalable background workers using Celery & Redis.

---

## 🧠 Phase 3: Advanced RAG & Intelligence
*Goal: Surpass standard RAG limitations with advanced reasoning and structured data.*

- [ ] **Agentic RAG:** Autonomous agents that can multi-hop search and self-correct answers.
- [ ] **Knowledge Graph (GraphRAG):** Integrate Neo4j to capture relationships between entities in documents.
- [ ] **Hierarchical Chunking:** Improve context retention for very large documents (manuals/legal).
- [ ] **Multi-lingual Support:** Optimized embeddings and prompts for 20+ languages.
- [ ] **Fine-Tuning Pipeline:** Domain-specific embedding fine-tuning for Legal/Financial sectors.
- [ ] **Evaluation Automation:** Full integration with RAGAS for continuous CI/CD evaluation.

---

## 🌐 Phase 4: Ecosystem & Integration
*Goal: Expand reach and handle non-textual data.*

- [ ] **Multi-modal RAG:** Support for images, charts, and tables within PDFs.
- [ ] **Slack & Microsoft Teams Bot:** Bring the assistant to where the work happens.
- [ ] **Browser Extension:** Overlay EKA knowledge on top of web-based SaaS tools.
- [ ] **Local LLM Support:** Option for fully air-gapped deployment using Llama 3 / Mistral.
- [ ] **Feedback Loop 2.0:** Active learning based on user "thumbs up/down" to refine retrieval.
- [ ] **Enterprise SSO:** SAML / Okta integration for seamless login.

---

## ⏳ Future Horizon (2027+)
- **Personalized Knowledge Agents:** AI that learns individual user preferences and workflows.
- **Predictive Knowledge Delivery:** Surfacing information *before* a user even asks, based on their current task.
- **Auto-Correction of Docs:** Identifying inconsistencies in company documents and suggesting fixes.

---

## 🛠️ Contribution Note
We are currently focusing on **Phase 2**. If you are interested in contributing to the Connectors or Security layers, please check our [Contribution Guidelines](./CONTRIBUTING.md).

---

> *"The goal is not to search, but to find."*
