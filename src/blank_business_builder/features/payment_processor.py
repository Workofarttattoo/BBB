"""
Payment processor for Stripe integration.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations

try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    stripe = None
    STRIPE_AVAILABLE = False

from ..ech0_service import ECH0Service

class PaymentProcessor:
    """
    Payment processor for handling Stripe payments.
    """

    def __init__(self, api_key: str):
        if STRIPE_AVAILABLE:
            stripe.api_key = api_key
        self.ech0_service = ECH0Service()

    async def create_checkout_session(self, price_id: str, success_url: str, cancel_url: str) -> str:
        """
        Create a Stripe checkout session.
        """
        try:
            # Try creating checkout session with ECH0 first
            return await self.ech0_service.create_checkout_session(price_id, success_url, cancel_url)
        except Exception:
            # Fallback to Stripe
            if STRIPE_AVAILABLE and stripe:
                try:
                    checkout_session = stripe.checkout.Session.create(
                        line_items=[
                            {
                                'price': price_id,
                                'quantity': 1,
                            },
                        ],
                        mode='payment',
                        success_url=success_url,
                        cancel_url=cancel_url,
                    )
                    return checkout_session.url
                except Exception as e:
                    return str(e)
            else:
                return "Error: Stripe not available"
