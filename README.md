# Better Business Builder (BBB)

**Turn-Key Autonomous Business Platform** — Onboard once, collect passive income forever.

Better Business Builder deploys Level 6 Autonomous AI Agents that run your business
hands-off: research, marketing, sales, fulfillment, support, and finance — all automated.

> Copyright © 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

---

## Architecture

```
                        ┌─────────────┐
                        │   Clients   │
                        └──────┬──────┘
                               │ HTTPS (443)
                        ┌──────▼──────┐
                        │    Nginx    │  SSL termination · rate limiting · static cache
                        └──────┬──────┘
                               │ :8000
                 ┌─────────────▼─────────────┐
                 │   FastAPI / Uvicorn (×4)   │  REST API · WebSocket · /metrics
                 └─────┬──────────┬──────────┘
                       │          │
            ┌──────────▼──┐  ┌───▼──────────┐
            │ PostgreSQL  │  │    Redis      │  Cache · Celery broker
            │    15       │  │    7          │
            └─────────────┘  └───┬──────────┘
                                 │
                 ┌───────────────▼───────────────┐
                 │          Celery                │
                 │  ┌─────────┐  ┌────────────┐  │
                 │  │ Worker  │  │    Beat     │  │  Background & scheduled tasks
                 │  └─────────┘  └────────────┘  │
                 └───────────────────────────────┘
                               │
              ┌────────────────▼───────────────┐
              │          Monitoring             │
              │  ┌────────────┐ ┌───────────┐  │
              │  │ Prometheus │ │  Grafana   │  │
              │  └────────────┘ └───────────┘  │
              │       ┌──────────┐             │
              │       │  Flower  │             │
              │       └──────────┘             │
              └────────────────────────────────┘
```

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/Workofarttattoo/BBB.git && cd BBB

# 2. Copy env and fill in secrets
cp .env.production.example .env.production
#    Edit .env.production — at minimum set SECRET_KEY, JWT_SECRET_KEY, DATABASE_PASSWORD

# 3. Start everything
docker compose up -d          # dev (ports exposed)
# — or —
make up                       # same thing via Makefile
```

The API will be available at **http://localhost:8000**. Health check: `GET /health`.

---

## Full Deployment Guide

### Prerequisites

| Requirement      | Minimum            |
|------------------|--------------------|
| OS               | Ubuntu 22.04 LTS   |
| RAM              | 4 GB               |
| Disk             | 40 GB SSD          |
| Docker           | 24+                |
| Docker Compose   | v2                 |
| Domain           | DNS A record → IP  |

### 1. Server Setup

```bash
# System packages
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io docker-compose-v2 certbot python3-certbot-nginx nginx

# Enable Docker
sudo systemctl enable --now docker
sudo usermod -aG docker $USER   # logout/login after
```

### 2. SSL Certificate (Let's Encrypt)

```bash
sudo certbot certonly --standalone -d bbb.aios.is -d www.bbb.aios.is
# Certs land in /etc/letsencrypt/live/bbb.aios.is/
```

### 3. Deploy

```bash
git clone https://github.com/Workofarttattoo/BBB.git /opt/bbb && cd /opt/bbb
cp .env.production.example .env.production
# ✏️  Fill in every value in .env.production

# Production stack (nginx fronts everything, no ports exposed directly)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Run database migrations
docker compose exec api alembic upgrade head
```

### 4. Nginx Reverse Proxy

Copy the provided `nginx.conf` to your server:

```bash
sudo cp nginx.conf /etc/nginx/sites-available/bbb
sudo ln -sf /etc/nginx/sites-available/bbb /etc/nginx/sites-enabled/bbb
sudo nginx -t && sudo systemctl reload nginx
```

### 5. Verify

```bash
curl -s https://bbb.aios.is/health | python3 -m json.tool
```

### 6. Ongoing Deploys

```bash
# From project root
./scripts/deploy.sh            # pull → migrate → rebuild → restart → health check
# — or —
make deploy
```

---

## API Overview

Base URL: `https://bbb.aios.is` (or `http://localhost:8000` in dev)

### Authentication

```bash
# Register
curl -X POST /api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "s3cure!", "full_name": "Jane Doe"}'

# Login → returns JWT
curl -X POST /api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "s3cure!"}'
# → {"access_token": "eyJ...", "token_type": "bearer"}

# Authenticated request
curl -H "Authorization: Bearer <token>" /api/auth/me
```

