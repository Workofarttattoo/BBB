"""
Echo Prime validation for BBB business models.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Dict, List

from .bbb_unified_business_library import UnifiedBusinessModel


@dataclass
class FactCheckResult:
    """Result of a deterministic business model fact check."""

    claim: str
    is_verified: bool
    confidence: float
    evidence: List[str]
    red_flags: List[str]
    category: str

    def to_dict(self) -> Dict:
        data = asdict(self)
        data["verified"] = data.pop("is_verified")
        return data


class TruthVerificationEngine:
    """Verify BBB recommendations for realistic revenue, costs, claims, and tooling."""

    def __init__(self) -> None:
        self.reality_bounds = {
            "monthly_revenue": {"min": 0, "max": 100000, "reasonable_max": 50000},
            "startup_cost": {"min": 0, "max": 100000, "reasonable_max": 50000},
            "automation_level": {"min": 0, "max": 100, "realistic_max": 95},
            "time_to_profit_months": {"min": 0, "max": 36, "reasonable_range": (1, 18)},
            "success_probability": {"min": 0.0, "max": 1.0, "realistic_max": 0.95},
        }
        self.hallucination_patterns = [
            r"100% automated",
            r"guaranteed.*profit",
            r"zero.*risk",
            r"unlimited.*potential",
            r"\$\d{6,}.*per.*month.*passive",
            r"no.*work.*required",
            r"ai.*does.*everything",
        ]
        self.pseudo_science_terms = [
            "quantum manifest",
            "vibration frequency",
            "energy alignment",
            "chakra optimization",
            "cosmic synchronization",
            "metaphysical algorithm",
            "spiritual blockchain",
            "consciousness mining",
        ]

    def verify_business_model(self, business: UnifiedBusinessModel) -> List[FactCheckResult]:
        return [
            self._verify_revenue(business),
            self._verify_costs(business),
            self._verify_automation(business),
            self._verify_timeline(business),
            self._check_pseudo_science(business),
            self._check_hallucinations(business),
        ]

    def _verify_revenue(self, business: UnifiedBusinessModel) -> FactCheckResult:
        revenue = business.monthly_revenue_potential
        bounds = self.reality_bounds["monthly_revenue"]
        red_flags = []
        evidence = []

        if revenue < bounds["min"] or revenue > bounds["max"]:
            red_flags.append(f"Revenue ${revenue} outside possible range")
        if revenue > bounds["reasonable_max"]:
            red_flags.append(f"Revenue ${revenue} exceeds typical automation business max")
        monthly_roi = revenue / max(business.startup_cost, 1)
        if monthly_roi > 5:
            red_flags.append(f"ROI of {monthly_roi:.0%}/month is unrealistically high")
        if business.automation_level > 90 and revenue > 50000:
            red_flags.append("High automation with revenue over $50K/mo needs stronger evidence")
        if not red_flags:
            evidence.append(f"Revenue ${revenue}/mo is within configured reality bounds")

        return self._result(f"Monthly revenue: ${revenue}", red_flags, evidence, "revenue")

    def _verify_costs(self, business: UnifiedBusinessModel) -> FactCheckResult:
        cost = business.startup_cost
        bounds = self.reality_bounds["startup_cost"]
        red_flags = []
        evidence = []
        if cost < bounds["min"] or cost > bounds["max"]:
            red_flags.append(f"Startup cost ${cost} outside possible range")
        if cost > bounds["reasonable_max"]:
            red_flags.append(f"Startup cost ${cost} requires institutional planning")
        if not red_flags:
            evidence.append(f"Startup cost ${cost} is within configured bounds")
        return self._result(f"Startup cost: ${cost}", red_flags, evidence, "cost")

    def _verify_automation(self, business: UnifiedBusinessModel) -> FactCheckResult:
        automation = business.automation_level
        red_flags = []
        evidence = []
        bounds = self.reality_bounds["automation_level"]
        if automation < bounds["min"] or automation > bounds["max"]:
            red_flags.append(f"Automation level {automation}% outside possible range")
        if automation > bounds["realistic_max"]:
            red_flags.append(f"Automation level {automation}% exceeds realistic max")
        if automation > 90 and business.time_commitment_hours_week < 2:
            red_flags.append("Very high automation still needs monitoring time")
        if not red_flags:
            evidence.append(f"Automation level {automation}% is realistic for the model")
        return self._result(f"Automation level: {automation}%", red_flags, evidence, "automation")

    def _verify_timeline(self, business: UnifiedBusinessModel) -> FactCheckResult:
        months = [int(value) for value in re.findall(r"\d+", str(business.time_to_profit_months))]
        min_month = min(months) if months else 0
        max_month = max(months) if months else 0
        red_flags = []
        evidence = []
        bounds = self.reality_bounds["time_to_profit_months"]
        if max_month > bounds["max"]:
            red_flags.append(f"Time to profit {max_month} months exceeds maximum bound")
        if min_month == 0 and business.monthly_revenue_potential > 10000:
            red_flags.append("Immediate profit claim needs supporting evidence")
        if not red_flags:
            evidence.append(f"Time to profit {business.time_to_profit_months} months is plausible")
        return self._result(
            f"Time to profit: {business.time_to_profit_months}",
            red_flags,
            evidence,
            "timeline",
        )

    def _check_pseudo_science(self, business: UnifiedBusinessModel) -> FactCheckResult:
        text = self._business_text(business)
        red_flags = [term for term in self.pseudo_science_terms if term in text]
        evidence = [] if red_flags else ["No pseudo-science terms detected"]
        return self._result("Scientific validity check", red_flags, evidence, "technical")

    def _check_hallucinations(self, business: UnifiedBusinessModel) -> FactCheckResult:
        text = self._business_text(business)
        red_flags = [
            f"Hallucination pattern detected: {pattern}"
            for pattern in self.hallucination_patterns
            if re.search(pattern, text, re.IGNORECASE)
        ]
        evidence = [] if red_flags else ["No hallucination patterns detected"]
        return self._result("Hallucination check", red_flags, evidence, "technical")

    @staticmethod
    def _business_text(business: UnifiedBusinessModel) -> str:
        return " ".join(
            [
                business.name,
                business.description,
                business.automation_strategy,
                " ".join(business.tools_required),
                " ".join(business.revenue_streams),
            ]
        ).lower()

    @staticmethod
    def _result(
        claim: str,
        red_flags: List[str],
        evidence: List[str],
        category: str,
    ) -> FactCheckResult:
        is_verified = not red_flags
        return FactCheckResult(
            claim=claim,
            is_verified=is_verified,
            confidence=1.0 if is_verified else 0.0,
            evidence=evidence,
            red_flags=red_flags,
            category=category,
        )


class BBBParliamentValidator:
    """Deterministic Echo Prime validator for BBB business recommendations."""

    def __init__(self) -> None:
        self.truth_engine = TruthVerificationEngine()

    async def validate_business_model(self, business: UnifiedBusinessModel) -> Dict:
        fact_checks = self.truth_engine.verify_business_model(business)
        failed_checks = [check for check in fact_checks if not check.is_verified]
        algorithm_check = self._verify_algorithms(business)
        market_check = self._verify_market_claims(business)

        red_flags = []
        for check in failed_checks:
            red_flags.extend(check.red_flags)
        red_flags.extend(f"Fake algorithm: {item}" for item in algorithm_check["fake_algorithms"])
        red_flags.extend(f"Market issue: {item}" for item in market_check["issues"])

        truth_confidence = (len(fact_checks) - len(failed_checks)) / max(len(fact_checks), 1)
        algorithm_confidence = 1.0 if algorithm_check["all_verified"] else 0.0
        market_confidence = 1.0 if market_check["is_realistic"] else 0.0
        verification_confidence = (
            truth_confidence * 0.50
            + algorithm_confidence * 0.20
            + market_confidence * 0.30
        )

        if verification_confidence >= 0.85:
            overall_status = "VERIFIED"
        elif verification_confidence >= 0.70:
            overall_status = "ACCEPTABLE_WITH_WARNINGS"
        else:
            overall_status = "FAILED_VALIDATION"

        return {
            "business_name": business.name,
            "timestamp": datetime.utcnow().isoformat(),
            "validation_stages": {
                "truth_verification": {
                    "total_checks": len(fact_checks),
                    "passed": len(fact_checks) - len(failed_checks),
                    "failed": len(failed_checks),
                    "details": [check.to_dict() for check in fact_checks],
                },
                "algorithm_check": algorithm_check,
                "market_check": market_check,
            },
            "overall_status": overall_status,
            "red_flags": red_flags,
            "verification_confidence": verification_confidence,
        }

    def _verify_algorithms(self, business: UnifiedBusinessModel) -> Dict:
        text = TruthVerificationEngine._business_text(business)
        fake_patterns = [
            r"quantum\s+(?!computing|algorithm|algorithms|sdk|physics|machine learning)",
            r"ai\s+magic",
            r"automated\s+everything",
        ]
        fake_algorithms = []
        for pattern in fake_patterns:
            fake_algorithms.extend(re.findall(pattern, text, re.IGNORECASE))
        return {
            "fake_algorithms": fake_algorithms,
            "all_verified": len(fake_algorithms) == 0,
        }

    @staticmethod
    def _verify_market_claims(business: UnifiedBusinessModel) -> Dict:
        issues = []
        if not business.target_market or len(business.target_market) < 10:
            issues.append("Target market too vague or missing")
        if not business.revenue_streams:
            issues.append("No revenue streams specified")
        if not business.tools_required:
            issues.append("No tools/platforms specified")
        return {"is_realistic": len(issues) == 0, "issues": issues}
