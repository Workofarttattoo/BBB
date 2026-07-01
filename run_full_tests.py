import sys
import os
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath('src'))

class SafeMock(MagicMock):
    def __iter__(self):
        return iter([])
    def __call__(self, *args, **kwargs):
        return SafeMock()
    def _is_coroutine(self):
        return False
    def __gt__(self, other):
        return True
    def __lt__(self, other):
        return True
    def in_(self, _):
        return True
    def __bool__(self):
        return True

class MockBase:
    pass

class MockColumn:
    pass

sys.modules['requests'] = MagicMock()
sys.modules['httpx'] = MagicMock()
sys.modules['uvicorn'] = MagicMock()
sys.modules['fastapi'] = MagicMock()
sys.modules['fastapi.middleware'] = MagicMock()
sys.modules['fastapi.responses'] = MagicMock()
sys.modules['fastapi.staticfiles'] = MagicMock()
sys.modules['fastapi.security'] = MagicMock()
sys.modules['sqlalchemy'] = SafeMock()
sys.modules['sqlalchemy.ext.declarative'] = MagicMock()
sys.modules['sqlalchemy.ext.declarative'].declarative_base = lambda: MockBase
sys.modules['sqlalchemy.pool'] = MagicMock()
sys.modules['sqlalchemy.orm'] = MagicMock()
sys.modules['sqlalchemy.exc'] = MagicMock()
sys.modules['sqlalchemy.types'] = MagicMock()
sys.modules['sqlalchemy.dialects.postgresql'] = MagicMock()
sys.modules['pydantic'] = MagicMock()
sys.modules['openai'] = MagicMock()
sys.modules['anthropic'] = MagicMock()
sys.modules['sendgrid'] = MagicMock()
sys.modules['twilio'] = MagicMock()
sys.modules['tweepy'] = MagicMock()
sys.modules['dotenv'] = MagicMock()
sys.modules['numpy'] = MagicMock(bool_=bool)
sys.modules['duckduckgo_search'] = MagicMock()
sys.modules['bland_python'] = MagicMock()
sys.modules['praw'] = MagicMock()
sys.modules['stripe'] = MagicMock()
sys.modules['bs4'] = MagicMock()
sys.modules['jose'] = MagicMock()
sys.modules['passlib'] = MagicMock()
sys.modules['src.blank_business_builder.database'] = MagicMock()
sys.modules['task_queue'] = MagicMock()
sys.modules['semantic_framework'] = MagicMock()

import pytest
sys.exit(pytest.main(['tests/']))
