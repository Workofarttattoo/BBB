FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Environment variables
ENV DATABASE_URL=postgresql://user:password@db:5432/flowstate
ENV REDIS_URL=redis://redis:6379
ENV SUPABASE_URL=https://cszoklkfdszqsxhufhhj.supabase.co
ENV STRIPE_SECRET_KEY=sk_live_...

# Run application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
