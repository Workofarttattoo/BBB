#!/usr/bin/env python3
"""
START AUTONOMOUS OS
===================

Entry point for the Autonomous Business Operating System.
Loads environment variables and launches the persistent engine.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add src to python path
sys.path.append(str(Path(__file__).parent / "src"))

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("autonomous_os.log")
    ]
)
logger = logging.getLogger("OS_BOOTSTRAP")

async def bootstrap():
    """Bootstrap the Autonomous OS."""
    logger.info("Initializing Autonomous Business OS...")

    # Check for critical environment variables (Real Mode)
    required_vars = ["OPENAI_API_KEY", "STRIPE_API_KEY", "TWILIO_ACCOUNT_SID", "ELEVENLABS_API_KEY"]
    missing = [v for v in required_vars if not os.getenv(v)]

    if missing:
        logger.warning(f"Missing environment variables: {missing}")
        logger.warning("System will run in LIMITED/DRY-RUN mode for missing services.")
    else:
        logger.info("All critical services configured (Real Mode Active).")

    try:
        from blank_business_builder.autonomous_os import BusinessOS

        # Initialize OS
        os_system = BusinessOS(owner_name="Joshua Hendricks Cole")

        # Ensure ChatterTech AI exists
        if not os_system.active_businesses:
            os_system.register_business("ChatterTech AI")

        logger.info("🚀 Launching Daily Operational Loop...")

        # Run Forever
        while True:
            await os_system.run_daily_cycle()
            logger.info("Daily cycle complete. Sleeping for next cycle...")
            await asyncio.sleep(10) # 10s sleep for demo/test purposes

    except ImportError as e:
        logger.error(f"Failed to import BusinessOS: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"OS Crash: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(bootstrap())
