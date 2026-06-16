#!/bin/bash
/home/jules/.local/share/pipx/venvs/pytest/bin/python -c "
import sys, os
from unittest.mock import MagicMock
sys.modules['numpy'] = MagicMock(bool_=bool)
sys.modules['fastapi'] = MagicMock()
sys.modules['fastapi.testclient'] = MagicMock()
sys.path.insert(0, os.path.abspath('src'))
import pytest
pytest.main(['tests/test_hive_mind_qulab.py'])
"
