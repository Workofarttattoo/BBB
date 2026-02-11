#!/usr/bin/env python3
"""
Red Team Tools - Subscription & Licensing System

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

Supabase-backed subscription management and license validation for Red Team Security Tools.
Supports Professional, Enterprise, and Unlimited tiers with seat management.
"""

import os
import uuid
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict
from enum import Enum

# Supabase client
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("[warn] supabase-py not installed: pip install supabase")


class SubscriptionTier(Enum):
    """Subscription tier levels"""
    PROFESSIONAL = "professional"  # $99/mo or $997/yr
    ENTERPRISE = "enterprise"      # $299/mo or $2,997/yr
    UNLIMITED = "unlimited"        # $997/mo or $9,997/yr
    LIFETIME = "lifetime"          # $2,997 one-time (legacy)


class SubscriptionStatus(Enum):
    """Subscription status"""
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    TRIAL = "trial"


@dataclass
class Customer:
    """Customer record"""
    id: str
    email: str
    stripe_customer_id: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class Subscription:
    """Subscription record"""
    id: str
    customer_id: str
    tier: SubscriptionTier
    status: SubscriptionStatus
    stripe_subscription_id: Optional[str] = None
    current_period_end: Optional[datetime] = None
    seats_total: int = 1
    seats_used: int = 1
    created_at: Optional[datetime] = None


@dataclass
class License:
    """License key record"""
    id: str
    subscription_id: str
    license_key: str
    user_email: Optional[str] = None
    activated_at: Optional[datetime] = None
    last_validated: Optional[datetime] = None
    machine_id: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class UsageEvent:
    """Tool usage event"""
    id: str
    license_key: str
    tool_name: str
    event_type: str  # 'launch', 'scan', 'export', etc.
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None


