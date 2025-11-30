# CLAUDE.md - AI Assistant Guide for Better Business Builder (BBB)

> **Last Updated**: 2025-11-30
> **Repository**: Better Business Builder (BBB)
> **Purpose**: Comprehensive guide for AI assistants working with the BBB codebase

---

## Table of Contents

1. [Repository Overview](#repository-overview)
2. [Codebase Architecture](#codebase-architecture)
3. [Core Components](#core-components)
4. [Development Workflows](#development-workflows)
5. [Testing Conventions](#testing-conventions)
6. [Deployment & Infrastructure](#deployment--infrastructure)
7. [API Structure](#api-structure)
8. [Configuration Management](#configuration-management)
9. [Common Tasks](#common-tasks)
10. [Best Practices](#best-practices)
11. [File Reference Guide](#file-reference-guide)

---

## Repository Overview

### What is BBB?

Better Business Builder (BBB) is a **turn-key autonomous business platform** that deploys Level 6 AI agents to run businesses completely hands-off. Users onboard once, AI handles everything, and they collect passive income.

**Key Capabilities**:
- Fully autonomous business operations (research, marketing, sales, fulfillment, support, finance)
- Quantum-inspired business idea optimization
- Multi-domain expert system with RAG
- Premium workflows (ghost writing, marketing agency, no-code apps)
- Integration with ech0 local brain for advanced LLM capabilities
- Scalable to 1M+ concurrent business deployments

**Technology Stack**:
- **Backend**: Python 3.9+, FastAPI, SQLAlchemy, Alembic
- **Database**: PostgreSQL 15 with JSONB, UUID support
- **Cache/Queue**: Redis 7, Celery
- **LLMs**: OpenAI GPT-4, Anthropic Claude, Ollama/ech0
- **Payments**: Stripe
- **Email**: SendGrid
- **Monitoring**: Prometheus, Grafana, Sentry
- **Deployment**: Docker, Docker Compose, Kubernetes-ready

**Target Outcome**: $20,000+ per quarter in passive income per business

---

## Codebase Architecture

### Directory Structure

```
/home/user/BBB/
├── src/blank_business_builder/          # Main Python package
│   ├── __init__.py                      # Package exports
│   ├── main.py                          # FastAPI app (150+ endpoints)
│   ├── cli.py                           # CLI interface
│   ├── database.py                      # SQLAlchemy ORM models
│   ├── auth.py                          # JWT authentication
│   ├── payments.py                      # Stripe integration
│   ├── integrations.py                  # External API factories
│   ├── level6_agent.py                  # Autonomous agent core
│   ├── quantum_optimizer.py             # Business idea ranking
│   ├── expert_system.py                 # Multi-domain expert system
│   ├── autonomous_business.py           # Business orchestration
│   ├── ech0_service.py                  # ech0 local brain integration
│   ├── metrics.py                       # Prometheus metrics
│   ├── business_data.py                 # 32+ curated business ideas
│   ├── onboarding.py                    # User intake wizard
│   ├── jiminy.py                        # Ethical compliance
│   ├── features/                        # Feature modules
│   │   ├── ai_content_generator.py     # Content creation
│   │   ├── marketing_automation.py     # Campaign orchestration
│   │   ├── ai_workflow_builder.py      # No-code workflows
│   │   └── white_label_platform.py     # Reseller capabilities
│   └── premium_workflows/               # Premium tier features
│       ├── ghost_writing_agent.py      # Fiverr/Upwork automation
│       ├── marketing_agency_agent.py   # Digital marketing
│       ├── nocode_app_agent.py         # SaaS/app building
│       └── quantum_optimizer.py        # Advanced optimization
├── tests/                               # Test suite
│   ├── test_auth.py                    # Authentication tests
│   ├── test_businesses.py              # Business CRUD tests
│   ├── test_comprehensive_bbb.py       # Integration tests
│   └── [8 more test files]
├── alembic/                            # Database migrations
├── monitoring/                         # Prometheus/Grafana configs
├── k8s/                                # Kubernetes manifests
├── docs/                               # Documentation
├── docker-compose.yml                  # Full stack orchestration
├── Dockerfile                          # Production container
├── pyproject.toml                      # Project metadata
├── requirements.txt                    # Python dependencies
├── schema.sql                          # PostgreSQL schema
└── [Root-level autonomous systems]     # Standalone scripts
```

### Design Patterns

| Pattern | Implementation | Location |
|---------|---------------|----------|
| **Factory** | Service instance creation | `integrations.py` |
| **Observer** | Metric collection | `metrics.py` |
| **Strategy** | Backup/recovery strategies | `disaster_recovery.py` |
| **Dependency Injection** | FastAPI `Depends()` | `main.py` |
| **Async/Await** | Non-blocking I/O | Throughout |
| **Dataclasses** | Typed entities | All modules |
| **Singleton** | DB connection pools | `database.py` |

### Package Organization

- **Core Package**: `src/blank_business_builder/` - All production code
- **CLI Entry**: `src/blank_business_builder/cli.py` - Commands: `bbb`, `blank-business-builder`
- **API Entry**: `src/blank_business_builder/main.py` - FastAPI application
- **Tests**: `tests/` - Pytest suite with 85%+ coverage requirement
- **Root Scripts**: Autonomous orchestration scripts (deployment, monitoring)

---

## Core Components

### 1. Level 6 Autonomous Agents

**File**: `src/blank_business_builder/level6_agent.py`

**Purpose**: Self-directed AI agents managing business operations with 80-98% automation

**Key Classes**:
```python
class AutonomyLevel(Enum):
    LIMITED = "limited"    # 80% automation (Starter)
    FULL = "full"          # 95% automation (Professional)
    MAXIMUM = "maximum"    # 98% automation (Enterprise)

class Level6Agent:
    async def run_autonomous_operations(db: Session) -> List[AgentDecision]
    async def manage_customer_lifecycle(db: Session)
    async def optimize_content_generation(db: Session)
    async def manage_churn_prevention(db: Session)
    async def optimize_revenue(db: Session)
    async def manage_marketing_campaigns(db: Session)
    async def handle_support_automation(db: Session)
    async def strategic_planning(db: Session)  # MAXIMUM only
    async def market_expansion_analysis(db: Session)  # MAXIMUM only
```

**Decision Model**:
```python
@dataclass
class AgentDecision:
    decision_type: str       # Type of operation
    action: str             # Specific action to take
    confidence: float       # 0.0-1.0 confidence score
    reasoning: str          # Explanation
    data: Dict[str, Any]    # Supporting data
    timestamp: datetime
    requires_approval: bool # Human-in-loop flag
```

**When modifying agents**:
- All agent operations must be async
- Always include confidence scores and reasoning
- Log decisions to audit_log table
- Respect autonomy level restrictions
- Use `requires_approval=True` for high-risk actions

### 2. Quantum Optimizer

**File**: `src/blank_business_builder/quantum_optimizer.py`

**Purpose**: Rank business ideas using quantum-inspired probability amplitudes

**Algorithm**:
1. Project 3-month profit accounting for ramp-up: `revenue * months - expenses - startup_cost`
2. Convert to probability amplitudes: `amplitude = sqrt(profit / total_profit)`
3. Calculate success probability: `probability = amplitude²`
4. Filter ideas failing $4,500/month floor
5. Return ranked results by (probability, profit) descending

**Usage**:
```python
from blank_business_builder import QuantumOptimizer, BusinessIdea

optimizer = QuantumOptimizer(
    monthly_floor=4500.0,    # Minimum monthly profit
    quarter_target=20000.0   # Quarterly revenue target
)

results = optimizer.evaluate(business_ideas)
# Returns List[OptimizationResult] sorted by success probability
```

**Key Fields**:
- `three_month_profit`: Projected profit over 3 months
- `success_probability`: Quantum amplitude squared
- `meets_floor`: Boolean for $4,500/month threshold
- `meets_target`: Boolean for $20,000/quarter threshold

### 3. Expert System

**File**: `src/blank_business_builder/expert_system.py`

**Purpose**: Multi-domain expert system with RAG, vector databases, and ensemble intelligence

**Architecture**:
- **Vector DB**: ChromaDB + FAISS for semantic search
- **Fine-tuning**: PyTorch-based domain-specific training
- **Ensemble**: Multiple experts voting on answers
- **RAG Pipeline**: Retrieve → Augment → Generate

**Supported Domains**:
```python
class ExpertDomain(Enum):
    # Science
    CHEMISTRY, BIOLOGY, PHYSICS, MATERIALS_SCIENCE
    # Engineering
    SOFTWARE_ENGINEERING, ELECTRICAL, MECHANICAL
    # Business
    MARKETING, FINANCE, SALES, OPERATIONS
    # AI/ML
    DATA_SCIENCE, MACHINE_LEARNING, QUANTUM_COMPUTING
    # General
    GENERAL
```

**Query Interface**:
```python
@dataclass
class ExpertQuery:
    query: str
    domain: Optional[ExpertDomain]
    context: Dict[str, Any]
    max_results: int = 5
    confidence_threshold: float = 0.7
    use_ensemble: bool = False

# Response includes answer, confidence, sources, citations
response: ExpertResponse = await expert_system.query(expert_query)
```

**When extending**:
- Add domain-specific knowledge to vector DB
- Fine-tune models on domain data
- Ensure graceful degradation without optional deps
- Always return confidence scores

### 4. Premium Workflows

**Directory**: `src/blank_business_builder/premium_workflows/`

**Purpose**: Turn-key autonomous business models for premium users

#### A. Ghost Writing Agent (`ghost_writing_agent.py`)
- Auto-creates Fiverr/Upwork gigs
- Fulfills writing orders using LLMs
- Manages client communication
- Handles revisions and payments
- **Revenue**: $50-$300+ per project

#### B. Marketing Agency Agent (`marketing_agency_agent.py`)
- Multi-channel campaign management
- Client onboarding automation
- Content calendar generation
- Performance analytics
- **Pricing**: $999-$2,999/month

#### C. No-Code App Agent (`nocode_app_agent.py`)
- Analyzes app requirements
- Generates low-code solutions (Bubble, Zapier)
- Deploys working prototypes
- **Revenue**: $999-$5,000 per build + revenue share

**Integration Pattern**:
```python
from blank_business_builder.premium_workflows import GhostWritingAgent

agent = GhostWritingAgent(
    user_id=user.id,
    autonomy_level=AutonomyLevel.FULL
)
await agent.run_autonomous_operations(db)
```

### 5. ech0 Integration

**File**: `src/blank_business_builder/ech0_service.py`

**Purpose**: Local LLM brain with extended context and specialized capabilities

**Key Methods**:
```python
class ECH0Service:
    async def _get_ech0_response(prompt: str, max_tokens: int) -> str
    async def generate_content(topic: str, content_type: str) -> str
    async def send_email(from_email, to_email, subject, body) -> bool
    async def post_to_social_media(platform: str, content: str) -> bool
    async def scrape_url(url: str) -> str
    async def google_search(query: str) -> str
```

**Advanced Capabilities** (root-level scripts):
- `ech0_semantic_lattice.py` - Semantic knowledge mapping
- `ech0_enhanced_parliament.py` - Advanced approval flow with Prime optimization
- `ech0_autonomous_business.py` - Full autonomous operations
- `ech0_full_autonomy_system.py` - Maximum autonomy mode

**When using ech0**:
- Fallback to OpenAI/Anthropic if ech0 unavailable
- Use for tasks requiring extended context (>100K tokens)
- Enable semantic lattice for prior art detection
- Use parliament mode for multi-expert consensus

---

## Development Workflows

### Setting Up Local Environment

```bash
# 1. Clone and navigate
cd /home/user/BBB

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install --upgrade pip
pip install -e .              # Editable install
pip install -e ".[dev]"       # With dev dependencies

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your API keys and configuration

# 5. Initialize database
docker-compose up -d postgres redis
alembic upgrade head

# 6. Run development server
uvicorn blank_business_builder.main:app --reload --port 8000

# 7. Or use CLI
bbb --gui
```

### Code Style & Formatting

**Tools** (configured in `pyproject.toml`):
- **Black**: Code formatter (line length 100)
- **isort**: Import sorter (Black-compatible profile)
- **mypy**: Static type checker (gradual typing)
- **flake8**: Linter
- **bandit**: Security linter
- **safety**: Dependency vulnerability scanner

**Pre-commit workflow**:
```bash
# Format code
black src/ tests/
isort src/ tests/

# Type check
mypy src/

# Lint
flake8 src/ tests/

# Security scan
bandit -r src/
safety check
```

### Type Hints Convention

**Always use type hints** for:
- Function parameters
- Return types
- Class attributes
- Complex data structures

**Example**:
```python
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class AgentDecision:
    decision_type: str
    confidence: float
    data: Dict[str, Any]
    timestamp: datetime

async def process_decision(
    decision: AgentDecision,
    db: Session,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Process an agent decision and return results."""
    pass
```

### Async/Await Patterns

**Use async for**:
- API route handlers
- Database queries
- External API calls
- Agent operations
- Long-running tasks

**Example**:
```python
# Good - parallel execution
async def run_autonomous_operations(self, db: Session):
    tasks = [
        self.manage_customer_lifecycle(db),
        self.optimize_content_generation(db),
        self.manage_churn_prevention(db),
    ]
    results = await asyncio.gather(*tasks)
    return results

# Bad - sequential when parallel is possible
async def run_autonomous_operations(self, db: Session):
    result1 = await self.manage_customer_lifecycle(db)
    result2 = await self.optimize_content_generation(db)  # Waits unnecessarily
    return [result1, result2]
```

### Database Operations

**Always use sessions from dependency injection**:
```python
from sqlalchemy.orm import Session
from fastapi import Depends

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/api/businesses")
async def create_business(
    business_data: BusinessCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    business = Business(**business_data.dict(), user_id=current_user.id)
    db.add(business)
    db.commit()
    db.refresh(business)
    return business
```

**Migration workflow**:
```bash
# Create migration
alembic revision --autogenerate -m "Add new table"

# Review migration file in alembic/versions/

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Adding New Features

**Standard process**:

1. **Create feature module**: `src/blank_business_builder/features/new_feature.py`
2. **Define data models**: Add SQLAlchemy models to `database.py`
3. **Add API endpoints**: Add routes to `main.py` or create router
4. **Write tests**: Create `tests/test_new_feature.py`
5. **Update documentation**: Add to relevant markdown files
6. **Create migration**: `alembic revision --autogenerate`

**Example structure**:
```python
# src/blank_business_builder/features/new_feature.py

from typing import Dict, Any
from sqlalchemy.orm import Session
from ..database import NewFeatureModel

class NewFeatureService:
    """Service for new feature operations."""

    def __init__(self, db: Session):
        self.db = db

    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process new feature request."""
        # Implementation
        pass

# Add to main.py
from .features.new_feature import NewFeatureService

@app.post("/api/new-feature")
async def new_feature_endpoint(
    data: NewFeatureRequest,
    db: Session = Depends(get_db)
):
    service = NewFeatureService(db)
    result = await service.process(data.dict())
    return result
```

---

## Testing Conventions

### Test Structure

**Location**: `/home/user/BBB/tests/`

**Organization**:
- `test_auth.py` - Authentication and authorization
- `test_businesses.py` - Business CRUD operations
- `test_comprehensive_bbb.py` - Full integration tests
- `test_ech0_prime_bbb.py` - ech0 integration
- `test_integration.py` - API endpoint tests
- `test_multi_channel_marketing.py` - Marketing automation
- `test_smart_lead_nurturing.py` - Lead management
- `test_disaster_recovery.py` - Backup and failover

### Test Configuration

**pytest.ini**:
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
addopts = -v --tb=short --cov=src --cov-report=html --cov-report=term
```

**Coverage requirement**: Minimum 85%

### Writing Tests

**Pattern**:
```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from blank_business_builder.main import app
from blank_business_builder.database import Base

# In-memory database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine)

@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test, drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)

@pytest.fixture
def auth_headers(client):
    """Get authentication headers."""
    response = client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "testpass123",
        "full_name": "Test User"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

class TestBusinesses:
    """Test business operations."""

    def test_create_business(self, client, auth_headers):
        """Test creating a new business."""
        response = client.post(
            "/api/businesses",
            json={
                "business_name": "AI Chatbot Service",
                "industry": "Technology",
                "description": "AI chatbot integration"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["business_name"] == "AI Chatbot Service"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_autonomous_operations(self, db):
        """Test agent autonomous operations."""
        from blank_business_builder.level6_agent import Level6Agent

        agent = Level6Agent(user_id="test", autonomy_level=AutonomyLevel.FULL)
        decisions = await agent.run_autonomous_operations(db)
        assert len(decisions) > 0
        assert all(isinstance(d, AgentDecision) for d in decisions)
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py

# Run specific test
pytest tests/test_auth.py::TestAuthentication::test_register_user

# Run with coverage
pytest --cov=src --cov-report=html

# Run integration tests only
pytest -m integration

# Run unit tests only
pytest -m unit

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

---

## Deployment & Infrastructure

### Docker Stack

**File**: `docker-compose.yml`

**Services**:
- **postgres**: PostgreSQL 15 database
- **redis**: Redis 7 (cache + task queue)
- **api**: FastAPI application (Uvicorn)
- **celery**: Background job worker
- **celery-beat**: Scheduled task scheduler
- **flower**: Celery monitoring (port 5555)
- **prometheus**: Metrics collection (port 9090)
- **grafana**: Monitoring dashboards (port 3000)

**Start full stack**:
```bash
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f api

# Stop stack
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

### Environment Variables

**Required variables** (see `.env.example`):

```bash
# Application
APP_NAME=BBB
ENVIRONMENT=production
DEBUG=false

# Database
DATABASE_URL=postgresql://bbb:password@postgres:5432/bbb
REDIS_URL=redis://redis:6379/0

# Authentication
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Payments
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Email
SENDGRID_API_KEY=SG...
SENDGRID_FROM_EMAIL=noreply@yourdomain.com

# LLMs
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Monitoring
SENTRY_DSN=https://...
PROMETHEUS_PORT=9090
```

### Deployment Scripts

**Root-level scripts**:

1. **Deploy Autonomous Business**:
```bash
./DEPLOY_AUTONOMOUS_BUSINESS.sh
# Deploys single autonomous business with all services
```

2. **Deploy Complete System**:
```bash
./DEPLOY_COMPLETE_AUTONOMOUS_SYSTEM.sh
# Full stack deployment with monitoring
```

3. **Stop System**:
```bash
./STOP_AUTONOMOUS_SYSTEM.sh
# Graceful shutdown of all services
```

### Health Checks

**Endpoints**:
- `GET /health` - Basic health check
- `GET /metrics` - Prometheus metrics
- `GET /api/agents/status` - Agent operation status

**Example health check**:
```bash
curl http://localhost:8000/health
# Returns: {"status": "healthy", "timestamp": "2025-11-30T12:15:00Z"}
```

### Monitoring

**Prometheus Metrics** (`metrics.py`):
```python
# Request metrics
bbb_requests_total
bbb_request_duration_seconds

# Business metrics
bbb_active_businesses
bbb_revenue_total
bbb_subscription_changes_total

# Agent metrics
bbb_agent_tasks_total
bbb_agent_decisions_total

# AI metrics
bbb_ai_requests_total
bbb_ai_tokens_used_total
```

**Grafana Dashboards**:
- Overall system health
- Business performance
- Agent operations
- Revenue analytics
- API performance

Access: `http://localhost:3000` (default credentials in `.env`)

---

## API Structure

### Base URL

**Local**: `http://localhost:8000`
**Production**: Set via `BASE_URL` environment variable

### Authentication

**Type**: JWT Bearer tokens

**Flow**:
1. Register: `POST /api/auth/register`
2. Login: `POST /api/auth/login` → Receive `access_token` + `refresh_token`
3. Use token: `Authorization: Bearer <access_token>` header
4. Refresh: `POST /api/auth/refresh` with refresh token
5. Logout: `POST /api/auth/logout`

**Token lifetimes**:
- Access token: 60 minutes
- Refresh token: 30 days

### Endpoint Conventions

**Pattern**: `/api/{resource}/{action}`

**HTTP Methods**:
- `GET` - Retrieve resource(s)
- `POST` - Create new resource
- `PATCH` - Update resource (partial)
- `PUT` - Replace resource (full)
- `DELETE` - Remove resource

**Response format**:
```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "timestamp": "2025-11-30T12:15:00Z"
}
```

**Error format**:
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid business name",
    "details": { "field": "business_name", "issue": "too_short" }
  },
  "timestamp": "2025-11-30T12:15:00Z"
}
```

### Key Endpoint Groups

**Authentication**:
```
POST   /api/auth/register
POST   /api/auth/login
POST   /api/auth/refresh
POST   /api/auth/logout
GET    /api/auth/me
```

**Businesses**:
```
POST   /api/businesses
GET    /api/businesses
GET    /api/businesses/{business_id}
PATCH  /api/businesses/{business_id}
DELETE /api/businesses/{business_id}
```

**Content Generation**:
```
POST   /api/content/blog
POST   /api/content/email
POST   /api/content/social
POST   /api/content/copy
```

**Marketing Campaigns**:
```
POST   /api/campaigns
GET    /api/campaigns
GET    /api/campaigns/{campaign_id}
PATCH  /api/campaigns/{campaign_id}
POST   /api/campaigns/{campaign_id}/publish
```

**Agent Operations**:
```
GET    /api/agents/status
GET    /api/agents/decisions
POST   /api/agents/approve-decision/{decision_id}
```

**Analytics**:
```
GET    /api/metrics/dashboard
GET    /api/metrics/revenue
GET    /api/metrics/customers
GET    /api/metrics/campaigns
```

### Adding New Endpoints

**Pattern**:
```python
# In main.py or create a router

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

router = APIRouter(prefix="/api/new-feature", tags=["new-feature"])

class NewFeatureRequest(BaseModel):
    field1: str
    field2: int

class NewFeatureResponse(BaseModel):
    result: str
    status: str

@router.post("", response_model=NewFeatureResponse)
async def create_new_feature(
    request: NewFeatureRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new feature instance."""
    # Validate permissions
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="User not active")

    # Process request
    result = process_feature(request, db)

    # Log to audit trail
    log_audit(current_user.id, "new_feature_created", result.id)

    return NewFeatureResponse(result=result.id, status="created")

# Include router in app
app.include_router(router)
```

---

## Configuration Management

### Configuration Files

| File | Purpose |
|------|---------|
| `.env` | Environment-specific secrets (NEVER commit) |
| `.env.example` | Template for required variables |
| `pyproject.toml` | Project metadata, dependencies, tool configs |
| `pytest.ini` | Test runner configuration |
| `alembic.ini` | Database migration settings |
| `docker-compose.yml` | Container orchestration |

### Environment Variable Loading

**Uses `python-dotenv`**:
```python
from dotenv import load_dotenv
import os

load_dotenv()  # Loads .env file

DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
```

**Pydantic Settings** (recommended):
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    openai_api_key: str
    stripe_secret_key: str

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

### Feature Flags

**Pattern**:
```python
# In .env
ENABLE_AUTONOMOUS_MODE=true
ENABLE_AI_CONTENT_GENERATION=true
ENABLE_REALTIME_UPDATES=false

# In code
import os

ENABLE_AUTONOMOUS_MODE = os.getenv("ENABLE_AUTONOMOUS_MODE", "false").lower() == "true"

if ENABLE_AUTONOMOUS_MODE:
    # Enable autonomous features
    pass
```

### Secrets Management

**Development**: Use `.env` file
**Production**: Use environment variables or secrets manager (AWS Secrets Manager, Vault)

**Never commit**:
- API keys
- Database passwords
- JWT secrets
- Stripe keys
- Any credentials

---

## Common Tasks

### Task 1: Add a New Business Idea

**File**: `src/blank_business_builder/business_data.py`

```python
BUSINESS_IDEAS = [
    # ... existing ideas
    BusinessIdea(
        name="Your New Business",
        industry="Industry Name",
        description="Brief description",
        startup_cost=1000.0,
        expected_monthly_revenue=5000.0,
        expected_monthly_expenses=2000.0,
        time_commitment_hours_per_week=10,
        ramp_up_months=2
    )
]
```

### Task 2: Create a New Agent Capability

**File**: `src/blank_business_builder/level6_agent.py`

```python
class Level6Agent:
    async def new_capability(self, db: Session) -> List[AgentDecision]:
        """Add new autonomous capability."""
        decisions = []

        # Implement logic
        if condition:
            decision = AgentDecision(
                decision_type="new_capability",
                action="specific_action",
                confidence=0.85,
                reasoning="Why this decision was made",
                data={"key": "value"},
                timestamp=datetime.utcnow(),
                requires_approval=False
            )
            decisions.append(decision)

        return decisions

    async def run_autonomous_operations(self, db: Session):
        tasks = [
            # ... existing tasks
            self.new_capability(db),  # Add new capability
        ]
        results = await asyncio.gather(*tasks)
        return [d for result in results for d in (result or [])]
```

### Task 3: Add External API Integration

**File**: `src/blank_business_builder/integrations.py`

```python
class NewServiceClient:
    """Client for New Service API."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.newservice.com"

    async def call_api(self, endpoint: str, data: Dict) -> Dict:
        """Make API call to New Service."""
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/{endpoint}",
                json=data,
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            response.raise_for_status()
            return response.json()

# Add to integrations factory
def get_new_service_client() -> NewServiceClient:
    api_key = os.getenv("NEW_SERVICE_API_KEY")
    return NewServiceClient(api_key)
```

### Task 4: Create Database Migration

```bash
# 1. Modify models in database.py
# Example: Add new field to Business model

# 2. Generate migration
alembic revision --autogenerate -m "Add new_field to businesses"

# 3. Review generated migration in alembic/versions/

# 4. Edit if needed, then apply
alembic upgrade head

# 5. To rollback if needed
alembic downgrade -1
```

### Task 5: Add Prometheus Metric

**File**: `src/blank_business_builder/metrics.py`

```python
from prometheus_client import Counter, Gauge, Histogram

# Add new metric
new_feature_requests = Counter(
    "bbb_new_feature_requests_total",
    "Total number of new feature requests",
    ["feature_type", "status"]
)

# Use in code
new_feature_requests.labels(feature_type="content", status="success").inc()
```

### Task 6: Run Autonomous Business Locally

```bash
# Using CLI
bbb --autonomous \
    --business "AI Chatbot Integration Service" \
    --duration 24 \
    --founder "John Doe" \
    --location "San Francisco" \
    --startup-budget 5000 \
    --weekly-hours 20
```

**Programmatic**:
```python
from blank_business_builder.autonomous_business import launch_autonomous_business
import asyncio

async def main():
    metrics = await launch_autonomous_business(
        business_concept="AI Chatbot Integration Service",
        founder_name="John Doe",
        duration_hours=24.0
    )
    print(f"Revenue: ${metrics['metrics']['revenue']['total']}")

asyncio.run(main())
```

---

## Best Practices

### Code Quality

1. **Type Hints**: Always use type hints for parameters, returns, and attributes
2. **Docstrings**: Document all public functions, classes, and modules
3. **Error Handling**: Use try-except with specific exceptions, log errors
4. **Security**: Validate inputs, sanitize SQL, use parameterized queries
5. **Performance**: Use async/await, batch operations, cache results
6. **Testing**: Write tests for all new features (85%+ coverage)

### Database Best Practices

1. **Use transactions**: Wrap related operations in transactions
2. **Connection pooling**: Use SQLAlchemy's built-in pooling
3. **Migrations**: Never modify schema manually, always use Alembic
4. **Indexes**: Add indexes for frequently queried fields
5. **JSONB**: Use JSONB for flexible metadata, not critical data

### API Best Practices

1. **Versioning**: Use `/api/v1/` prefix for versioned APIs
2. **Pagination**: Implement pagination for list endpoints
3. **Rate limiting**: Add rate limits for public endpoints
4. **Validation**: Use Pydantic models for request/response validation
5. **Documentation**: Keep OpenAPI/Swagger docs up to date

### Security Best Practices

1. **Authentication**: Always verify JWT tokens
2. **Authorization**: Check user permissions before actions
3. **Secrets**: Never commit secrets, use environment variables
4. **SQL Injection**: Use parameterized queries (SQLAlchemy ORM)
5. **XSS**: Sanitize user inputs before rendering
6. **CORS**: Configure CORS appropriately for production
7. **Audit Logging**: Log all sensitive operations

### Agent Development Best Practices

1. **Confidence Scores**: Always include confidence in decisions
2. **Reasoning**: Explain why decisions were made
3. **Human-in-Loop**: Use `requires_approval=True` for high-risk actions
4. **Error Recovery**: Handle failures gracefully, retry with backoff
5. **Monitoring**: Log agent operations to metrics and audit log
6. **Testing**: Test agents with mock data and edge cases

### Performance Best Practices

1. **Async Operations**: Use async/await for I/O operations
2. **Parallel Execution**: Use `asyncio.gather()` for independent tasks
3. **Caching**: Cache expensive computations in Redis
4. **Database Queries**: Use select_related/joinedload to avoid N+1
5. **Background Jobs**: Use Celery for long-running tasks
6. **Monitoring**: Track performance metrics with Prometheus

---

## File Reference Guide

### Must-Read Files

**Core Architecture**:
- `src/blank_business_builder/__init__.py` - Package exports
- `src/blank_business_builder/main.py` - FastAPI app (150+ endpoints)
- `src/blank_business_builder/database.py` - ORM models
- `src/blank_business_builder/level6_agent.py` - Autonomous agents
- `src/blank_business_builder/quantum_optimizer.py` - Business ranking
- `src/blank_business_builder/expert_system.py` - Multi-domain experts

**Configuration**:
- `pyproject.toml` - Project metadata and dependencies
- `.env.example` - Required environment variables
- `docker-compose.yml` - Full stack orchestration
- `schema.sql` - Database schema

**Testing**:
- `pytest.ini` - Test configuration
- `tests/test_auth.py` - Authentication tests
- `tests/test_comprehensive_bbb.py` - Integration tests

### Feature Modules

**Location**: `src/blank_business_builder/features/`

- `ai_content_generator.py` - Content creation (blogs, emails, ads)
- `marketing_automation.py` - Multi-channel campaigns
- `ai_workflow_builder.py` - No-code workflow automation
- `white_label_platform.py` - Reseller/SaaS capabilities
- `market_research.py` - Competitive analysis
- `email_service.py` - SendGrid integration
- `social_media.py` - Social platform integrations
- `payment_processor.py` - Stripe integration

### Premium Workflows

**Location**: `src/blank_business_builder/premium_workflows/`

- `ghost_writing_agent.py` - Fiverr/Upwork automation ($50-$300/project)
- `marketing_agency_agent.py` - Digital marketing agency ($999-$2,999/mo)
- `nocode_app_agent.py` - SaaS/app builder ($999-$5,000/build)
- `quantum_optimizer.py` - Advanced optimization features

### Root-Level Scripts

**Autonomous Systems**:
- `level8_agents_dispatch.py` - Multi-agent coordination
- `mass_business_deployment_api.py` - Deploy 1M+ businesses
- `ech0_enhanced_parliament.py` - Advanced approval system
- `human_behavior_simulator.py` - Realistic behavior patterns
- `fiverr_autonomous_manager.py` - Fiverr automation
- `hive_mind_coordinator.py` - Agent orchestration

**Deployment Scripts**:
- `DEPLOY_AUTONOMOUS_BUSINESS.sh` - Deploy single business
- `DEPLOY_COMPLETE_AUTONOMOUS_SYSTEM.sh` - Full stack deployment
- `STOP_AUTONOMOUS_SYSTEM.sh` - Graceful shutdown

### Documentation Files

**Key Documentation**:
- `README.md` - Project overview
- `FEATURES.md` - Complete feature list
- `DEPLOYMENT_GUIDE.md` - Deployment instructions
- `EXPERT_SYSTEM_README.md` - Expert system guide
- `AUTONOMOUS_SYSTEM_COMPLETE_GUIDE.md` - Autonomous operations
- `PRODUCTION_READINESS_ROADMAP.md` - Production checklist
- `HUMAN_BEHAVIOR_PROTOCOLS.md` - Behavior simulation guide

---

## Troubleshooting

### Common Issues

**Issue**: Database connection fails
**Solution**: Check `DATABASE_URL` in `.env`, ensure PostgreSQL is running

**Issue**: Agent operations not executing
**Solution**: Check `ENABLE_AUTONOMOUS_MODE=true` in `.env`

**Issue**: API requests fail with 401
**Solution**: Verify JWT token is valid and not expired

**Issue**: Tests failing
**Solution**: Ensure test database is clean, check fixtures

**Issue**: Docker containers not starting
**Solution**: Check logs with `docker-compose logs -f`, verify ports not in use

### Getting Help

1. Check documentation in `/docs` directory
2. Review test files for usage examples
3. Check git commit history for recent changes
4. Review error logs in Sentry (if configured)
5. Check Prometheus metrics for system health

---

## Copyright & License

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved.

**License**: Proprietary - PATENT PENDING

This is proprietary software. All files should include the copyright header:
```python
# Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
```

---

## Changelog

**2025-11-30**: Initial CLAUDE.md creation
- Comprehensive codebase documentation
- Architecture and component descriptions
- Development workflows and best practices
- API structure and conventions
- Testing and deployment guides

---

*This document is maintained for AI assistants working with the BBB codebase. Keep it updated as the codebase evolves.*
