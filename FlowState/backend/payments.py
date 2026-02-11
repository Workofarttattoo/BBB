
"""
Stripe Payment Processing for FlowState
"""

import stripe
import os
from fastapi import HTTPException
from typing import Optional, Dict, Any

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_...")


class PaymentService:
    """Handle subscriptions and payments via Stripe"""

    def __init__(self):
        self.price_ids = {
            "free": None,
            "pro": os.getenv("STRIPE_PRO_PRICE_ID", "price_..."),
            "enterprise": os.getenv("STRIPE_ENTERPRISE_PRICE_ID", "price_...")
        }

    async def create_customer(self, email: str, name: Optional[str] = None) -> str:
        """Create Stripe customer"""
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={"source": "flowstate"}
            )
            return customer.id
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=str(e))

    async def create_subscription(self, customer_id: str, plan: str = "pro") -> Dict[str, Any]:
        """Create subscription for customer"""
        if plan not in self.price_ids or self.price_ids[plan] is None:
            raise HTTPException(status_code=400, detail="Invalid plan")

        try:
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{"price": self.price_ids[plan]}],
                payment_behavior="default_incomplete",
                payment_settings={"save_default_payment_method": "on_subscription"},
                expand=["latest_invoice.payment_intent"]
            )

            return {
                "subscription_id": subscription.id,
                "client_secret": subscription.latest_invoice.payment_intent.client_secret,
                "status": subscription.status
            }
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=str(e))

    async def cancel_subscription(self, subscription_id: str) -> bool:
        """Cancel subscription"""
        try:
            stripe.Subscription.delete(subscription_id)
            return True
        except stripe.error.StripeError:
            return False

    async def create_checkout_session(self, customer_email: str, plan: str = "pro") -> str:
        """Create Stripe Checkout session"""
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price": self.price_ids[plan],
                    "quantity": 1
                }],
                mode="subscription",
                success_url=os.getenv("STRIPE_SUCCESS_URL", "https://flowstatus.work/success"),
                cancel_url=os.getenv("STRIPE_CANCEL_URL", "https://flowstatus.work/pricing"),
                customer_email=customer_email
            )
            return session.url
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=str(e))

    async def handle_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """Process Stripe webhook events"""
        webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_...")

        try:
            event = stripe.Webhook.construct_event(
                payload, signature, webhook_secret
            )

            # Handle different event types
            if event.type == "checkout.session.completed":
                session = event.data.object
                # Provision access for customer
                return {"action": "provision", "customer": session.customer}

            elif event.type == "customer.subscription.deleted":
                subscription = event.data.object
                # Revoke access for customer
                return {"action": "revoke", "customer": subscription.customer}

            elif event.type == "invoice.payment_failed":
                invoice = event.data.object
                # Send email about failed payment
                return {"action": "payment_failed", "customer": invoice.customer}

            return {"action": "ignored", "type": event.type}

        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise HTTPException(status_code=401, detail="Invalid signature")


payment_service = PaymentService()
