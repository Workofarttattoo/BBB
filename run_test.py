import sys, os
from unittest.mock import MagicMock
sys.path.insert(0, os.path.abspath('src'))

# Mocking all the required dependencies to run a local test in isolated environment
sys.modules['fastapi'] = MagicMock()
sys.modules['sqlalchemy'] = MagicMock()
sys.modules['sqlalchemy.orm'] = MagicMock()
sys.modules['sqlalchemy.ext.declarative'] = MagicMock()
sys.modules['pydantic'] = MagicMock()
sys.modules['openai'] = MagicMock()
sys.modules['stripe'] = MagicMock()

from src.blank_business_builder.level6_agent import Level6Agent, Business
print("Imported successfully")
