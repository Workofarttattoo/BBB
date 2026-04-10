#!/usr/bin/env bash
# Better Business Builder — Production Deploy Script
# Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved.
#
# Usage: ./scripts/deploy.sh
# Steps: pull → migrate → rebuild → restart → health check

set -euo pipefail

COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"
HEALTH_URL="${HEALTH_URL:-http://localhost:8000/health}"
MAX_RETRIES=15
RETRY_INTERVAL=4

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${GREEN}[deploy]${NC} $*"; }
warn()  { echo -e "${YELLOW}[deploy]${NC} $*"; }
error() { echo -e "${RED}[deploy]${NC} $*" >&2; }

# ── Step 1: Pull latest code ────────────────────────────────────────────────
info "Pulling latest code..."
git pull --ff-only origin main

# ── Step 2: Rebuild images ──────────────────────────────────────────────────
info "Rebuilding Docker images..."
$COMPOSE build --pull

# ── Step 3: Run database migrations ─────────────────────────────────────────
info "Running database migrations..."
$COMPOSE run --rm api alembic upgrade head

# ── Step 4: Restart services ────────────────────────────────────────────────
info "Restarting services..."
$COMPOSE up -d --remove-orphans

# ── Step 5: Health check ────────────────────────────────────────────────────
info "Waiting for API to become healthy..."
for i in $(seq 1 $MAX_RETRIES); do
    if curl -sf "$HEALTH_URL" > /dev/null 2>&1; then
        info "✅ Health check passed (attempt $i/$MAX_RETRIES)"
        break
    fi
    if [ "$i" -eq "$MAX_RETRIES" ]; then
        error "❌ Health check failed after $MAX_RETRIES attempts"
        warn "Dumping API logs:"
        $COMPOSE logs --tail=40 api
        exit 1
    fi
    warn "Attempt $i/$MAX_RETRIES — retrying in ${RETRY_INTERVAL}s..."
    sleep "$RETRY_INTERVAL"
done

# ── Summary ─────────────────────────────────────────────────────────────────
info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
info "Deploy complete! Services running:"
$COMPOSE ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
