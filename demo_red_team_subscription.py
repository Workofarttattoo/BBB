#!/usr/bin/env python3
"""
Red Team Tools - License Manager Demo
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from blank_business_builder.red_team_subscription_system import (
        RedTeamLicenseManager,
        SubscriptionTier
    )
except ImportError as e:
    print(f"Error importing RedTeamLicenseManager: {e}")
    sys.exit(1)

async def demo():
    """Demo the licensing system"""
    print("Red Team Tools - License Manager Demo")
    print("=" * 60)

    # Initialize
    try:
        manager = RedTeamLicenseManager()
    except (RuntimeError, ValueError) as e:
        print(f"Failed to initialize manager: {e}")
        print("Please ensure SUPABASE_URL and SUPABASE_KEY are set and supabase-py is installed.")
        return

    try:
        # Create customer
        print("\n1. Creating customer...")
        customer = await manager.create_customer(
            email="pentest@example.com"
        )
        print(f"   Customer ID: {customer.id}")
        print(f"   Email: {customer.email}")

        # Create subscription
        print("\n2. Creating Professional subscription...")
        subscription = await manager.create_subscription(
            customer_id=customer.id,
            tier=SubscriptionTier.PROFESSIONAL,
            trial_days=14
        )
        print(f"   Subscription ID: {subscription.id}")
        print(f"   Tier: {subscription.tier.value}")
        print(f"   Status: {subscription.status.value}")
        print(f"   Expires: {subscription.current_period_end}")
        print(f"   Seats: {subscription.seats_used}/{subscription.seats_total}")

        # Get licenses
        print("\n3. Getting license keys...")
        licenses = await manager.get_subscription_licenses(subscription.id)
        for lic in licenses:
            print(f"   License: {lic.license_key}")

        # Validate license
        print("\n4. Validating license...")
        validation = await manager.validate_license(
            license_key=licenses[0].license_key,
            machine_id="demo-machine-001"
        )
        print(f"   Valid: {validation['valid']}")
        print(f"   Tier: {validation['tier']}")
        print(f"   Tools: {len(validation['tools_enabled'])} enabled")

        # Log usage
        print("\n5. Logging tool usage...")
        event = await manager.log_usage_event(
            license_key=licenses[0].license_key,
            tool_name="aurorascan",
            event_type="scan",
            metadata={"targets": 5, "vulnerabilities": 2}
        )
        print(f"   Event ID: {event.id}")
        print(f"   Tool: {event.tool_name}")
        print(f"   Type: {event.event_type}")

        print("\n" + "=" * 60)
        print("Demo complete! License system ready for production.")

    except Exception as e:
        print(f"\nError during demo: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(demo())
    except KeyboardInterrupt:
        print("\nDemo interrupted.")