class RedTeamLicenseManager:
    """
    Manages subscriptions and licenses for Red Team Tools.

    Features:
    - Subscription tier management
    - License key generation and validation
    - Seat management for Enterprise/Unlimited
    - Usage analytics
    - Stripe webhook handling
    """

    def __init__(self, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None):
        """Initialize with Supabase credentials"""
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL", "https://trokobwiphidmrmhwkni.supabase.co")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_KEY")

        if not SUPABASE_AVAILABLE:
            raise RuntimeError("supabase-py required: pip install supabase")

        if not self.supabase_key:
            raise ValueError("SUPABASE_KEY environment variable required")

        self.client: Client = create_client(self.supabase_url, self.supabase_key)

    def generate_license_key(self, subscription_id: str, tier: SubscriptionTier) -> str:
        """
        Generate unique license key.

        Format: TIER-XXXX-XXXX-XXXX-XXXX
        Example: PRO-A1B2-C3D4-E5F6-G7H8
        """
        prefix_map = {
            SubscriptionTier.PROFESSIONAL: "PRO",
            SubscriptionTier.ENTERPRISE: "ENT",
            SubscriptionTier.UNLIMITED: "UNL",
            SubscriptionTier.LIFETIME: "LFT"
        }

        prefix = prefix_map.get(tier, "UNK")
        unique_id = hashlib.sha256(f"{subscription_id}{uuid.uuid4()}".encode()).hexdigest()[:16].upper()

        # Format as XXXX-XXXX-XXXX-XXXX
        parts = [unique_id[i:i+4] for i in range(0, 16, 4)]
        return f"{prefix}-{'-'.join(parts)}"

    async def create_customer(self, email: str, stripe_customer_id: Optional[str] = None) -> Customer:
        """Create new customer"""
        customer_id = str(uuid.uuid4())

        data = {
            "id": customer_id,
            "email": email,
            "stripe_customer_id": stripe_customer_id,
            "created_at": datetime.utcnow().isoformat()
        }

        result = self.client.table("customers").insert(data).execute()

        return Customer(
            id=customer_id,
            email=email,
            stripe_customer_id=stripe_customer_id,
            created_at=datetime.utcnow()
        )

    async def create_subscription(
        self,
        customer_id: str,
        tier: SubscriptionTier,
        stripe_subscription_id: Optional[str] = None,
        trial_days: int = 14
    ) -> Subscription:
        """
        Create new subscription with automatic license generation.

        Args:
            customer_id: Customer UUID
            tier: Subscription tier
            stripe_subscription_id: Stripe subscription ID
            trial_days: Trial period in days (default 14)

        Returns:
            Subscription object with generated licenses
        """
        subscription_id = str(uuid.uuid4())

        # Determine seat count based on tier
        seats_map = {
            SubscriptionTier.PROFESSIONAL: 1,
            SubscriptionTier.ENTERPRISE: 5,
            SubscriptionTier.UNLIMITED: 999,
            SubscriptionTier.LIFETIME: 1
        }
        seats = seats_map.get(tier, 1)

        # Set expiration
        current_period_end = datetime.utcnow() + timedelta(days=trial_days)

        data = {
            "id": subscription_id,
            "customer_id": customer_id,
            "tier": tier.value,
            "status": SubscriptionStatus.TRIAL.value,
            "stripe_subscription_id": stripe_subscription_id,
            "current_period_end": current_period_end.isoformat(),
            "seats_total": seats,
            "seats_used": 0,
            "created_at": datetime.utcnow().isoformat()
        }

        self.client.table("subscriptions").insert(data).execute()

        # Generate initial license key
        await self.create_license(subscription_id, tier)

        return Subscription(
            id=subscription_id,
            customer_id=customer_id,
            tier=tier,
            status=SubscriptionStatus.TRIAL,
            stripe_subscription_id=stripe_subscription_id,
            current_period_end=current_period_end,
            seats_total=seats,
            seats_used=0,
            created_at=datetime.utcnow()
        )

    async def create_license(
        self,
        subscription_id: str,
        tier: SubscriptionTier,
        user_email: Optional[str] = None
    ) -> License:
        """Generate and store license key"""
        license_id = str(uuid.uuid4())
        license_key = self.generate_license_key(subscription_id, tier)

        data = {
            "id": license_id,
            "subscription_id": subscription_id,
            "license_key": license_key,
            "user_email": user_email,
            "created_at": datetime.utcnow().isoformat()
        }

        self.client.table("licenses").insert(data).execute()

        return License(
            id=license_id,
            subscription_id=subscription_id,
            license_key=license_key,
            user_email=user_email,
            created_at=datetime.utcnow()
        )

    async def validate_license(self, license_key: str, machine_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate license key and return subscription details.

        Returns:
            {
                "valid": bool,
                "tier": str,
                "status": str,
                "expires": datetime,
                "tools_enabled": List[str],
                "message": str
            }
        """
        # Fetch license
        license_result = self.client.table("licenses").select("*").eq("license_key", license_key).execute()

        if not license_result.data:
            return {
                "valid": False,
                "message": "Invalid license key"
            }

        license_data = license_result.data[0]

        # Fetch subscription
        sub_result = self.client.table("subscriptions").select("*").eq("id", license_data["subscription_id"]).execute()

        if not sub_result.data:
            return {
                "valid": False,
                "message": "Subscription not found"
            }

        sub_data = sub_result.data[0]

        # Check expiration
        expires = datetime.fromisoformat(sub_data["current_period_end"].replace("Z", "+00:00"))
        if datetime.utcnow() > expires and sub_data["status"] != "active":
            return {
                "valid": False,
                "message": "Subscription expired",
                "expires": expires
            }

        # Check seat limit (if machine_id provided)
        if machine_id:
            if not license_data.get("machine_id"):
                # First activation
                self.client.table("licenses").update({
                    "machine_id": machine_id,
                    "activated_at": datetime.utcnow().isoformat()
                }).eq("license_key", license_key).execute()

                # Increment seats_used
                self.client.table("subscriptions").update({
                    "seats_used": sub_data["seats_used"] + 1
                }).eq("id", sub_data["id"]).execute()

            elif license_data["machine_id"] != machine_id:
                return {
                    "valid": False,
                    "message": "License already activated on different machine"
                }

        # Update last validated
        self.client.table("licenses").update({
            "last_validated": datetime.utcnow().isoformat()
        }).eq("license_key", license_key).execute()

        # Return validation result
        tier = SubscriptionTier(sub_data["tier"])

        # All tools enabled for all tiers (for now)
        tools_enabled = [
            "aurorascan", "cipherspear", "skybreaker", "mythickey",
            "spectratrace", "nemesishydra", "obsidianhunt", "vectorflux",
            "dirreaper", "vulnhunter", "proxyphantom", "belchstudio",
            "nmappro", "hashsolver", "payloadforge", "metawrapper"
        ]

        return {
            "valid": True,
            "tier": tier.value,
            "status": sub_data["status"],
            "expires": expires,
            "tools_enabled": tools_enabled,
            "seats_total": sub_data["seats_total"],
            "seats_used": sub_data["seats_used"],
            "message": "License valid"
        }

    async def log_usage_event(
        self,
        license_key: str,
        tool_name: str,
        event_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UsageEvent:
        """Log tool usage for analytics"""
        event_id = str(uuid.uuid4())

        data = {
            "id": event_id,
            "license_key": license_key,
            "tool_name": tool_name,
            "event_type": event_type,
            "metadata": json.dumps(metadata) if metadata else None,
            "created_at": datetime.utcnow().isoformat()
        }

        self.client.table("usage_events").insert(data).execute()

        return UsageEvent(
            id=event_id,
            license_key=license_key,
            tool_name=tool_name,
            event_type=event_type,
            metadata=metadata,
            created_at=datetime.utcnow()
        )

    async def get_customer_subscription(self, customer_id: str) -> Optional[Subscription]:
        """Get active subscription for customer"""
        result = self.client.table("subscriptions")\
            .select("*")\
            .eq("customer_id", customer_id)\
            .in_("status", ["active", "trial", "past_due"])\
            .order("created_at", desc=True)\
            .limit(1)\
            .execute()

        if not result.data:
            return None

        sub = result.data[0]
        return Subscription(
            id=sub["id"],
            customer_id=sub["customer_id"],
            tier=SubscriptionTier(sub["tier"]),
            status=SubscriptionStatus(sub["status"]),
            stripe_subscription_id=sub.get("stripe_subscription_id"),
            current_period_end=datetime.fromisoformat(sub["current_period_end"].replace("Z", "+00:00")) if sub.get("current_period_end") else None,
            seats_total=sub["seats_total"],
            seats_used=sub["seats_used"],
            created_at=datetime.fromisoformat(sub["created_at"].replace("Z", "+00:00")) if sub.get("created_at") else None
        )

    async def get_subscription_licenses(self, subscription_id: str) -> List[License]:
        """Get all licenses for a subscription"""
        result = self.client.table("licenses")\
            .select("*")\
            .eq("subscription_id", subscription_id)\
            .execute()

        licenses = []
        for lic in result.data:
            licenses.append(License(
                id=lic["id"],
                subscription_id=lic["subscription_id"],
                license_key=lic["license_key"],
                user_email=lic.get("user_email"),
                activated_at=datetime.fromisoformat(lic["activated_at"].replace("Z", "+00:00")) if lic.get("activated_at") else None,
                last_validated=datetime.fromisoformat(lic["last_validated"].replace("Z", "+00:00")) if lic.get("last_validated") else None,
                machine_id=lic.get("machine_id"),
                created_at=datetime.fromisoformat(lic["created_at"].replace("Z", "+00:00")) if lic.get("created_at") else None
            ))

        return licenses

    async def handle_stripe_webhook(self, event_type: str, event_data: Dict[str, Any]) -> bool:
        """
        Handle Stripe webhook events.

        Supported events:
        - customer.subscription.created
        - customer.subscription.updated
        - customer.subscription.deleted
        - invoice.payment_succeeded
        - invoice.payment_failed
        """
        if event_type == "customer.subscription.created":
            # New subscription
            stripe_sub_id = event_data["id"]
            customer_id = event_data["customer"]

            # Determine tier from price_id
            price_id = event_data["items"]["data"][0]["price"]["id"]
            tier = self._price_id_to_tier(price_id)

            # Get or create customer
            customer = await self._get_or_create_customer_by_stripe_id(customer_id)

            # Create subscription
            await self.create_subscription(
                customer_id=customer.id,
                tier=tier,
                stripe_subscription_id=stripe_sub_id
            )

            return True

        elif event_type == "customer.subscription.updated":
            # Subscription changed
            stripe_sub_id = event_data["id"]
            status = event_data["status"]
            current_period_end = datetime.fromtimestamp(event_data["current_period_end"])

            # Update subscription
            self.client.table("subscriptions").update({
                "status": status,
                "current_period_end": current_period_end.isoformat()
            }).eq("stripe_subscription_id", stripe_sub_id).execute()

            return True

        elif event_type == "customer.subscription.deleted":
            # Subscription canceled
            stripe_sub_id = event_data["id"]

            self.client.table("subscriptions").update({
                "status": SubscriptionStatus.CANCELED.value
            }).eq("stripe_subscription_id", stripe_sub_id).execute()

            return True

        elif event_type == "invoice.payment_failed":
            # Payment failed
            stripe_sub_id = event_data["subscription"]

            self.client.table("subscriptions").update({
                "status": SubscriptionStatus.PAST_DUE.value
            }).eq("stripe_subscription_id", stripe_sub_id).execute()

            return True

        return False

    def _price_id_to_tier(self, price_id: str) -> SubscriptionTier:
        """Map Stripe price ID to subscription tier"""
        # TODO: Update with actual Stripe price IDs after setup
        price_map = {
            "price_professional_monthly": SubscriptionTier.PROFESSIONAL,
            "price_professional_yearly": SubscriptionTier.PROFESSIONAL,
            "price_enterprise_monthly": SubscriptionTier.ENTERPRISE,
            "price_enterprise_yearly": SubscriptionTier.ENTERPRISE,
            "price_unlimited_monthly": SubscriptionTier.UNLIMITED,
            "price_unlimited_yearly": SubscriptionTier.UNLIMITED,
        }

        return price_map.get(price_id, SubscriptionTier.PROFESSIONAL)

    async def _get_or_create_customer_by_stripe_id(self, stripe_customer_id: str) -> Customer:
        """Get customer by Stripe ID or create if not exists"""
        result = self.client.table("customers")\
            .select("*")\
            .eq("stripe_customer_id", stripe_customer_id)\
            .execute()

        if result.data:
            c = result.data[0]
            return Customer(
                id=c["id"],
                email=c["email"],
                stripe_customer_id=c["stripe_customer_id"],
                created_at=datetime.fromisoformat(c["created_at"].replace("Z", "+00:00")) if c.get("created_at") else None
            )

        # Customer doesn't exist, create placeholder
        # (Email will be updated when customer object webhook arrives)
        return await self.create_customer(
            email=f"stripe_{stripe_customer_id}@pending.com",
            stripe_customer_id=stripe_customer_id
        )


