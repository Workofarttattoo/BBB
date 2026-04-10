# Better Business Builder - Deployment Guide

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Production Deployment](#production-deployment)
4. [Database Setup](#database-setup)
5. [Environment Configuration](#environment-configuration)
6. [Testing](#testing)
7. [Monitoring & Maintenance](#monitoring--maintenance)

---

## Prerequisites

### Required Services

- **PostgreSQL 14+** - Primary database
- **Redis 6+** - Caching and session storage (optional)
- **Python 3.11+** - Application runtime
- **Node.js 18+** - Frontend build tools

### External API Accounts

- **Stripe** - Payment processing (https://stripe.com)
- **SendGrid** - Email delivery (https://sendgrid.com)
- **OpenAI** - AI content generation (https://openai.com)
- **Buffer** - Social media scheduling (https://buffer.com)
- **Auth0** (Optional) - Enterprise authentication (https://auth0.com)

---

## Local Development Setup

### 1. Clone and Install

```bash
git clone <repository-url>
cd Blank_Business_Builder

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup

```bash
# Create PostgreSQL database
createdb better_business_builder

# Run migrations
alembic upgrade head

# Or use the SQL schema directly
psql better_business_builder < schema.sql
```

### 3. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### 4. Run Development Server

```bash
# Start FastAPI server
cd src/blank_business_builder
python main.py

# Or using uvicorn directly
uvicorn blank_business_builder.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/blank_business_builder --cov-report=html

# Open coverage report
open htmlcov/index.html
```

---

## Production Deployment

### Option 1: Traditional VPS (DigitalOcean, AWS EC2, Linode)

#### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.11 python3.11-venv postgresql redis-server nginx

# Create application user
sudo useradd -m -s /bin/bash bbbuser
sudo su - bbbuser
```

#### 2. Application Deployment

```bash
# Clone repository
git clone <repository-url> /home/bbbuser/app
cd /home/bbbuser/app

# Setup virtual environment
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Update with production values
```

#### 3. Database Setup

```bash
# Create production database
sudo -u postgres createdb better_business_builder
sudo -u postgres createuser bbbuser
sudo -u postgres psql -c "ALTER USER bbbuser WITH PASSWORD 'secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE better_business_builder TO bbbuser;"

# Run migrations
alembic upgrade head
```

#### 4. Systemd Service

Create `/etc/systemd/system/bbb.service`:

```ini
[Unit]
Description=Better Business Builder FastAPI Service
After=network.target postgresql.service

[Service]
Type=notify
User=bbbuser
Group=bbbuser
WorkingDirectory=/home/bbbuser/app
Environment="PATH=/home/bbbuser/app/venv/bin"
ExecStart=/home/bbbuser/app/venv/bin/uvicorn blank_business_builder.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable bbb
sudo systemctl start bbb
sudo systemctl status bbb
```

#### 5. Nginx Reverse Proxy

Create `/etc/nginx/sites-available/bbb`:

```nginx
server {
    listen 80;
    server_name betterbusinessbuilder.com www.betterbusinessbuilder.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support (if needed)
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

```bash
# Enable site and restart Nginx
sudo ln -s /etc/nginx/sites-available/bbb /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 6. SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d betterbusinessbuilder.com -d www.betterbusinessbuilder.com

# Auto-renewal is configured automatically
sudo certbot renew --dry-run
```

---

### Option 2: Docker Deployment

#### 1. Create Dockerfile

Already exists at `/Users/noone/Blank_Business_Builder/Dockerfile`

#### 2. Docker Compose Setup

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://bbbuser:password@db:5432/better_business_builder
      - REDIS_URL=redis://redis:6379/0
    env_file:
      - .env
    depends_on:
      - db
      - redis
    restart: always

  db:
    image: postgres:14
    environment:
      - POSTGRES_DB=better_business_builder
      - POSTGRES_USER=bbbuser
      - POSTGRES_PASSWORD=secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

  redis:
    image: redis:7-alpine
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web
    restart: always

volumes:
  postgres_data:
```

#### 3. Deploy with Docker

```bash
# Build and start services
docker-compose up -d

# Run migrations
docker-compose exec web alembic upgrade head

# View logs
docker-compose logs -f web

# Stop services
docker-compose down
```

---

### Option 3: Cloud Platform Deployment

#### Heroku

```bash
# Install Heroku CLI
# https://devcenter.heroku.com/articles/heroku-cli

# Create Heroku app
heroku create better-business-builder

# Add PostgreSQL addon
heroku addons:create heroku-postgresql:hobby-dev

# Add Redis addon (optional)
heroku addons:create heroku-redis:hobby-dev

# Set environment variables
heroku config:set JWT_SECRET_KEY=your-secret-key
heroku config:set STRIPE_SECRET_KEY=your-stripe-key
# ... (set all other environment variables)

# Deploy
git push heroku main

# Run migrations
heroku run alembic upgrade head

# Open application
heroku open
```

#### AWS Elastic Beanstalk

```bash
# Install EB CLI
pip install awsebcli

# Initialize EB application
eb init -p python-3.11 better-business-builder

# Create environment
eb create production-env

# Deploy
eb deploy

# Open application
eb open
```

---

## Database Setup

### Creating Initial Migration

```bash
# Initialize Alembic (already done)
alembic init alembic

# Generate initial migration
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head
```

### Database Backups

```bash
# Backup database
pg_dump better_business_builder > backup_$(date +%Y%m%d).sql

# Restore database
psql better_business_builder < backup_20250115.sql

# Automated backups (add to crontab)
0 2 * * * /usr/bin/pg_dump better_business_builder | gzip > /backups/bbb_$(date +\%Y\%m\%d).sql.gz
```

---

## Environment Configuration

### Required Environment Variables

```bash
# Security
JWT_SECRET_KEY=<generate-with-openssl-rand-hex-32>
STRIPE_WEBHOOK_SECRET=<from-stripe-dashboard>

# Database
DATABASE_URL=postgresql://user:password@host:5432/database

# APIs
OPENAI_API_KEY=sk-...
SENDGRID_API_KEY=SG....
STRIPE_SECRET_KEY=sk_live_...
```

### Generating Secure Keys

```bash
# Generate JWT secret
openssl rand -hex 32

# Generate random password
openssl rand -base64 32
```

---

## Testing

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_auth.py

# Specific test
pytest tests/test_auth.py::TestAuthentication::test_register_user

# With coverage
pytest --cov=src/blank_business_builder --cov-report=html

# Integration tests only
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

### Test Coverage Goals

- **Minimum**: 70% coverage
- **Target**: 85% coverage
- **Critical paths**: 95%+ coverage (auth, payments)

---

## Monitoring & Maintenance

### Health Checks

```bash
# Application health
curl https://betterbusinessbuilder.com/health

# Database connection
psql $DATABASE_URL -c "SELECT 1;"

# Redis connection
redis-cli ping
```

### Logging

```bash
# Application logs (systemd)
sudo journalctl -u bbb -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```

### Performance Monitoring

- **Sentry** - Error tracking (configured via SENTRY_DSN)
- **Prometheus** - Metrics collection
- **Grafana** - Visualization dashboards

### Maintenance Tasks

```bash
# Database vacuum (weekly)
psql $DATABASE_URL -c "VACUUM ANALYZE;"

# Clear Redis cache
redis-cli FLUSHDB

# Update dependencies
pip list --outdated
pip install -U <package>

# Security updates
sudo apt update && sudo apt upgrade -y
```

---

## Scaling Strategies

### Horizontal Scaling

1. **Load Balancer**: Use Nginx or AWS ALB
2. **Multiple App Instances**: Scale web service replicas
3. **Database Read Replicas**: For read-heavy workloads
4. **Redis Cluster**: For distributed caching

### Vertical Scaling

- Start: 1 CPU, 2GB RAM ($10-20/month)
- Growth: 2 CPU, 4GB RAM ($40-60/month)
- Scale: 4 CPU, 8GB RAM ($80-120/month)

---

## Troubleshooting

### Common Issues

#### Database Connection Errors

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Verify connection string
psql $DATABASE_URL -c "SELECT version();"

# Check firewall rules
sudo ufw status
```

#### Stripe Webhooks Not Working

1. Verify webhook secret in Stripe dashboard
2. Check endpoint URL is publicly accessible
3. Test with Stripe CLI: `stripe listen --forward-to localhost:8000/api/webhooks/stripe`

#### High Memory Usage

```bash
# Check processes
top
htop

# Reduce workers in uvicorn
uvicorn main:app --workers 2

# Enable connection pooling
# Add to DATABASE_URL: ?pool_size=10&max_overflow=20
```

---

## Security Checklist

- [ ] Change all default passwords
- [ ] Use strong JWT_SECRET_KEY
- [ ] Enable HTTPS/SSL
- [ ] Configure CORS properly
- [ ] Enable rate limiting
- [ ] Set up firewall rules
- [ ] Regular security updates
- [ ] Database backups configured
- [ ] Environment variables secured
- [ ] Stripe webhook signature verification

---

## Support & Resources

- **Documentation**: https://docs.betterbusinessbuilder.com
- **API Reference**: https://api.betterbusinessbuilder.com/docs
- **Support Email**: support@betterbusinessbuilder.com
- **Status Page**: https://status.betterbusinessbuilder.com

---

**Deployment Checklist Complete** ✅

Your Better Business Builder is now production-ready!
