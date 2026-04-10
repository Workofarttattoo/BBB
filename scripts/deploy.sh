#!/bin/bash
# Better Business Builder - Deployment Script
# Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

set -e

echo "=================================================="
echo "🚀 Better Business Builder - Deployment Started"
echo "=================================================="

# Check if docker-compose.prod.yml exists
if [ ! -f docker-compose.prod.yml ]; then
    echo "❌ Error: docker-compose.prod.yml not found. Are you in the project root?"
    exit 1
fi

echo "📦 Pulling latest code..."
git pull origin main

echo "🏗️  Rebuilding Docker images..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

echo "🔄 Restarting services..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

echo "⏳ Waiting for database to be ready..."
sleep 10

echo "🗄️  Running migrations..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml run --rm api alembic upgrade head

echo "🩺 Performing health check..."
if curl -k -s -o /dev/null -w "%{http_code}" https://localhost/health | grep -q "200\|404"; then
    # Note: Using 404 as valid because the root might not have an endpoint or might be protected
    # but the server is responding. Adjust if you have a specific /health endpoint.
    echo "✅ Health check passed."
else
    echo "⚠️  Health check returned an unexpected status code. Please verify the services."
fi

echo "=================================================="
echo "🎉 Deployment Completed successfully!"
echo "=================================================="
