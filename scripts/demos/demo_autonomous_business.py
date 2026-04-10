#!/usr/bin/env python3
"""
Autonomous Business Demonstration
=================================

Demonstration of the autonomous business orchestration system.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from blank_business_builder.autonomous_business import launch_autonomous_business


async def demo():
    """Demo: Launch autonomous business."""
    result = await launch_autonomous_business(
        business_concept="AI Chatbot Integration Service",
        founder_name="Joshua Cole",
        duration_hours=0.1,  # 6 minutes for demo
        market_research_api_key="test",
        sendgrid_api_key="test",
        stripe_api_key="test",
        twitter_consumer_key="test",
        twitter_consumer_secret="test",
        twitter_access_token="test",
        twitter_access_token_secret="test"
    )

    print("\n" + "="*60)
    print("FINAL AUTONOMOUS BUSINESS METRICS")
    print("="*60)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(demo())
