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
    TWILIO_API_KEY_SID = os.getenv("TWILIO_API_KEY_SID", "")
    TWILIO_API_KEY_SECRET = os.getenv("TWILIO_API_KEY_SECRET", "")
    TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "")

    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
    
    TWITTER_CONSUMER_KEY = os.getenv("TWITTER_CONSUMER_KEY", "")
    TWITTER_CONSUMER_SECRET = os.getenv("TWITTER_CONSUMER_SECRET", "")
    TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "")

    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
    SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "noreply@betterbusinessbuilder.com")

    BUFFER_ACCESS_TOKEN = os.getenv("BUFFER_ACCESS_TOKEN", "")

    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./business_builder.db")

    # Redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-please-change-in-production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

    # Ollama / Echo
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "echo")

    # Outreach stack (Bland + Apollo + Slack + Echo private reasoning)
    BLAND_API_KEY = os.getenv("BLAND_API_KEY", "")
    BLAND_WEBHOOK_SECRET = os.getenv("BLAND_WEBHOOK_SECRET", "")
    BLAND_BASE_URL = os.getenv("BLAND_BASE_URL", "https://api.bland.ai")
    BBB_PERSONA_ID = os.getenv("BBB_PERSONA_ID", "")
    BLAND_FROM_NUMBER = os.getenv("BLAND_FROM_NUMBER", "")
    BLAND_DEFAULT_LANGUAGE = os.getenv("BLAND_DEFAULT_LANGUAGE", "en-US")
    BLAND_MAX_DURATION_MINUTES = int(os.getenv("BLAND_MAX_DURATION_MINUTES", "8"))
    BLAND_WAIT_FOR_GREETING = os.getenv("BLAND_WAIT_FOR_GREETING", "true").lower() == "true"
    BLAND_RECORD_CALLS = os.getenv("BLAND_RECORD_CALLS", "true").lower() == "true"

    APOLLO_API_KEY = os.getenv("APOLLO_API_KEY", "")
    APOLLO_BASE_URL = os.getenv("APOLLO_BASE_URL", "https://api.apollo.io")

    SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
    SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET", "")
    SLACK_CHANNEL_SALES = os.getenv("SLACK_CHANNEL_SALES", "")
    SLACK_CHANNEL_MARKETING = os.getenv("SLACK_CHANNEL_MARKETING", "")
    SLACK_CHANNEL_OPS = os.getenv("SLACK_CHANNEL_OPS", "")
    SLACK_CHANNEL_EXEC = os.getenv("SLACK_CHANNEL_EXEC", "")
    SLACK_CHANNEL_SUPPORT = os.getenv("SLACK_CHANNEL_SUPPORT", "")

    ECHO_BASE_URL = os.getenv("ECHO_BASE_URL", "")

settings = Config()


def validate_production_config():
    """Validate critical settings are not using defaults in production."""
    import os
    if os.getenv("ENVIRONMENT", "development") == "production":
        issues = []
        if settings.SECRET_KEY in ("your-secret-key-please-change-in-production", ""):
            issues.append("SECRET_KEY must be set to a secure random value")
        if not settings.DATABASE_URL or settings.DATABASE_URL.startswith("sqlite"):
            issues.append("DATABASE_URL must be a PostgreSQL connection string in production")
        if issues:
            raise RuntimeError(
                "Production configuration errors:\n" +
                "\n".join(f"  - {i}" for i in issues)
            )
