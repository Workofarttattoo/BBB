"""
Fiduciary Manager for handling licensing, revenue share, and financial logic.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

ADMIN_BYPASS_CODE = "F00lpr00f596!"
STATE_FILE = "business_state.json"


@dataclass
class LicenseState:
    tier: str  # "free", "paid", "partner" (revenue share)
    active: bool
    revenue_share_percentage: float
    start_date: str
    last_payment_date: Optional[str] = None
    bypass_used: bool = False


class FiduciaryManager:
    """Manages licensing, revenue sharing, and financial compliance."""

    def __init__(self, state_file: str = STATE_FILE):
        self.state_file = Path(state_file)
        self.state = self._load_state()

    def _load_state(self) -> Dict:
        if not self.state_file.exists():
            return {
                "license": {
                    "tier": "free",
                    "active": False,
                    "revenue_share_percentage": 0.0,
                    "start_date": datetime.now().isoformat(),
                    "bypass_used": False
                },
                "wallet": 0.0,
                "revenue_total": 0.0
            }
        try:
            with open(self.state_file, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

    def _save_state(self):
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=2)

    def get_license_info(self) -> Dict:
        return self.state.get("license", {})

    def activate_revenue_share(self) -> Dict:
        """Activate the 50% revenue share model (Partner Tier)."""
        current_license = self.state.get("license", {})

        # Once on partner tier, cannot switch back to free or paid easily without termination
        if current_license.get("tier") == "partner":
            logger.warning("Already on Partner Tier.")
            return current_license

        self.state["license"] = {
            "tier": "partner",
            "active": True,
            "revenue_share_percentage": 0.50,  # 50% share
            "start_date": datetime.now().isoformat(),
            "bypass_used": False
        }
        self._save_state()
        logger.info("Revenue Share (Partner Tier) activated: 50% split.")
        return self.state["license"]

    def purchase_paid_license(self) -> Dict:
        """Activate the full ownership model (Paid Tier)."""
        current_license = self.state.get("license", {})

        # If already on partner tier, switching is restricted (per user requirement "No switching later")
        # However, typically upgrading to paid is allowed, but the prompt says "No switching later".
        # We will enforce this strict rule: If you picked Rev Share, you stick with it for the contract duration.
        if current_license.get("tier") == "partner":
            raise ValueError("Cannot switch from Partner Tier to Paid Tier. Contract is binding.")

        self.state["license"] = {
            "tier": "paid",
            "active": True,
            "revenue_share_percentage": 0.0,
            "start_date": datetime.now().isoformat(),
            "bypass_used": False
        }
        self._save_state()
        logger.info("Paid License activated: 100% ownership.")
        return self.state["license"]

    def apply_admin_bypass(self, code: str) -> bool:
        """Apply admin bypass code to unlock Paid Tier for free."""
        if code == ADMIN_BYPASS_CODE:
            self.state["license"] = {
                "tier": "paid",  # Treat as paid/owner
                "active": True,
                "revenue_share_percentage": 0.0,
                "start_date": datetime.now().isoformat(),
                "bypass_used": True
            }
            self._save_state()
            logger.info("Admin Bypass applied. Unlocked Owner Tier.")
            return True
        return False

    def process_revenue(self, amount: float) -> Dict[str, float]:
        """Process incoming revenue and split according to license."""
        license_info = self.state.get("license", {})
        share_pct = license_info.get("revenue_share_percentage", 0.0)

        platform_share = amount * share_pct
        user_share = amount - platform_share

        self.state["wallet"] = self.state.get("wallet", 0.0) + user_share
        self.state["revenue_total"] = self.state.get("revenue_total", 0.0) + amount

        self._save_state()

        return {
            "total": amount,
            "user_share": user_share,
            "platform_share": platform_share
        }
