# Better Business Builder (BBB)

**Turn-Key Autonomous Business Platform** - Onboard once, collect passive income forever.
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

Better Business Builder deploys **Level 6 Autonomous AI Agents** that run your business completely hands-off. You onboard, the AI handles EVERYTHING, you get paid.

## Architecture Overview

```ascii
+-------------------+       +--------------------+       +----------------------+
|                   |       |                    |       |                      |
|  Client / Browser +------->  Nginx (Reverse    +------->  FastAPI Application |
|                   | HTTPS |  Proxy / SSL)      | HTTP  |  (uvicorn workers)   |
+-------------------+       +--------------------+       +----------------------+
                                  |                             |
                                  |                             |
                                  v                             v
                         +--------------------+       +----------------------+
                         |                    |       |                      |
                         |  Grafana (Metrics) |<------+  PostgreSQL 15 (DB)  |
                         |                    |       |                      |
                         +--------------------+       +----------------------+
                                  ^                             |
                                  |                             v
                         +--------------------+       +----------------------+
                         |                    |       |                      |
                         |  Prometheus        |       |  Redis 7 (Cache &    |
                         |  (Time Series DB)  |       |  Message Broker)     |
                         |                    |       +----------------------+
                         +--------------------+                 |
                                                                |
                                                                v
                         +--------------------+       +----------------------+
                         |                    |       |                      |
                         |  Flower (Celery    |<------+  Celery Workers &    |
                         |  Monitor Dashboard)|       |  Celery Beat         |
                         +--------------------+       +----------------------+
```

### Services & Roles
- **Nginx**: Reverse proxy, SSL termination, static file caching, and rate-limiting.
- **FastAPI**: Core backend application handling REST APIs and websockets.
- **PostgreSQL 15**: Primary relational database for user data, business metrics, etc.
- **Redis 7**: Caching layer and message broker for background task queues.
- **Celery Worker**: Executes asynchronous background tasks (e.g., email sending, AI model calls).
- **Celery Beat**: Scheduler for periodic background tasks.
- **Flower**: Web-based monitoring tool for Celery workers.
- **Prometheus**: Time-series database that scrapes metrics from the API and other services.
- **Grafana**: Dashboard visualization for metrics stored in Prometheus.

## Quick Start (Development)

Requires Python 3.9+ and Docker Desktop.

1. **Clone the repository and install dependencies:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -e .
   ```

2. **Copy environment variables:**
   ```bash
   cp .env.example .env
   ```

3. **Start services using Make:**
   ```bash
   make up
   ```

4. **Run database migrations:**
   ```bash
   make migrate
   ```

5. **Access the application:**
   - API Docs: `http://localhost:8000/docs`
   - Flower Monitor: `http://localhost:5555`
   - Grafana Dashboard: `http://localhost:3000`

## Production Deployment Guide

### 1. Server Setup
Provision a Linux server (Ubuntu 22.04 recommended) with Docker and Docker Compose installed.

### 2. Domain & SSL
Point your domain to your server's IP. Place your SSL certificates in the `./certs` directory:
- `./certs/fullchain.pem`
- `./certs/privkey.pem`

### 3. Environment Configuration
Copy the production environment template:
```bash
cp .env.production.example .env.production
```
Fill out `.env.production` carefully. **Important:** Generate secure secret keys:
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

### 4. Deploy
Use the provided deployment script to pull the latest code, build images, restart containers, and run migrations:
```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

Alternatively, manually using the production override:
```bash
make prod-up
make migrate
```

## Environment Variables Reference

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `SECRET_KEY` | Core application secret key | Yes | `v2...` |
| `JWT_SECRET_KEY` | Secret for JWT auth tokens | Yes | `a3...` |
| `DATABASE_URL` | PostgreSQL connection string | Yes | `postgresql://user:pass@host:5432/db` |
| `REDIS_URL` | Redis connection string | Yes | `redis://redis:6379/0` |
| `OPENAI_API_KEY` | OpenAI API Key (or Anthropic/Ollama) | Yes | `sk-...` |
| `STRIPE_SECRET_KEY` | Payment processing secret key | Yes* | `sk_live_...` |
| `CORS_ORIGINS` | Allowed CORS origins | Yes | `https://yourdomain.com` |

*(Required for revenue features)*

## API Documentation

The FastAPI application provides interactive documentation accessible at `/docs` or `/redoc` when running.

### Example: Create a new user
```bash
curl -X 'POST' \
  'https://yourdomain.com/api/v1/users/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "Jane Doe"
}'
```

### Example: Launch Autonomous Business
```bash
curl -X 'POST' \
  'https://yourdomain.com/api/v1/business/launch' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer <your_jwt_token>' \
  -H 'Content-Type: application/json' \
  -d '{
  "concept": "AI Chatbot Integration Service",
  "duration_hours": 24
}'
```

## Testing & Development

Run the test suite using Make:
```bash
make test
```

Run linting:
```bash
make lint
```

Create a new database migration:
```bash
make migration m="Description of changes"
```

Open a bash shell inside the API container:
```bash
make shell
```

## Monitoring Setup

The project includes a robust monitoring stack configured out of the box:
- **Prometheus** scrapes metrics from the FastAPI app and infrastructure.
- **Grafana** connects to Prometheus to visualize these metrics. You can access Grafana at port `3000` (or via reverse proxy). Use the `GRAFANA_PASSWORD` set in your environment to login.
- **Flower** monitors Celery task queues and workers, accessible at port `5555` (or `/flower/` in production). Note: Consider securing this endpoint with authentication if exposed publicly.
