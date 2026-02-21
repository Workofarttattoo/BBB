import asyncio
import pytest
from unittest.mock import MagicMock, patch
import sys
import os
from datetime import datetime

# Mock dependencies
mock_fastapi = MagicMock()
sys.modules['fastapi'] = mock_fastapi
sys.modules['sqlalchemy'] = MagicMock()
sys.modules['sqlalchemy.orm'] = MagicMock()
sys.modules['sqlalchemy.ext.declarative'] = MagicMock()

# Mock internal modules
mock_db_mod = MagicMock()
class Business:
    id = "id"
    user_id = "user_id"
class AgentTask:
    id = "id"
    business_id = "business_id"
    status = "status"
class MetricsHistory:
    id = "id"
    business_id = "business_id"
    timestamp = "timestamp"
mock_db_mod.Business = Business
mock_db_mod.AgentTask = AgentTask
mock_db_mod.MetricsHistory = MetricsHistory
sys.modules['blank_business_builder.database'] = mock_db_mod

mock_auth_mod = MagicMock()
sys.modules['blank_business_builder.auth'] = mock_auth_mod

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from blank_business_builder.websockets import get_agent_activity, _get_agent_activity_sync, websocket_endpoint

def test_get_agent_activity_logic():
    async def run_test():
        mock_db = MagicMock()

        # Setup mock tasks
        task1 = MagicMock()
        task1.agent_role = "developer"
        task1.task_type = "coding"
        task1.status = "in_progress"
        task1.description = "Task 1"
        task1.started_at = datetime.utcnow()

        mock_db.query().filter().all.return_value = [task1]

        # Call the async function
        result = await get_agent_activity("biz-123", mock_db)

        assert result["business_id"] == "biz-123"
        assert len(result["agents"]) == 1
        assert result["agents"][0]["role"] == "developer"
        assert result["agents"][0]["active_tasks"] == 1
        assert result["agents"][0]["current_task"]["task_type"] == "coding"

    asyncio.run(run_test())

def test_websocket_endpoint_ownership_check():
    async def run_test():
        mock_ws = MagicMock()
        mock_ws.accept = MagicMock(return_value=asyncio.Future())
        mock_ws.accept.return_value.set_result(None)
        mock_ws.close = MagicMock(return_value=asyncio.Future())
        mock_ws.close.return_value.set_result(None)
        mock_ws.send_json = MagicMock(return_value=asyncio.Future())
        mock_ws.send_json.return_value.set_result(None)

        # Mock authentication
        mock_auth_mod.AuthService.decode_token.return_value = {"sub": "user-123"}

        mock_db = MagicMock()

        # Mock business NOT found (unauthorized)
        mock_db.query().filter().first.return_value = None

        # Run the endpoint
        await websocket_endpoint(mock_ws, "biz-123", "valid-token", mock_db)

        # Verify it closed with 1008
        mock_ws.close.assert_called()
        # Find the call with code=1008
        found = False
        for call in mock_ws.close.call_args_list:
            if call.kwargs.get('code') == 1008:
                found = True
                break
        assert found

    asyncio.run(run_test())

def test_websocket_endpoint_authorized():
    async def run_test():
        mock_ws = MagicMock()
        mock_ws.accept = MagicMock(return_value=asyncio.Future())
        mock_ws.accept.return_value.set_result(None)
        mock_ws.close = MagicMock(return_value=asyncio.Future())
        mock_ws.close.return_value.set_result(None)
        mock_ws.send_json = MagicMock(return_value=asyncio.Future())
        mock_ws.send_json.return_value.set_result(None)

        # Mock authentication
        mock_auth_mod.AuthService.decode_token.return_value = {"sub": "user-123"}

        mock_db = MagicMock()
        mock_business = MagicMock()
        mock_db.query().filter().first.return_value = mock_business

        # Mock websocket_update_loop to return immediately
        with patch('blank_business_builder.websockets.websocket_update_loop', return_value=asyncio.Future()) as mock_loop:
            mock_loop.return_value.set_result(None)
            await websocket_endpoint(mock_ws, "biz-123", "valid-token", mock_db)

        # Verify manager.connect was called (implicitly via effect)
        # and initial data was sent
        mock_ws.send_json.assert_called()
        args, kwargs = mock_ws.send_json.call_args
        assert args[0]["type"] == "connected"

    asyncio.run(run_test())