### Core Endpoints

| Method | Path                                | Description                       |
|--------|-------------------------------------|-----------------------------------|
| GET    | `/health`                           | Health check                      |
| GET    | `/metrics`                          | Prometheus metrics                |
| POST   | `/api/auth/register`                | Create account                    |
| POST   | `/api/auth/login`                   | Get JWT token                     |
| GET    | `/api/auth/me`                      | Current user profile              |
| POST   | `/api/businesses`                   | Create a business                 |
| GET    | `/api/businesses`                   | List businesses                   |
| POST   | `/api/ai/generate-business-plan`    | AI-generated business plan        |
| POST   | `/api/ai/generate-marketing-copy`   | AI-generated marketing copy       |
| POST   | `/api/ai/generate-email-campaign`   | AI-generated email campaign       |
| POST   | `/api/payments/create-checkout-session` | Stripe checkout              |
| POST   | `/api/payments/create-portal-session`   | Stripe billing portal        |
| POST   | `/api/webhooks/stripe`              | Stripe webhook receiver           |
| GET    | `/api/license/status`               | License status                    |
| POST   | `/api/license/accept-revenue-share` | Accept revenue-share agreement    |
| POST   | `/api/license/activate`             | Activate license                  |
| WS     | `/ws/dashboard/{business_id}`       | Real-time dashboard WebSocket     |

### AI — Generate a Business Plan

```bash
curl -X POST https://bbb.aios.is/api/ai/generate-business-plan \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "business_type": "AI Chatbot Integration Service",
    "target_market": "Small businesses",
    "budget": 5000
  }'
```

### Payments — Create Checkout

```bash
curl -X POST https://bbb.aios.is/api/payments/create-checkout-session \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"price_id": "price_xxx", "success_url": "https://bbb.aios.is/success"}'
```

---

## Environment Variables

Copy `.env.production.example` → `.env.production` and fill in all values.

| Variable                | Required | Description                                      |
|-------------------------|----------|--------------------------------------------------|
| `SECRET_KEY`            | ✅       | App secret — `python -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `JWT_SECRET_KEY`        | ✅       | JWT signing key (generate same way)              |
| `DATABASE_URL`          | ✅       | PostgreSQL connection string                     |
| `DATABASE_PASSWORD`     | ✅       | Password for Docker Compose PostgreSQL           |
| `REDIS_URL`             | ✅       | Redis connection string                          |
| `STRIPE_SECRET_KEY`     | ⚠️       | Stripe live secret key (for payments)            |
| `STRIPE_WEBHOOK_SECRET` | ⚠️       | Stripe webhook signing secret                    |
| `OPENAI_API_KEY`        | ⚠️       | OpenAI API key (or use Ollama)                   |
| `ANTHROPIC_API_KEY`     | ⚠️       | Anthropic API key (optional)                     |
| `LLM_PROVIDER`          |          | `openai` (default) or `ollama`                   |
| `OLLAMA_BASE_URL`       |          | Ollama endpoint if using local LLM               |
| `OLLAMA_MODEL`          |          | Ollama model name                                |
| `SENDGRID_API_KEY`      |          | SendGrid for transactional email                 |
| `SENDGRID_FROM_EMAIL`   |          | Sender email address                             |
| `TWILIO_ACCOUNT_SID`    |          | Twilio account SID                               |
| `TWILIO_AUTH_TOKEN`     |          | Twilio auth token                                |
| `TWILIO_FROM_NUMBER`    |          | Twilio sender phone number                       |
| `TWITTER_CONSUMER_KEY`  |          | Twitter/X API key                                |
| `TWITTER_CONSUMER_SECRET`|         | Twitter/X API secret                             |
| `TWITTER_BEARER_TOKEN`  |          | Twitter/X bearer token                           |
| `BUFFER_ACCESS_TOKEN`   |          | Buffer social media scheduling                   |
| `SENTRY_DSN`            |          | Sentry error tracking DSN                        |
| `GRAFANA_PASSWORD`      |          | Grafana admin password                           |
| `CORS_ORIGINS`          | ✅       | Comma-separated allowed origins                  |

> ✅ = required, ⚠️ = required for that feature to work

---

## Services

| Service         | Image / Build    | Default Port | Description                      |
|-----------------|------------------|--------------|----------------------------------|
| **api**         | `Dockerfile`     | 8000         | FastAPI application (4 workers)  |
| **postgres**    | `postgres:15`    | 5432         | Primary database                 |
| **redis**       | `redis:7`        | 6379         | Cache & Celery broker            |
| **celery**      | `Dockerfile`     | —            | Background task workers          |
| **celery-beat** | `Dockerfile`     | —            | Scheduled task scheduler         |
| **flower**      | `Dockerfile`     | 5555         | Celery task monitoring UI        |
| **prometheus**  | `prom/prometheus` | 9090        | Metrics collection               |
| **grafana**     | `grafana/grafana` | 3000        | Dashboards & alerting            |

---

## Development Setup

```bash
# Clone and enter
git clone https://github.com/Workofarttattoo/BBB.git && cd BBB

