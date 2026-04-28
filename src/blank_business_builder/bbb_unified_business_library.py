#!/usr/bin/env python3
"""
BBB Unified Business Library.

This installable module backs BBB recommendations and Echo Prime validation in
cloud deployments. It combines packaged 2025 AI automation data with legacy BBB
business models.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class UnifiedBusinessModel:
    """Universal business model structure."""

    name: str
    category: str
    tier: str
    startup_cost: int
    monthly_revenue_potential: int
    automation_level: int
    time_commitment_hours_week: int
    difficulty: str
    description: str
    tools_required: List[str]
    revenue_streams: List[str]
    automation_strategy: str
    target_market: str
    success_probability: float
    time_to_profit_months: str
    source: str

    def to_dict(self) -> Dict:
        return asdict(self)


class BBBUnifiedLibrary:
    """Unified business library combining packaged research and legacy models."""

    def __init__(self, data_path: Optional[Path] = None) -> None:
        package_dir = Path(__file__).resolve().parent
        self.repo_root = package_dir.parents[1]
        self.data_path = data_path or self.repo_root / "data" / "bbb_ai_businesses_2025.json"
        self.ai_automation_businesses = self._load_ai_automation_businesses()
        self.legacy_businesses = self._load_legacy_businesses()

    def _load_ai_automation_businesses(self) -> List[UnifiedBusinessModel]:
        """Load packaged 2025 AI automation research."""
        try:
            data = json.loads(self.data_path.read_text())
        except FileNotFoundError:
            return []

        businesses = []
        for business in data.get("businesses", []):
            businesses.append(
                UnifiedBusinessModel(
                    name=business["name"],
                    category=business["category"],
                    tier=self._determine_tier(business["monthly_revenue_potential"]),
                    startup_cost=business["startup_cost"],
                    monthly_revenue_potential=business["monthly_revenue_potential"],
                    automation_level=business["automation_level"],
                    time_commitment_hours_week=business["time_commitment_hours_week"],
                    difficulty=business["difficulty"],
                    description=business["description"],
                    tools_required=business["tools_required"],
                    revenue_streams=business["revenue_streams"],
                    automation_strategy=business["automation_strategy"],
                    target_market=business["target_market"],
                    success_probability=business["success_probability"],
                    time_to_profit_months=business.get("time_to_profit_months", "1-2"),
                    source="2025_research",
                )
            )
        return businesses

    def _load_legacy_businesses(self) -> List[UnifiedBusinessModel]:
        """Load the core legacy BBB business models."""
        return [
            UnifiedBusinessModel(
                name="Quantum-Optimized Crypto Mining",
                category="Cryptocurrency",
                tier="Tier 1",
                startup_cost=30000,
                monthly_revenue_potential=32500,
                automation_level=95,
                time_commitment_hours_week=2,
                difficulty="Hard",
                description=(
                    "Use quantum computing and machine learning techniques to forecast "
                    "profitable mining windows, manage pools, and optimize energy use."
                ),
                tools_required=["Mining rigs", "Quantum computing SDKs", "ML forecasting"],
                revenue_streams=["Mining rewards", "Staking income"],
                automation_strategy=(
                    "Algorithms predict mining windows, forecast energy costs, and switch coins."
                ),
                target_market="Cryptocurrency operators with existing technical infrastructure",
                success_probability=0.75,
                time_to_profit_months="2-4",
                source="legacy",
            ),
            UnifiedBusinessModel(
                name="NFT Collection Trading",
                category="Digital Art",
                tier="Tier 1",
                startup_cost=12500,
                monthly_revenue_potential=50000,
                automation_level=90,
                time_commitment_hours_week=5,
                difficulty="Hard",
                description="Generate NFT art, deploy smart contracts, manage community, and execute trading strategies.",
                tools_required=["AI design tools", "Smart contract platforms", "Community automation"],
                revenue_streams=["Primary sales", "Royalties", "Trading profits"],
                automation_strategy="AI generates art, analyzes trends, manages social channels, and optimizes rarity.",
                target_market="NFT collectors, digital art buyers, and Web3 communities",
                success_probability=0.65,
                time_to_profit_months="1-3",
                source="legacy",
            ),
            UnifiedBusinessModel(
                name="SaaS Micro-Tools Empire",
                category="Software",
                tier="Tier 1",
                startup_cost=6000,
                monthly_revenue_potential=30000,
                automation_level=95,
                time_commitment_hours_week=8,
                difficulty="Medium",
                description="Identify market gaps, build no-code tools, and automate customer acquisition and support.",
                tools_required=["No-code platforms", "AI analysis tools", "Marketing automation"],
                revenue_streams=["Monthly subscriptions", "Annual plans", "Enterprise licenses"],
                automation_strategy="AI identifies gaps, builds tools via no-code, and automates SEO, PPC, and support.",
                target_market="Small businesses and solopreneurs needing focused productivity tools",
                success_probability=0.80,
                time_to_profit_months="2-4",
                source="legacy",
            ),
            UnifiedBusinessModel(
                name="Amazon FBA Arbitrage",
                category="Ecommerce",
                tier="Tier 1",
                startup_cost=20000,
                monthly_revenue_potential=27500,
                automation_level=92,
                time_commitment_hours_week=10,
                difficulty="Medium",
                description="Scan products for arbitrage opportunities, manage inventory, and optimize pricing dynamically.",
                tools_required=["Amazon Seller account", "Arbitrage scanning tools", "Inventory management"],
                revenue_streams=["Product margin", "Volume discounts"],
                automation_strategy="AI scans products, manages shipments, forecasts demand, and updates pricing.",
                target_market="Online shoppers in high-demand retail categories",
                success_probability=0.82,
                time_to_profit_months="1-2",
                source="legacy",
            ),
            UnifiedBusinessModel(
                name="Print-on-Demand Empire",
                category="Ecommerce",
                tier="Tier 1",
                startup_cost=1250,
                monthly_revenue_potential=16500,
                automation_level=95,
                time_commitment_hours_week=6,
                difficulty="Easy",
                description="Generate designs using AI, test on multiple platforms, and scale winning designs.",
                tools_required=["AI design tools", "Redbubble", "Merch by Amazon", "Etsy"],
                revenue_streams=["Design sales", "Platform royalties"],
                automation_strategy="AI generates designs, tests platforms, optimizes SEO, and scales winners.",
                target_market="T-shirt, merchandise, and personalized gift buyers",
                success_probability=0.88,
                time_to_profit_months="1-2",
                source="legacy",
            ),
            UnifiedBusinessModel(
                name="Automated Tax Preparation",
                category="Finance Services",
                tier="Tier 2",
                startup_cost=2000,
                monthly_revenue_potential=20000,
                automation_level=88,
                time_commitment_hours_week=15,
                difficulty="Medium",
                description="Automated tax return preparation with CPA review for complex cases.",
                tools_required=["Tax software", "AI preparation tools", "E-filing systems"],
                revenue_streams=["Per-return fees", "Seasonal packages"],
                automation_strategy="AI prepares returns, flags complex cases for CPA review, and e-files automatically.",
                target_market="Individuals and small businesses with routine tax filing needs",
                success_probability=0.85,
                time_to_profit_months="1",
                source="legacy",
            ),
            UnifiedBusinessModel(
                name="SEO Content Agency",
                category="Content Creation",
                tier="Tier 2",
                startup_cost=1000,
                monthly_revenue_potential=15000,
                automation_level=85,
                time_commitment_hours_week=12,
                difficulty="Medium",
                description="AI-generated SEO content for clients, keyword research, and publishing automation.",
                tools_required=["AI writing tools", "SEO platforms", "WordPress"],
                revenue_streams=["Monthly retainers", "Per-article fees"],
                automation_strategy="AI researches keywords, generates content, publishes articles, and tracks rankings.",
                target_market="Small businesses needing consistent content marketing",
                success_probability=0.87,
                time_to_profit_months="1-2",
                source="legacy",
            ),
            UnifiedBusinessModel(
                name="Virtual Executive Assistant",
                category="B2B Services",
                tier="Tier 2",
                startup_cost=500,
                monthly_revenue_potential=12000,
                automation_level=80,
                time_commitment_hours_week=15,
                difficulty="Easy",
                description="AI-powered virtual assistant services for executives and entrepreneurs.",
                tools_required=["Calendly", "Zapier", "AI chatbots", "Email automation"],
                revenue_streams=["Monthly subscriptions", "Per-hour fees"],
                automation_strategy="AI handles scheduling, email management, research, and escalates complex tasks.",
                target_market="Busy executives, founders, and entrepreneurs",
                success_probability=0.82,
                time_to_profit_months="1",
                source="legacy",
            ),
            UnifiedBusinessModel(
                name="Financial Literacy Courses",
                category="Education",
                tier="Tier 2",
                startup_cost=2500,
                monthly_revenue_potential=10000,
                automation_level=90,
                time_commitment_hours_week=8,
                difficulty="Medium",
                description="AI-generated financial education courses on autopilot platforms.",
                tools_required=["Teachable", "AI content generation", "Video editing tools"],
                revenue_streams=["Course sales", "Membership subscriptions"],
                automation_strategy="AI creates lessons, generates quizzes, automates email sequences, and tracks progress.",
                target_market="Individuals seeking practical financial education",
                success_probability=0.78,
                time_to_profit_months="2-3",
                source="legacy",
            ),
            UnifiedBusinessModel(
                name="Automated Dropshipping",
                category="Ecommerce",
                tier="Tier 3",
                startup_cost=3000,
                monthly_revenue_potential=8000,
                automation_level=85,
                time_commitment_hours_week=12,
                difficulty="Medium",
                description="Automated dropshipping store with AI product selection and marketing.",
                tools_required=["Shopify", "Supplier platforms", "AI marketing tools"],
                revenue_streams=["Product margins", "Upsells"],
                automation_strategy="AI selects products, creates pages, runs campaigns, and handles order routing.",
                target_market="Online shoppers in validated trending niches",
                success_probability=0.72,
                time_to_profit_months="1-2",
                source="legacy",
            ),
        ]

    @staticmethod
    def _determine_tier(monthly_revenue: int) -> str:
        if monthly_revenue >= 10000:
            return "Tier 1"
        if monthly_revenue >= 5000:
            return "Tier 2"
        if monthly_revenue >= 3000:
            return "Tier 3"
        if monthly_revenue >= 1500:
            return "Tier 4"
        return "Tier 5"

    def get_all_businesses(self) -> List[UnifiedBusinessModel]:
        return self.ai_automation_businesses + self.legacy_businesses

    def get_by_category(self, category: str) -> List[UnifiedBusinessModel]:
        return [business for business in self.get_all_businesses() if business.category == category]

    def get_by_tier(self, tier: str) -> List[UnifiedBusinessModel]:
        return [business for business in self.get_all_businesses() if business.tier == tier]

    def get_by_automation_level(self, min_automation: int) -> List[UnifiedBusinessModel]:
        return [
            business for business in self.get_all_businesses()
            if business.automation_level >= min_automation
        ]

    def get_by_startup_cost(self, max_cost: int) -> List[UnifiedBusinessModel]:
        return [business for business in self.get_all_businesses() if business.startup_cost <= max_cost]

    def get_recommendations(
        self,
        budget: int,
        available_hours_week: int,
        experience_level: str,
        preferred_categories: Optional[List[str]] = None,
    ) -> List[Dict]:
        all_businesses = self.get_all_businesses()
        affordable = [business for business in all_businesses if business.startup_cost <= budget]
        time_fit = [
            business for business in affordable
            if business.time_commitment_hours_week <= available_hours_week
        ]
        difficulty_map = {
            "beginner": ["Easy"],
            "intermediate": ["Easy", "Medium"],
            "advanced": ["Easy", "Medium", "Hard"],
        }
        difficulty_fit = [
            business for business in time_fit
            if business.difficulty in difficulty_map.get(
                experience_level.lower(), ["Easy", "Medium", "Hard"]
            )
        ]
        if preferred_categories:
            difficulty_fit = [
                business for business in difficulty_fit
                if business.category in preferred_categories
            ]

        denominator = max(budget, 1)
        scored = []
        for business in difficulty_fit:
            score = (
                business.success_probability * 0.3
                + (business.automation_level / 100) * 0.3
                + min(business.monthly_revenue_potential / 20000, 1) * 0.2
                + max(0, 1 - business.startup_cost / denominator) * 0.2
            )
            scored.append({"business": business, "match_score": round(score * 100, 2)})

        scored.sort(key=lambda item: item["match_score"], reverse=True)
        return scored[:5]

    def generate_summary_report(self) -> Dict:
        businesses = self.get_all_businesses()
        categories = sorted({business.category for business in businesses})
        return {
            "total_businesses": len(businesses),
            "total_categories": len(categories),
            "categories": categories,
            "ai_automation_count": len(self.ai_automation_businesses),
            "legacy_count": len(self.legacy_businesses),
            "average_startup_cost": round(
                sum(business.startup_cost for business in businesses) / max(len(businesses), 1),
                2,
            ),
            "average_monthly_revenue": round(
                sum(business.monthly_revenue_potential for business in businesses)
                / max(len(businesses), 1),
                2,
            ),
            "average_automation_level": round(
                sum(business.automation_level for business in businesses) / max(len(businesses), 1),
                2,
            ),
        }
