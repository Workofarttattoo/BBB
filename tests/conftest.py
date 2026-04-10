"""
BBB Test Configuration — shared fixtures and sys.modules protection.
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved.
"""
import os, sys, pytest

SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_bbb.db")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_placeholder")
os.environ.setdefault("SENDGRID_API_KEY", "SG.test_placeholder")
os.environ.setdefault("TWILIO_ACCOUNT_SID", "AC_test_placeholder")
os.environ.setdefault("TWILIO_AUTH_TOKEN", "test_auth_token")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-placeholder")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")

# Cache real packages before any test file can stomp them with MagicMock
_REAL = {}
for _p in ("fastapi", "requests", "anthropic", "stripe"):
    try:
        __import__(_p)
        _REAL[_p] = sys.modules[_p]
    except ImportError:
        pass

def _restore():
    for n, m in _REAL.items():
        if sys.modules.get(n) is not m:
            sys.modules[n] = m
        for k in list(sys.modules):
            if k.startswith(f"{n}.") and not hasattr(sys.modules[k], "__file__") and not hasattr(sys.modules[k], "__path__"):
                del sys.modules[k]

def pytest_pycollect_makemodule(module_path, parent):
    _restore()

def pytest_collectreport(report):
    _restore()

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"
