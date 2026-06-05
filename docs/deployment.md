# Deployment Guide

## 1. Local Development
For rapid development and testing.

### Prerequisites
- Python 3.10+
- PostgreSQL 15+ with `pgvector` extension
- Redis 6+

### Setup
1. **Clone & Install:**
   ```bash
   git clone https://github.com/your-username/enterprise-knowledge-assistant.git
   cd enterprise-knowledge-assistant/backend
   pip install -r requirements.txt
   ```
2. **Environment Variables:**
   Copy `.env.example` to `.env` and fill in your keys.
3. **Database Migrations:**
   ```bash
   alembic upgrade head
   ```
4. **Run Server:**
   ```bash
   uvicorn app.main:app --reload
   ```

---

## 2. Docker Deployment
The recommended way for staging and self-hosted production.

### Build and Run
```bash
docker-compose -f docker-compose.prod.yml up --build -d
```
This includes:
- **api:** FastAPI backend
- **worker:** Celery worker for document processing
- **db:** PostgreSQL with `pgvector`
- **redis:** Task queue and cache
- **nginx:** Reverse proxy and SSL termination

---

## 3. Cloud Deployment (AWS/GCP/Azure)

### Infrastructure Recommendations
- **Database:** Managed service (e.g., AWS RDS PostgreSQL) with `pgvector` support enabled.
- **Compute:** AWS ECS (Fargate) or EKS (Kubernetes) for the API and Workers.
- **Storage:** AWS S3 for document storage.
- **Cache:** AWS ElastiCache for Redis.

### Production Checklist
- [ ] Enable HTTPS/TLS 1.3.
- [ ] Set `WORKERS_COUNT` based on CPU cores.
- [ ] Configure `CORS_ORIGINS` to only allow your frontend domain.
- [ ] Implement Rate Limiting.
- [ ] Set up Prometheus/Grafana monitoring.
- [ ] Configure centralized logging (CloudWatch/ELK).

---

## 4. Platform-as-a-Service (PaaS)

### Railway / Render
1. Connect your GitHub repository.
2. Add a PostgreSQL database resource (ensure it supports `pgvector`).
3. Add a Redis resource.
4. Set the Environment Variables in the platform dashboard.
5. Deploy.

---

## 5. CI/CD Pipeline
Recommended GitHub Actions workflow:
1. **Linting:** `ruff check .`
2. **Testing:** `pytest`
3. **Build:** Build Docker image and push to ECR/GHCR.
4. **Deploy:** Trigger a rolling update on the target platform.
