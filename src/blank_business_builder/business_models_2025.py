"""
35+ Automated Business Models for Level-6-Agent Operations.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class BusinessModel:
    name: str
    industry: str
    ramp_up_months: int
    startup_cost: float
    expected_monthly_revenue: float
    expected_monthly_expenses: float
    time_commitment_hours_per_week: int
    description: str
    automation_level: float = 0.9
    difficulty: str = "Medium"
    required_roles: List[str] = field(default_factory=lambda: ["marketer", "sales", "support", "finance", "executive"])
    tier: int = 1

# --- Tier 1: Highest Profit, Easiest Automation ---

TIER_1_MODELS = [
    BusinessModel(
        name="Quantum-Optimized Crypto Mining",
        industry="Crypto",
        ramp_up_months=3,
        startup_cost=30000.0,
        expected_monthly_revenue=32500.0,  # Avg of 15-50K
        expected_monthly_expenses=12000.0, # Energy + maintenance
        time_commitment_hours_per_week=1,
        description="Uses quantum algorithms to predict optimal mining times and switch coins dynamically.",
        automation_level=1.0,
        difficulty="Medium",
        required_roles=["crypto_miner", "finance", "executive"],
        tier=1
    ),
    BusinessModel(
        name="NFT Collection Creation & Trading",
        industry="Crypto",
        ramp_up_months=2,
        startup_cost=12500.0,
        expected_monthly_revenue=52500.0, # Avg of 5-100K+
        expected_monthly_expenses=5000.0,
        time_commitment_hours_per_week=2,
        description="Generates NFT art using AI, manages smart contracts, and executes trading strategies.",
        automation_level=0.98,
        difficulty="Hard",
        required_roles=["nft_trader", "content_creator", "marketer", "community_manager"],
        tier=1
    ),
    BusinessModel(
        name="SaaS Micro-Tools Empire",
        industry="Technology",
        ramp_up_months=3,
        startup_cost=6000.0,
        expected_monthly_revenue=30000.0,
        expected_monthly_expenses=4000.0,
        time_commitment_hours_per_week=3,
        description="Identifies market gaps, builds no-code tools, handles acquisition and support.",
        automation_level=0.95,
        difficulty="Medium",
        required_roles=["saas_builder", "marketer", "support", "finance"],
        tier=1
    ),
    BusinessModel(
        name="Amazon FBA Arbitrage",
        industry="Ecommerce",
        ramp_up_months=2,
        startup_cost=20000.0,
        expected_monthly_revenue=27500.0,
        expected_monthly_expenses=18000.0,
        time_commitment_hours_per_week=4,
        description="Scans for arbitrage opportunities, purchases inventory, and manages FBA shipments.",
        automation_level=0.92,
        difficulty="Medium",
        required_roles=["arbitrage_bot", "fulfillment", "support", "finance"],
        tier=1
    ),
    BusinessModel(
        name="Print-on-Demand Empire",
        industry="Ecommerce",
        ramp_up_months=2,
        startup_cost=1250.0,
        expected_monthly_revenue=16500.0,
        expected_monthly_expenses=8000.0,
        time_commitment_hours_per_week=2,
        description="Generates AI designs, tests on multiple platforms, and scales winners.",
        automation_level=0.97,
        difficulty="Easy",
        required_roles=["content_creator", "marketer", "support", "finance"],
        tier=1
    ),
]

# --- Tier 2: High Profit, Good Automation ---

TIER_2_MODELS = [
    BusinessModel(
        name="Automated Tax Preparation Battalion",
        industry="Finance",
        ramp_up_months=1,
        startup_cost=2000.0,
        expected_monthly_revenue=20000.0,
        expected_monthly_expenses=4000.0,
        time_commitment_hours_per_week=5,
        description="Markets tax services, collects docs, and uses AI to prepare returns.",
        automation_level=0.88,
        difficulty="Medium",
        required_roles=["tax_preparer", "marketer", "support", "finance"],
        tier=2
    ),
    BusinessModel(
        name="Survey Taking Battalion",
        industry="Gig Economy",
        ramp_up_months=0,
        startup_cost=750.0,
        expected_monthly_revenue=5500.0,
        expected_monthly_expenses=500.0,
        time_commitment_hours_per_week=0,
        description="Manages 100+ survey accounts and uses AI to complete surveys intelligently.",
        automation_level=1.0,
        difficulty="Easy",
        required_roles=["survey_bot", "finance"],
        tier=2
    ),
    BusinessModel(
        name="Website Testing Agency",
        industry="Quality Assurance",
        ramp_up_months=2,
        startup_cost=2000.0,
        expected_monthly_revenue=10500.0,
        expected_monthly_expenses=1500.0,
        time_commitment_hours_per_week=2,
        description="Performs automated usability testing, runs A/B tests, and generates reports.",
        automation_level=0.94,
        difficulty="Easy",
        required_roles=["tester_bot", "marketer", "finance"],
        tier=2
    ),
    BusinessModel(
        name="Stock Photography Empire",
        industry="Digital Assets",
        ramp_up_months=3,
        startup_cost=1250.0,
        expected_monthly_revenue=8000.0,
        expected_monthly_expenses=500.0,
        time_commitment_hours_per_week=2,
        description="Generates AI images, optimizes for trends, and uploads to stock sites.",
        automation_level=0.96,
        difficulty="Easy",
        required_roles=["content_creator", "finance"],
        tier=2
    ),
    BusinessModel(
        name="YouTube Automation Channels",
        industry="Content Creation",
        ramp_up_months=5,
        startup_cost=3000.0,
        expected_monthly_revenue=12500.0,
        expected_monthly_expenses=2000.0,
        time_commitment_hours_per_week=4,
        description="Researches trends, generates scripts/videos using AI, and publishes on schedule.",
        automation_level=0.90,
        difficulty="Medium",
        required_roles=["content_creator", "marketer", "finance"],
        tier=2
    ),
]

# --- Tier 3: Medium Profit, Full Automation ---

TIER_3_MODELS = [
    BusinessModel(
        name="Lead Generation & Sales",
        industry="B2B Services",
        ramp_up_months=2,
        startup_cost=1000.0,
        expected_monthly_revenue=10000.0,
        expected_monthly_expenses=2000.0,
        time_commitment_hours_per_week=3,
        description="Generates leads via SEO/PPC, qualifies with AI, sells to businesses.",
        automation_level=0.92,
        difficulty="Medium",
        required_roles=["sales", "marketer", "finance"],
        tier=3
    ),
    BusinessModel(
        name="Faceless TikTok Channels",
        industry="Content Creation",
        ramp_up_months=2,
        startup_cost=500.0,
        expected_monthly_revenue=6500.0,
        expected_monthly_expenses=500.0,
        time_commitment_hours_per_week=2,
        description="Creates viral content using AI, posts frequently, monetizes via funds/sponsors.",
        automation_level=0.95,
        difficulty="Easy",
        required_roles=["content_creator", "marketer", "finance"],
        tier=3
    ),
    BusinessModel(
        name="Etsy Digital Products Store",
        industry="Ecommerce",
        ramp_up_months=2,
        startup_cost=200.0,
        expected_monthly_revenue=8000.0,
        expected_monthly_expenses=500.0,
        time_commitment_hours_per_week=1,
        description="AI generates planners, templates, printables; automated marketing and support.",
        automation_level=0.98,
        difficulty="Easy",
        required_roles=["content_creator", "marketer", "support", "finance"],
        tier=3
    ),
    BusinessModel(
        name="Dropshipping (AI-Optimized)",
        industry="Ecommerce",
        ramp_up_months=3,
        startup_cost=1500.0,
        expected_monthly_revenue=14000.0,
        expected_monthly_expenses=8000.0,
        time_commitment_hours_per_week=5,
        description="Quantum algorithms find winning products, automates ads, support, fulfillment.",
        automation_level=0.87,
        difficulty="Medium",
        required_roles=["dropshipper", "marketer", "support", "finance"],
        tier=3
    ),
     BusinessModel(
        name="Kindle Publishing Empire",
        industry="Publishing",
        ramp_up_months=4,
        startup_cost=500.0,
        expected_monthly_revenue=5500.0,
        expected_monthly_expenses=1000.0,
        time_commitment_hours_per_week=2,
        description="AI writes books, generates covers, optimizes keywords, manages pricing.",
        automation_level=0.94,
        difficulty="Easy",
        required_roles=["content_creator", "marketer", "finance"],
        tier=3
    ),
]

# --- Bonus: Quantum + ML + AI Opportunities ---

BONUS_MODELS = [
    BusinessModel(
        name="Quantum-Enhanced Trading Bot",
        industry="Finance",
        ramp_up_months=2,
        startup_cost=75000.0,
        expected_monthly_revenue=110000.0, # Avg 20-200K
        expected_monthly_expenses=10000.0,
        time_commitment_hours_per_week=1,
        description="Uses quantum algorithms for pattern recognition and trades automatically.",
        automation_level=1.0,
        difficulty="Hard",
        required_roles=["quantum_trader", "finance", "executive"],
        tier=6 # Special Tier
    ),
]

def get_all_business_models() -> List[BusinessModel]:
    return TIER_1_MODELS + TIER_2_MODELS + TIER_3_MODELS + BONUS_MODELS
