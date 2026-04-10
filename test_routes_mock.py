import sys
from unittest.mock import MagicMock

class MockModule(MagicMock):
    @classmethod
    def __getattr__(cls, name):
        return MagicMock()

sys.modules['fastapi'] = MockModule()
sys.modules['fastapi.security'] = MockModule()
sys.modules['fastapi.middleware.cors'] = MockModule()
sys.modules['fastapi.responses'] = MockModule()
sys.modules['sqlalchemy'] = MockModule()
sys.modules['sqlalchemy.orm'] = MockModule()
sys.modules['sqlalchemy.ext.declarative'] = MockModule()
sys.modules['sqlalchemy.types'] = MockModule()
sys.modules['sqlalchemy.dialects.postgresql'] = MockModule()
sys.modules['uvicorn'] = MockModule()
sys.modules['pydantic'] = MockModule()
sys.modules['email_validator'] = MockModule()
sys.modules['passlib'] = MockModule()
sys.modules['passlib.context'] = MockModule()
sys.modules['jose'] = MockModule()
sys.modules['jose.jwt'] = MockModule()
sys.modules['jwt'] = MockModule()
sys.modules['stripe'] = MockModule()
sys.modules['redis'] = MockModule()
sys.modules['prometheus_client'] = MockModule()
sys.modules['websockets'] = MockModule()
sys.modules['httpx'] = MockModule()
sys.modules['openai'] = MockModule()

try:
    from src.blank_business_builder.api_features import router as features_router
    from src.blank_business_builder.api_premium import router as premium_router
    from src.blank_business_builder.main import app
    print("Feature routes import successful.")
    print("Premium routes import successful.")
    print("Main app import successful.")
except Exception as e:
    import traceback
    traceback.print_exc()
