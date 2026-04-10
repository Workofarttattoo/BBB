"""
Unit tests for StripeService in blank_business_builder.payments.
"""

import sys
from unittest.mock import MagicMock, patch
import pytest

# Conditionally mock missing dependencies
try:
    import fastapi
except ImportError:
    mock_fastapi = MagicMock()
    class MockHTTPException(Exception):
        def __init__(self, status_code, detail=None):
            self.status_code = status_code
            self.detail = detail
    mock_fastapi.HTTPException = MockHTTPException
    mock_fastapi.status = MagicMock()
    mock_fastapi.status.HTTP_400_BAD_REQUEST = 400
    sys.modules['fastapi'] = mock_fastapi

try:
    import sqlalchemy
    import sqlalchemy.orm
except ImportError:
    mock_sqlalchemy = MagicMock()
    mock_sqlalchemy.orm = MagicMock()
    sys.modules['sqlalchemy'] = mock_sqlalchemy
    sys.modules['sqlalchemy.orm'] = mock_sqlalchemy.orm

from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from blank_business_builder.payments import StripeService

try:
    from fastapi import HTTPException
except ImportError:
    HTTPException = sys.modules['fastapi'].HTTPException

class TestStripeService:
    @pytest.fixture
    def mock_stripe(self):
        """Mock the stripe object in payments module."""
        with patch("blank_business_builder.payments.stripe") as mock:
            # Setup error classes
            class StripeError(Exception): pass
            class SignatureVerificationError(StripeError): pass

            mock.error.StripeError = StripeError
            mock.error.SignatureVerificationError = SignatureVerificationError
            yield mock

    def test_create_customer(self, mock_stripe):
        """Test creating a customer."""
        mock_stripe.Customer.create.return_value = {"id": "cus_123"}

        result = StripeService.create_customer("test@example.com", "Test User")

        mock_stripe.Customer.create.assert_called_once_with(
            email="test@example.com",
            name="Test User",
            metadata={}
        )
        assert result == {"id": "cus_123"}

    def test_create_customer_error(self, mock_stripe):
        """Test error handling when creating a customer."""
        mock_stripe.Customer.create.side_effect = mock_stripe.error.StripeError("API Error")

        with pytest.raises(HTTPException) as exc_info:
            StripeService.create_customer("test@example.com")

        assert exc_info.value.status_code == 400
        assert "Stripe error" in exc_info.value.detail

    def test_create_subscription(self, mock_stripe):
        """Test creating a subscription."""
        mock_stripe.Subscription.create.return_value = {"id": "sub_123"}

        result = StripeService.create_subscription(
            customer_id="cus_123",
            price_id="price_123",
            trial_days=14,
            metadata={"key": "value"}
        )

        mock_stripe.Subscription.create.assert_called_once_with(
            customer="cus_123",
            items=[{"price": "price_123"}],
            metadata={"key": "value"},
            expand=["latest_invoice.payment_intent"],
            trial_period_days=14
        )
        assert result == {"id": "sub_123"}

    def test_create_subscription_error(self, mock_stripe):
        """Test error handling when creating a subscription."""
        mock_stripe.Subscription.create.side_effect = mock_stripe.error.StripeError("API Error")

        with pytest.raises(HTTPException) as exc_info:
            StripeService.create_subscription("cus_123", "price_123")

        assert exc_info.value.status_code == 400

    def test_cancel_subscription_at_period_end(self, mock_stripe):
        """Test canceling subscription at period end."""
        mock_stripe.Subscription.modify.return_value = {"id": "sub_123", "status": "canceled"}

        result = StripeService.cancel_subscription("sub_123", at_period_end=True)

        mock_stripe.Subscription.modify.assert_called_once_with(
            "sub_123",
            cancel_at_period_end=True
        )
        assert result["status"] == "canceled"

    def test_cancel_subscription_immediately(self, mock_stripe):
        """Test canceling subscription immediately."""
        mock_stripe.Subscription.delete.return_value = {"id": "sub_123", "status": "canceled"}

        result = StripeService.cancel_subscription("sub_123", at_period_end=False)

        mock_stripe.Subscription.delete.assert_called_once_with("sub_123")
        assert result["status"] == "canceled"

    def test_create_payment_intent(self, mock_stripe):
        """Test creating a payment intent."""
        mock_stripe.PaymentIntent.create.return_value = {"id": "pi_123"}

        result = StripeService.create_payment_intent(
            amount=1000,
            currency="usd",
            customer_id="cus_123"
        )

        mock_stripe.PaymentIntent.create.assert_called_once_with(
            amount=1000,
            currency="usd",
            metadata={},
            customer="cus_123"
        )
        assert result == {"id": "pi_123"}

    def test_create_checkout_session(self, mock_stripe):
        """Test creating a checkout session."""
        mock_stripe.checkout.Session.create.return_value = {"id": "cs_123"}

        result = StripeService.create_checkout_session(
            customer_id="cus_123",
            price_id="price_123",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel"
        )

        mock_stripe.checkout.Session.create.assert_called_once_with(
            customer="cus_123",
            payment_method_types=["card"],
            line_items=[{
                "price": "price_123",
                "quantity": 1,
            }],
            mode="subscription",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
            metadata={}
        )
        assert result == {"id": "cs_123"}

    def test_create_billing_portal_session(self, mock_stripe):
        """Test creating a billing portal session."""
        mock_stripe.billing_portal.Session.create.return_value = {"url": "https://billing.stripe.com/..."}

        result = StripeService.create_billing_portal_session("cus_123", "https://example.com/return")

        mock_stripe.billing_portal.Session.create.assert_called_once_with(
            customer="cus_123",
            return_url="https://example.com/return"
        )
        assert result["url"] == "https://billing.stripe.com/..."

    def test_verify_webhook_signature(self, mock_stripe):
        """Test verifying webhook signature."""
        mock_stripe.Webhook.construct_event.return_value = {"type": "test_event"}

        result = StripeService.verify_webhook_signature(b"payload", "sig_header")

        # Verify construct_event was called.
        # Note: STRIPE_WEBHOOK_SECRET is an env var, which might be mocked or read from os.getenv.
        # Since we patch 'stripe', we can just check arguments.
        # But we need to know what secret was passed.
        # It's better to just check arguments were passed through.

        # Get the secret used in the call
        args, _ = mock_stripe.Webhook.construct_event.call_args
        assert args[0] == b"payload"
        assert args[1] == "sig_header"
        # args[2] is the secret, we don't strictly care what it is for this test as long as it's passed.

        assert result == {"type": "test_event"}

    def test_verify_webhook_signature_error(self, mock_stripe):
        """Test error handling for invalid signature."""
        mock_stripe.Webhook.construct_event.side_effect = mock_stripe.error.SignatureVerificationError("Invalid sig")

        with pytest.raises(HTTPException) as exc_info:
            StripeService.verify_webhook_signature(b"payload", "bad_sig")

        assert exc_info.value.status_code == 400
        assert "Invalid signature" in exc_info.value.detail

    def test_verify_webhook_payload_error(self, mock_stripe):
        """Test error handling for invalid payload."""
        mock_stripe.Webhook.construct_event.side_effect = ValueError("Invalid payload")

        with pytest.raises(HTTPException) as exc_info:
            StripeService.verify_webhook_signature(b"bad_payload", "sig")

        assert exc_info.value.status_code == 400
        assert "Invalid payload" in exc_info.value.detail


