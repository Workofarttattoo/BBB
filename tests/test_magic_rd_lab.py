"""
Tests for Magic R&D Lab Business Logic
"""
import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from decimal import Decimal

# Add src to path just in case, typically pytest handles this if run from root
import sys
import os

# Ensure src is in path for imports
if 'src' not in sys.path:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from blank_business_builder.magic_rd_lab import MagicRDLab, RentalPackage, Customer, RDSession, PACKAGE_PRICING


class TestMagicRDLab:

    @pytest.fixture
    def lab(self):
        """Fixture for MagicRDLab instance."""
        return MagicRDLab()

    @pytest.fixture
    def customer(self, lab):
        """Fixture for a created customer."""
        return lab.create_customer("Test User", "Test Corp", "test@example.com")

    @pytest.fixture
    def session(self, lab, customer):
        """Fixture for a booked session."""
        return lab.book_session(
            customer.customer_id,
            RentalPackage.FEW_HOURS,
            "Test Project"
        )

    def test_create_customer(self, lab):
        """Test customer creation logic."""
        customer = lab.create_customer("John Doe", "ACME Inc", "john@acme.com")

        assert customer.customer_id.startswith("CUST")
        assert customer.name == "John Doe"
        assert customer.company == "ACME Inc"
        assert customer.email == "john@acme.com"
        assert customer.referral_code == f"RDL-{customer.customer_id}"
        assert customer.customer_id in lab.customers
        assert len(lab.customers) == 1

    def test_book_session_success(self, lab, customer):
        """Test successful session booking."""
        package = RentalPackage.FULL_DAY
        pricing = PACKAGE_PRICING[package]

        session = lab.book_session(
            customer.customer_id,
            package,
            "Big AI Training"
        )

        # Verify session details
        assert session.session_id.startswith("SES")
        assert session.customer_name == customer.name
        assert session.customer_email == customer.email
        assert session.package == package
        assert session.project_description == "Big AI Training"
        assert session.amount_paid == pricing["price"]
        assert session.status == "active"

        # Verify customer updates
        assert customer.sessions_count == 1
        assert customer.total_spent == pricing["price"]

        # Verify revenue update
        assert lab.revenue == pricing["price"]

        # Verify expiration calculation (approximate)
        expected_expiry = session.started_at + timedelta(hours=pricing["hours"])
        assert abs((session.expires_at - expected_expiry).total_seconds()) < 1.0

    def test_book_session_invalid_customer(self, lab):
        """Test booking with invalid customer ID."""
        with pytest.raises(ValueError, match="Customer INVALID not found"):
            lab.book_session("INVALID", RentalPackage.FEW_HOURS, "Project")

    def test_run_computation_success(self, lab, session):
        """Test running computation successfully."""

        async def run_test():
            # Mock asyncio.sleep to avoid delay
            with patch('asyncio.sleep', new_callable=MagicMock) as mock_sleep:
                # Mock sleep to return immediately (it's awaited so returns a coroutine or we patch it to be async-compatible if needed,
                # but asyncio.sleep is a coroutine function. Mocking it with a coroutine or just making sure await works is key.
                # Since we are in async context, patching with an async mock is best.
                mock_sleep.return_value = None  # In Python 3.8+ AsyncMock is available, or use a helper.
                # But typically patching asyncio.sleep with a strict mock might fail if not configured as async.
                # Let's try to just patch it to return a done future or use AsyncMock if available.
                # Simpler: just patch it to return None, as await None is not valid,
                # await requires an awaitable.
                # So we need a future.
                f = asyncio.Future()
                f.set_result(None)
                mock_sleep.return_value = f

                result = await lab.run_computation(session.session_id, "Calculate Pi")

                assert result["status"] == "completed"
                assert result["task"] == "Calculate Pi"
                assert "computation_time" in result

                # Verify session updates
                assert len(session.results) == 1
                assert session.results[0] == result
                # 2.0 seconds / 60 = 0.0333 hours
                assert session.hours_used > 0
                assert session.hours_used == pytest.approx(2.0/60)

        # Run the async test wrapper
        asyncio.run(run_test())

    def test_run_computation_invalid_session(self, lab):
        """Test running computation with invalid session ID."""
        async def run_test():
            with pytest.raises(ValueError, match="Session INVALID not found"):
                await lab.run_computation("INVALID", "Task")

        asyncio.run(run_test())

    def test_run_computation_expired_session(self, lab, session):
        """Test running computation on expired session."""
        # Manually expire the session
        session.expires_at = datetime.now() - timedelta(hours=1)

        async def run_test():
            with pytest.raises(ValueError, match=f"Session {session.session_id} has expired"):
                await lab.run_computation(session.session_id, "Task")

            # Verify status update
            assert session.status == "expired"

        asyncio.run(run_test())

    def test_get_session_status(self, lab, session):
        """Test retrieving session status."""
        status = lab.get_session_status(session.session_id)

        assert status["session_id"] == session.session_id
        assert status["customer"] == session.customer_name
        assert status["package"] == session.package.value
        assert status["status"] == session.status
        assert status["hours_purchased"] == PACKAGE_PRICING[session.package]["hours"]
        assert "time_remaining_hours" in status

    def test_get_customer_dashboard(self, lab, customer, session):
        """Test customer dashboard data aggregation."""
        # Add another completed session
        completed_session = lab.book_session(
            customer.customer_id,
            RentalPackage.FEW_HOURS,
            "Completed Project"
        )
        completed_session.status = "completed"

        dashboard = lab.get_customer_dashboard(customer.customer_id)

        assert dashboard["customer_id"] == customer.customer_id
        assert dashboard["name"] == customer.name
        assert dashboard["sessions"]["total"] == 2
        assert dashboard["sessions"]["active"] == 1
        assert dashboard["sessions"]["completed"] == 1

        # Verify total spent calculation
        expected_spent = PACKAGE_PRICING[RentalPackage.FEW_HOURS]["price"] * 2
        assert float(dashboard["total_spent"]) == float(expected_spent)

    def test_get_business_metrics(self, lab, customer):
        """Test business metrics calculation."""
        # Book a few sessions
        lab.book_session(customer.customer_id, RentalPackage.FEW_HOURS, "P1")
        lab.book_session(customer.customer_id, RentalPackage.FULL_DAY, "P2")

        metrics = lab.get_business_metrics()

        assert metrics["total_sessions"] == 2
        assert metrics["total_customers"] == 1

        expected_revenue = (
            PACKAGE_PRICING[RentalPackage.FEW_HOURS]["price"] +
            PACKAGE_PRICING[RentalPackage.FULL_DAY]["price"]
        )
        assert metrics["total_revenue"] == float(expected_revenue)

        assert metrics["package_distribution"][RentalPackage.FEW_HOURS.value] == 1
        assert metrics["package_distribution"][RentalPackage.FULL_DAY.value] == 1

    def test_get_pricing_info(self, lab):
        """Test pricing info structure."""
        info = lab.get_pricing_info()

        assert "packages" in info
        assert len(info["packages"]) == 3
        assert "capabilities" in info
        assert "guarantee" in info