# Create virtual environment
python -m venv .venv && source .venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"

# Copy dev env
cp .env.example .env

# Start infrastructure only
docker compose up -d postgres redis

# Run the app locally
uvicorn blank_business_builder.main:app --reload --port 8000

# Run migrations
alembic upgrade head
```

---

## Testing

```bash
# Run full test suite
make test
# — or —
pytest

# With coverage
pytest --cov=blank_business_builder --cov-report=html

# Lint
make lint
# — or —
black --check src/ tests/
isort --check-only src/ tests/
flake8 src/ tests/
```

51 test files covering auth, API endpoints, AI features, payments, autonomous agents,
disaster recovery, and more.

---

## Database Migrations (Alembic)

```bash
# Apply all pending migrations
make migrate
# — or —
docker compose exec api alembic upgrade head

# Create a new migration after model changes
make migration msg="add_user_preferences"
# — or —
docker compose exec api alembic revision --autogenerate -m "add_user_preferences"
```

> `alembic.ini` reads `DATABASE_URL` from the environment automatically (falls back to
> `postgresql://localhost/better_business_builder` for local dev).

---

## Monitoring

### Prometheus

- URL: `http://localhost:9090` (dev) — not exposed in production
- Scrapes `/metrics` on the API every 10 s
- Config: `monitoring/prometheus.yml`

### Grafana

- URL: `http://localhost:3000` (dev) — not exposed in production
- Default login: `admin` / `$GRAFANA_PASSWORD`
- Pre-provisioned datasource → Prometheus
- Dashboards: `monitoring/grafana/dashboards/`

### Flower (Celery)

- URL: `http://localhost:5555` (dev)
- Shows active/completed tasks, worker status, task history

---

## Makefile Targets

```
make up          Start all services
make down        Stop all services
make restart     Restart all services
make build       Rebuild images
make test        Run test suite
make lint        Run linters (black, isort, flake8)
make migrate     Apply database migrations
make migration   Create new migration (msg=...)
make logs        Tail all service logs
make shell       Open bash in the API container
make deploy      Run production deploy script
```

---

## Project Structure

```
BBB/
├── src/blank_business_builder/   # Application source
│   ├── main.py                   # FastAPI app & routes
│   ├── config.py                 # Settings from environment
│   ├── database.py               # SQLAlchemy models & engine
│   ├── auth.py                   # JWT auth, RBAC, rate limiting
│   ├── payments.py               # Stripe integration
│   ├── tasks.py                  # Celery task definitions
│   ├── features/                 # AI content, email, marketing, payments
│   └── premium_workflows/        # Ghost writing, marketing agency, quantum
├── tests/                        # 51 test files
├── alembic/                      # Database migrations
├── monitoring/                   # Prometheus & Grafana config
├── k8s/                          # Kubernetes manifests
├── scripts/                      # Deployment & utility scripts
├── static/                       # Static assets
├── docker-compose.yml            # Development stack
├── docker-compose.prod.yml       # Production overrides
├── Dockerfile                    # Application image
├── nginx.conf                    # Reverse proxy config
├── Makefile                      # Common commands
└── .env.production.example       # Environment template
```

---

## License

Proprietary — Copyright © 2025 Joshua Hendricks Cole (DBA: Corporation of Light).
All Rights Reserved. PATENT PENDING. See [LICENSE](LICENSE) for details.