class TestPaymentEventHandler:
    @pytest.fixture
    def mock_db(self):
        """Mock SQLAlchemy Session."""
        return MagicMock()

    @pytest.fixture
    def mock_models(self):
        """Mock User and Subscription models to avoid database imports."""
        mock_user = MagicMock()
        mock_sub = MagicMock()
        mock_user.__name__ = "User"
        mock_sub.__name__ = "Subscription"

        # Patch the models in the module namespace so `from .database import User, Subscription`
        # gets our mocks, or we can patch sys.modules

        with patch.dict('sys.modules', {'blank_business_builder.database': MagicMock(User=mock_user, Subscription=mock_sub)}):
            yield {"User": mock_user, "Subscription": mock_sub}

    def test_handle_subscription_deleted_happy_path(self, mock_db, mock_models):
        from blank_business_builder.payments import PaymentEventHandler

        # Setup test data
        event_data = {
            "object": {
                "id": "sub_123"
            }
        }

        # Mock Subscription query
        mock_sub_query = MagicMock()
        mock_db_subscription = MagicMock()
        mock_db_subscription.user_id = 1
        mock_sub_query.filter.return_value.first.return_value = mock_db_subscription

        # Mock User query
        mock_user_query = MagicMock()
        mock_user = MagicMock()
        mock_user_query.filter.return_value.first.return_value = mock_user

        # Configure db.query side_effects to return appropriate queries
        def query_side_effect(model):
            if model == mock_models["Subscription"]:
                return mock_sub_query
            elif model == mock_models["User"]:
                return mock_user_query
            return MagicMock()

        mock_db.query.side_effect = query_side_effect

        # Call the method
        PaymentEventHandler.handle_subscription_deleted(event_data, mock_db)

        # Verify subscription was updated
        assert mock_db_subscription.status == "canceled"

        # Verify user was downgraded
        assert mock_user.subscription_tier == "free"
        assert mock_user.license_status == "trial"
        # Since trial_expires_at is dynamic, we just check it was set
        assert mock_user.trial_expires_at is not None

        # Verify db.commit was called
        mock_db.commit.assert_called_once()

    def test_handle_subscription_deleted_subscription_not_found(self, mock_db, mock_models):
        from blank_business_builder.payments import PaymentEventHandler

        event_data = {
            "object": {
                "id": "sub_not_found"
            }
        }

        mock_sub_query = MagicMock()
        mock_sub_query.filter.return_value.first.return_value = None

        def query_side_effect(model):
            if model == mock_models["Subscription"]:
                return mock_sub_query
            return MagicMock()

        mock_db.query.side_effect = query_side_effect

        PaymentEventHandler.handle_subscription_deleted(event_data, mock_db)

        # Verify db.commit was not called since no subscription was found
        mock_db.commit.assert_not_called()

    def test_handle_subscription_deleted_user_not_found(self, mock_db, mock_models):
        from blank_business_builder.payments import PaymentEventHandler

        event_data = {
            "object": {
                "id": "sub_123"
            }
        }

        mock_sub_query = MagicMock()
        mock_db_subscription = MagicMock()
        mock_db_subscription.user_id = 1
        mock_sub_query.filter.return_value.first.return_value = mock_db_subscription

        mock_user_query = MagicMock()
        mock_user_query.filter.return_value.first.return_value = None

        def query_side_effect(model):
            if model == mock_models["Subscription"]:
                return mock_sub_query
            elif model == mock_models["User"]:
                return mock_user_query
            return MagicMock()

        mock_db.query.side_effect = query_side_effect

        PaymentEventHandler.handle_subscription_deleted(event_data, mock_db)

        # Verify subscription was updated
        assert mock_db_subscription.status == "canceled"

        # Verify db.commit was called even if user was not found
        mock_db.commit.assert_called_once()
