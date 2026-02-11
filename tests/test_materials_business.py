"""
Tests for Materials & Legal Business Logic
"""

import pytest
import sys
import os
import asyncio

# Ensure src is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from blank_business_builder.materials_business import MaterialsBusiness

@pytest.mark.asyncio
async def test_materials_business_initialization():
    """Test that the business system initializes correctly."""
    business = MaterialsBusiness()
    assert business.expert_system is not None
    assert business.mcp_server_running is False

@pytest.mark.asyncio
async def test_predict_materials():
    """Test materials science prediction."""
    business = MaterialsBusiness()

    # Test Student Query
    response = await business.predict_materials("What is Graphene?", client_type="student")
    assert "prediction" in response
    assert "Graphene" in response["prediction"] or "carbon" in response["prediction"]
    assert response["analysis"] == "Upgrade to Enterprise for deep analysis."

    # Test Enterprise Query
    ent_response = await business.predict_materials("What is Graphene?", client_type="enterprise")
    assert "ENTERPRISE ANALYSIS" in ent_response["analysis"]

@pytest.mark.asyncio
async def test_predict_legal():
    """Test legal prediction (TheGavl)."""
    business = MaterialsBusiness()

    response = await business.predict_legal("Are smart contracts binding?")
    assert "legal_opinion" in response
    assert "smart contracts" in response["legal_opinion"].lower() or "binding" in response["legal_opinion"].lower()
    assert "disclaimer" in response

def test_license_software():
    """Test software licensing issuance."""
    business = MaterialsBusiness()

    client_name = "TestCorp"
    response = business.license_software(client_name, "enterprise")

    assert response["status"] == "success"
    assert response["license_details"]["client_name"] == client_name
    assert response["license_details"]["key"].startswith("LIC-ENTERPRISE-")
    assert client_name in business.active_licenses

@pytest.mark.asyncio
async def test_mcp_server_startup():
    """Test MCP server startup simulation."""
    business = MaterialsBusiness()

    response = await business.start_mcp_server(port=9090)
    assert response["status"] == "running"
    assert response["port"] == 9090
    assert business.mcp_server_running is True

    # Test starting again
    response_2 = await business.start_mcp_server()
    assert response_2 is None  # Should return None/log warning if already running
