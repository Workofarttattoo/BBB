"""
Better Business Builder - Stripe Payment Processing
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""
import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

try:
    import stripe  # type: ignore
except ImportError:  # pragma: no cover
    class _StripeUnavailableError(Exception):
        """Raised when the Stripe SDK is not installed."""

    class _StripeUnavailableSignatureError(_StripeUnavailableError):
        """Raised when webhook signature verification is unavailable."""

    class _StubResource:
        @classmethod
        def create(cls, *args, **kwargs):
            raise _StripeUnavailableError("Stripe SDK not installed.")

        @classmethod
        def modify(cls, *args, **kwargs):
            raise _StripeUnavailableError("Stripe SDK not installed.")

        @classmethod
        def delete(cls, *args, **kwargs):
            raise _StripeUnavailableError("Stripe SDK not installed.")

    class _StubWebhook:
        @staticmethod
        def construct_event(*args, **kwargs):
            raise _StripeUnavailableSignatureError("Stripe SDK not installed.")

    stripe = type(
        "stripe",
        (),
        {
            "api_key": "",
            "Customer": _StubResource,
            "Subscription": _StubResource,
            "PaymentIntent": _StubResource,
            "error": type(
                "error",
                (),
                {
                    "StripeError": _StripeUnavailableError,
                    "SignatureVerificationError": _StripeUnavailableSignatureError,
                },
            ),
            "checkout": type("checkout", (), {"Session": _StubResource}),
            "billing_portal": type("billing_portal", (), {"Session": _StubResource}),
            "Webhook": _StubWebhook,
        },
    )()

# Configure Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")


class StripeService:
    """Stripe payment processing service."""

    # Subscription plans (prices in cents)
    PLANS = {
        "starter": {
            "name": "Starter",
            "price": 29900,  # $299/month
            "interval": "month",
            "features": [
                "Up to 3 active businesses",
                "30 campaigns/month",
                "500 AI requests/month",
                "100 social posts/month",
                "10 email campaigns/month",
                "Core automation features"
            ]
        },
        "pro": {
            "name": "Pro",
            "price": 79900,  # $799/month
            "interval": "month",
            "features": [
                "Up to 6 active businesses",
                "75 campaigns/month",
                "2,500 AI requests/month",
                "400 social posts/month",
                "40 email campaigns/month",
                "Quantum playbooks + premium automations",
                "Priority support"
            ]
        },
        "enterprise": {
            "name": "Enterprise",
            "price": 149900,  # $1,499/month
            "interval": "month",
            "features": [
                "Up to 12 active businesses",
                "Unlimited campaigns",
                "Unlimited AI requests",
                "Unlimited social posts",
                "Unlimited emails",
                "Dedicated success architect",
                "Custom integrations + SLAs",
                "White-label dashboards"
            ]
        }
    }

    @staticmethod
    def create_customer(email: str, name: Optional[str] = None, metadata: Optional[Dict] = None) -> stripe.Customer:
        """Create a Stripe customer."""
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata=metadata or {}
            )
            return customer
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stripe error: {str(e)}"
            )

    @staticmethod
    def create_subscription(
        customer_id: str,
        price_id: str,
        trial_days: int = 0,
        metadata: Optional[Dict] = None
    ) -> stripe.Subscription:
        """Create a Stripe subscription."""
        try:
            subscription_params = {
                "customer": customer_id,
                "items": [{"price": price_id}],
                "metadata": metadata or {},
                "expand": ["latest_invoice.payment_intent"]
            }

            if trial_days > 0:
                subscription_params["trial_period_days"] = trial_days

            subscription = stripe.Subscription.create(**subscription_params)
            return subscription

        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stripe error: {str(e)}"
            )

    @staticmethod
    def cancel_subscription(subscription_id: str, at_period_end: bool = True) -> stripe.Subscription:
        """Cancel a Stripe subscription."""
        try:
            if at_period_end:
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            else:
                subscription = stripe.Subscription.delete(subscription_id)

            return subscription

        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stripe error: {str(e)}"
            )

    @staticmethod
    def create_payment_intent(
        amount: int,
        currency: str = "usd",
        customer_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> stripe.PaymentIntent:
        """Create a Stripe payment intent for one-time payments."""
        try:
            payment_intent_params = {
                "amount": amount,
                "currency": currency,
                "metadata": metadata or {}
            }

            if customer_id:
                payment_intent_params["customer"] = customer_id

            payment_intent = stripe.PaymentIntent.create(**payment_intent_params)
            return payment_intent

        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stripe error: {str(e)}"
            )

    @staticmethod
    def create_checkout_session(
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        trial_days: int = 0,
        metadata: Optional[Dict] = None
    ) -> stripe.checkout.Session:
        """Create a Stripe Checkout session."""
        try:
            session_params = {
                "customer": customer_id,
                "payment_method_types": ["card"],
                "line_items": [{
                    "price": price_id,
                    "quantity": 1,
                }],
                "mode": "subscription",
                "success_url": success_url,
                "cancel_url": cancel_url,
                "metadata": metadata or {}
            }

            if trial_days > 0:
                session_params["subscription_data"] = {
                    "trial_period_days": trial_days
                }

            session = stripe.checkout.Session.create(**session_params)
            return session

        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stripe error: {str(e)}"
            )

    @staticmethod
    def create_billing_portal_session(customer_id: str, return_url: str) -> stripe.billing_portal.Session:
        """Create a Stripe billing portal session."""
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url
            )
            return session

        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stripe error: {str(e)}"
            )

    @staticmethod
    def verify_webhook_signature(payload: bytes, sig_header: str) -> Dict[str, Any]:
        """Verify Stripe webhook signature."""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
            return event

        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid payload"
            )
        except stripe.error.SignatureVerificationError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid signature"
            )


class PaymentEventHandler:
    """Handle Stripe webhook events."""

    @staticmethod
    def handle_subscription_created(event_data: Dict, db: Session):
        """Handle subscription.created event."""
        from .database import User, Subscription

        subscription = event_data["object"]
        customer_id = subscription["customer"]

        # Find user by Stripe customer ID
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if not user:
            return

        # Create subscription record
        db_subscription = Subscription(
            user_id=user.id,
            stripe_subscription_id=subscription["id"],
            plan_name=subscription["items"]["data"][0]["price"]["lookup_key"] or "starter",
            status=subscription["status"],
            current_period_start=datetime.fromtimestamp(subscription["current_period_start"]),
            current_period_end=datetime.fromtimestamp(subscription["current_period_end"])
        )
        db.add(db_subscription)

        # Update user subscription tier
        user.subscription_tier = db_subscription.plan_name
        db.commit()

    @staticmethod
    def handle_subscription_updated(event_data: Dict, db: Session):
        """Handle subscription.updated event."""
        from .database import Subscription

        subscription = event_data["object"]

        # Update subscription record
        db_subscription = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == subscription["id"]
        ).first()

        if db_subscription:
            db_subscription.status = subscription["status"]
            db_subscription.current_period_start = datetime.fromtimestamp(subscription["current_period_start"])
            db_subscription.current_period_end = datetime.fromtimestamp(subscription["current_period_end"])
            db_subscription.cancel_at_period_end = subscription.get("cancel_at_period_end", False)
            db.commit()

    @staticmethod
    def handle_subscription_deleted(event_data: Dict, db: Session):
        """Handle subscription.deleted event."""
        from .database import User, Subscription

        subscription = event_data["object"]

        # Update subscription record
        db_subscription = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == subscription["id"]
        ).first()

        if db_subscription:
            db_subscription.status = "canceled"

            # Downgrade user to free tier
            user = db.query(User).filter(User.id == db_subscription.user_id).first()
            if user:
                user.subscription_tier = "free"
                user.license_status = "trial"
                user.trial_expires_at = datetime.utcnow() + timedelta(days=3)

            db.commit()

    @staticmethod
    def handle_payment_succeeded(event_data: Dict, db: Session):
        """Handle payment_intent.succeeded event."""
        from .database import User, PaymentTransaction

        payment_intent = event_data["object"]
        customer_id = payment_intent.get("customer")

        if not customer_id:
            return

        # Find user
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if not user:
            return

        # Create payment transaction record
        transaction = PaymentTransaction(
            user_id=user.id,
            stripe_payment_intent_id=payment_intent["id"],
            amount=payment_intent["amount"] / 100,  # Convert cents to dollars
            currency=payment_intent["currency"].upper(),
            status="succeeded",
            description=payment_intent.get("description", "Payment"),
            metadata=payment_intent.get("metadata", {})
        )
        db.add(transaction)
        db.commit()

    @staticmethod
    def handle_payment_failed(event_data: Dict, db: Session):
        """Handle payment_intent.payment_failed event."""
        from .database import User, PaymentTransaction

        payment_intent = event_data["object"]
        customer_id = payment_intent.get("customer")

        if not customer_id:
            return

        # Find user
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if not user:
            return

        # Create failed payment transaction record
        transaction = PaymentTransaction(
            user_id=user.id,
            stripe_payment_intent_id=payment_intent["id"],
            amount=payment_intent["amount"] / 100,
            currency=payment_intent["currency"].upper(),
            status="failed",
            description=payment_intent.get("description", "Payment"),
            metadata=payment_intent.get("metadata", {})
        )
        db.add(transaction)
        db.commit()


# Webhook event router
WEBHOOK_HANDLERS = {
    "customer.subscription.created": PaymentEventHandler.handle_subscription_created,
    "customer.subscription.updated": PaymentEventHandler.handle_subscription_updated,
    "customer.subscription.deleted": PaymentEventHandler.handle_subscription_deleted,
    "payment_intent.succeeded": PaymentEventHandler.handle_payment_succeeded,
    "payment_intent.payment_failed": PaymentEventHandler.handle_payment_failed,
}


def handle_webhook_event(event: Dict, db: Session):
    """Route webhook event to appropriate handler."""
    event_type = event["type"]
    handler = WEBHOOK_HANDLERS.get(event_type)

    if handler:
        handler(event["data"], db)
    else:
        print(f"Unhandled event type: {event_type}")
