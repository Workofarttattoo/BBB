"""
Configuration settings for Blank Business Builder.
Loads environment variables from .env file.
"""

import os
from pathlib import Path

# Try to load .env file
env_path = Path(__file__).resolve().parent.parent.parent / '.env'

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=env_path)
except ImportError:
    # Fallback: Manual .env parsing
    if env_path.exists():
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        # Remove quotes if present
                        value = value.strip('"').strip("'")
                        os.environ.setdefault(key.strip(), value)
        except Exception as e:
            print(f"Warning: Could not parse .env file: {e}")

class Config:
    # API Keys & Integrations
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "")

    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")

    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
    SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "noreply@betterbusinessbuilder.com")

    BUFFER_ACCESS_TOKEN = os.getenv("BUFFER_ACCESS_TOKEN", "")

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./business_builder.db")

    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-please-change-in-production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

    # Ollama / Echo
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "echo")

settings = Config()
