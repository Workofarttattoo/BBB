#!/usr/bin/env python3
"""
SIMULATION ENGINE - Accelerated Business Evolution
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

This engine runs business simulations at accelerated speeds ("Fast Forward")
to generate error logs, train the Digital Twin, and validate stability before
real-world deployment.
"""

import time
import logging
import random
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [SIMULATION] %(message)s')
logger = logging.getLogger(__name__)

class SimulationEngine:
    """
    Runs accelerated simulations of business days.
    Generates synthetic events (leads, orders, errors).
    """

    def __init__(self, business_type: str = "Generic"):
        self.business_type = business_type
        self.days_simulated = 0
        self.events_log = []

        # Simulation parameters
        self.traffic_multiplier = 1.0
        self.error_rate = 0.05

        logger.info(f"Simulation Engine initialized for: {business_type}")

    def run_fast_forward(self, days: int, speed_factor: float = 0.1) -> List[str]:
        """
        Run a simulation for X days.
        speed_factor: seconds to wait per simulated day.
        Returns: List of critical errors encountered.
        """
        logger.info(f"--- FAST FORWARD: Running {days} days ---")
        detected_errors = []

        for day in range(1, days + 1):
            self.days_simulated += 1
            daily_report = self._simulate_day(day)

            if daily_report['errors']:
                detected_errors.extend(daily_report['errors'])
                logger.warning(f"Day {self.days_simulated}: {len(daily_report['errors'])} errors detected.")
            else:
                if day % 5 == 0: # Log every 5th day to avoid spam
                    logger.info(f"Day {self.days_simulated}: Operations normal. Revenue: ${daily_report['revenue']:.2f}")

            time.sleep(speed_factor)

        return detected_errors

    def _simulate_day(self, day_num: int) -> Dict[str, Any]:
        """Simulate a single day's activity."""

        # 1. Traffic Generation
        visitors = int(random.normalvariate(100, 20) * self.traffic_multiplier)

        # 2. Conversion (Leads/Orders)
        leads = int(visitors * 0.05)
        orders = int(visitors * 0.01)
        revenue = orders * random.randint(50, 200) # Avg order value

        # 3. Error Generation
        errors = []

        # Random chaotic events
        if random.random() < self.error_rate:
            error_type = random.choice([
                "DatabaseConnectionTimeout",
                "PaymentGatewayError",
                "EmailDeliveryFailure",
                "APIRateLimitExceeded",
                "FrontendRenderingCrash"
            ])
            errors.append(f"{error_type} at {random.randint(9, 17)}:00")

        # Load-based errors
        if visitors > 150:
            errors.append("HighLatencyWarning: Server load > 90%")

        return {
            "day": day_num,
            "visitors": visitors,
            "leads": leads,
            "orders": orders,
            "revenue": revenue,
            "errors": errors
        }

# Verification
if __name__ == "__main__":
    sim = SimulationEngine("Fiverr Scraper Service")

    # Run 30 days in ~3 seconds
    errors = sim.run_fast_forward(days=30, speed_factor=0.05)

    print("\n--- SIMULATION SUMMARY ---")
    print(f"Total Days: 30")
    print(f"Errors Found: {len(errors)}")
    for err in errors:
        print(f" - {err}")
