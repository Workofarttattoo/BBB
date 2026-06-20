import sys
import os
import pytest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath('src'))
sys.modules['sqlalchemy'] = MagicMock()
sys.modules['sqlalchemy.ext.declarative'] = MagicMock()
sys.modules['sqlalchemy.orm'] = MagicMock()

if __name__ == '__main__':
    sys.exit(pytest.main(['tests/test_bbb_real_business_library.py']))
