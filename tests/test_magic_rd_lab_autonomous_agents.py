import pytest
import sys
import os

# Ensure src is in path for imports
if 'src' not in sys.path:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from blank_business_builder.magic_rd_lab_autonomous_agents import MagicRDLabOrchestrator

def test_get_metrics_dashboard():
    """Test that get_metrics_dashboard includes the magic_rd_lab specific metrics."""
    # Instantiate the orchestrator
    orchestrator = MagicRDLabOrchestrator()

    # Manually set some metrics to ensure they are returned correctly
    orchestrator.magic_metrics.linkedin_messages_sent = 150
    orchestrator.magic_metrics.cold_calls_made = 75
    orchestrator.magic_metrics.demo_calls_scheduled = 10
    orchestrator.magic_metrics.sessions_booked = 5
    orchestrator.magic_metrics.computations_run = 20

    # Call the method
    dashboard = orchestrator.get_metrics_dashboard()

    # Assert the base metrics structure exists (at least it should be a dictionary)
    assert isinstance(dashboard, dict)

    # Assert magic_rd_lab metrics are included
    assert 'magic_rd_lab' in dashboard

    # Verify the specific metrics match what we set
    magic_metrics = dashboard['magic_rd_lab']
    assert magic_metrics['linkedin_messages_sent'] == 150
    assert magic_metrics['cold_calls_made'] == 75
    assert magic_metrics['demo_calls_scheduled'] == 10
    assert magic_metrics['sessions_booked'] == 5
    assert magic_metrics['computations_run'] == 20
    assert magic_metrics['marketing_agents'] == 2
    assert magic_metrics['sales_agents'] == 2
    assert magic_metrics['flagship_status'] == "MAXIMUM EFFORT - 2X FORCE DEPLOYED"
