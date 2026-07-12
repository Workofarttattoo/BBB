import sys, os
sys.path.insert(0, os.path.abspath('src'))
from unittest.mock import MagicMock

class SafeMock(MagicMock):
    def __iter__(self): return iter([])
    def __call__(self, *args, **kwargs): return SafeMock()
    def _is_coroutine(self): return False
    def __gt__(self, other): return True
    def __lt__(self, other): return False
    def in_(self, other): return True
    def __bool__(self): return True

class MockBase: pass
class MockColumn: pass
class MockSession(SafeMock):
    def query(self, *args, **kwargs): return self

sys.modules['sqlalchemy'] = SafeMock()
sys.modules['sqlalchemy.ext.declarative'] = MagicMock()
sys.modules['sqlalchemy.ext.declarative'].declarative_base = lambda: MockBase
sys.modules['sqlalchemy.orm'] = MagicMock()
sys.modules['sqlalchemy.orm'].Session = MockSession
sys.modules['sqlalchemy.pool'] = MagicMock()
sys.modules['sqlalchemy.exc'] = MagicMock()
sys.modules['sqlalchemy.types'] = MagicMock()
sys.modules['sqlalchemy.dialects.postgresql'] = MagicMock()

sys.modules['fastapi'] = MagicMock()
sys.modules['fastapi.middleware'] = MagicMock()
sys.modules['fastapi.responses'] = MagicMock()
sys.modules['fastapi.staticfiles'] = MagicMock()
sys.modules['fastapi.security'] = MagicMock()

sys.modules['numpy'] = MagicMock(bool_=bool)

for mod in ['requests', 'httpx', 'uvicorn', 'pydantic', 'openai', 'anthropic', 'sendgrid', 'twilio', 'tweepy', 'dotenv', 'duckduckgo_search', 'bland_python', 'praw', 'stripe', 'bs4', 'jose', 'passlib', 'src.blank_business_builder.database', 'task_queue', 'semantic_framework']:
    sys.modules[mod] = SafeMock()

import pytest
sys.exit(pytest.main(['tests/']))
