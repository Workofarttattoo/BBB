"""
Payment processor for Stripe integration.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations

try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    class MockStripe:
        api_key = ""
        class checkout:
            class Session:
                @staticmethod
                def create(*args, **kwargs): return type('Session', (), {'url': 'http://mock.url'})()
    stripe = MockStripe
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

    async def create_checkout_session(
        self,
        price_id: str,
        success_url: str,
        cancel_url: str,
        *,
        business_name: str = "default",
        role: str = "finance",
        approval_id: str | None = None,
        skip_gate: bool = False,
    ) -> str:
        """
        Create a Stripe checkout session.
        """
        if not skip_gate:
            from ..approval_gates import GateAction, gate_from_policy
            from ..enterprise_agent_policy import Capability, resolve_business_policy

            policy = resolve_business_policy(business_name).policy_for_role(role)
            gate_from_policy(
                mode_requires_approval=policy.requires_approval_before_side_effect(
                    Capability.PAYMENT_CHARGE
                ),
                action=GateAction.PAYMENT_CHARGE,
                business_name=business_name,
                role=role,
                approval_id=approval_id,
                metadata={"price_id": price_id},
                force_manual=policy.is_manual_only(Capability.PAYMENT_CHARGE),
            )
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
