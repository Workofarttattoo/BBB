import pytest
from unittest.mock import MagicMock, patch
import sys

# Mock missing dependencies to avoid needing to pip install everything
mock_duckduckgo = MagicMock()
sys.modules['duckduckgo_search'] = mock_duckduckgo

from src.blank_business_builder.sales_engineer import SalesEngineer
from src.blank_business_builder.semantic_framework import Lead, Person, Organization

def test_process_leads_empty():
    core_mock = MagicMock()
    engineer = SalesEngineer(core_mock)

    with patch.object(engineer, 'qualify') as mock_qualify, \
         patch.object(engineer, 'engage') as mock_engage:

        engineer.process_leads([])

        mock_qualify.assert_not_called()
        mock_engage.assert_not_called()

def test_process_leads_routing():
    core_mock = MagicMock()
    engineer = SalesEngineer(core_mock)

    lead_high_score = Lead(id="1")
    lead_low_score = Lead(id="2")

    def mock_qualify_side_effect(lead):
        if lead.id == "1":
            lead.score = 80
        else:
            lead.score = 50

    with patch.object(engineer, 'qualify', side_effect=mock_qualify_side_effect) as mock_qualify, \
         patch.object(engineer, 'engage') as mock_engage:

        engineer.process_leads([lead_high_score, lead_low_score])

        assert mock_qualify.call_count == 2
        mock_engage.assert_called_once_with(lead_high_score)

def test_process_leads_integration_with_qualify():
    core_mock = MagicMock()
    engineer = SalesEngineer(core_mock)

    # Qualified lead: SaaS (20) + CTO (20) + Base (50) = 90
    org1 = Organization(name="Tech Inc", industry="SaaS")
    person1 = Person(name="Alice", role="CTO")
    lead_qualified = Lead(id="1", organization=org1, person=person1)

    # Unqualified lead: missing organization/person -> score = 0
    lead_unqualified = Lead(id="2")

    with patch.object(engineer, 'engage') as mock_engage:
        engineer.process_leads([lead_qualified, lead_unqualified])

        assert lead_qualified.score >= 70
        assert lead_qualified.status == "Qualified"

        assert lead_unqualified.score < 70
        assert lead_unqualified.status == "Disqualified"

        mock_engage.assert_called_once_with(lead_qualified)
