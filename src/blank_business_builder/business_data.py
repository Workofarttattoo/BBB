"""
Curated library of starter business ideas for evaluation.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List

from .business_models_2025 import get_all_business_models

@dataclass(frozen=True)
class BusinessIdea:
    """Represents a candidate business concept."""

    name: str
    industry: str
    ramp_up_months: int
    startup_cost: float
    expected_monthly_revenue: float
    expected_monthly_expenses: float
    time_commitment_hours_per_week: int
    description: str
    automation_level: float = 0.0
    difficulty: str = "Medium"
    required_roles: List[str] = field(default_factory=list)

    @property
    def monthly_profit(self) -> float:
        return self.expected_monthly_revenue - self.expected_monthly_expenses


def default_ideas() -> Iterable[BusinessIdea]:
    """Provide a set of diversified business concepts for evaluation."""

    # Load 2025 Models
    new_models = [
        BusinessIdea(
            name=m.name,
            industry=m.industry,
            ramp_up_months=m.ramp_up_months,
            startup_cost=m.startup_cost,
            expected_monthly_revenue=m.expected_monthly_revenue,
            expected_monthly_expenses=m.expected_monthly_expenses,
            time_commitment_hours_per_week=m.time_commitment_hours_per_week,
            description=m.description,
            automation_level=m.automation_level,
            difficulty=m.difficulty,
            required_roles=m.required_roles
        ) for m in get_all_business_models()
    ]

    # Legacy Models (Preserved for compatibility)
    legacy_models = [
        # EDUCATION & TRAINING (Low-Medium Budget)
        BusinessIdea(
            name="Financial Literacy Micro-Courses",
            industry="Education",
            ramp_up_months=1,
            startup_cost=1200.0,
            expected_monthly_revenue=6200.0,
            expected_monthly_expenses=1800.0,
            time_commitment_hours_per_week=12,
            description="Async video lessons paired with live Q&A for early-career professionals.",
        ),
        BusinessIdea(
            name="Corporate Training Bootcamps",
            industry="Education",
            ramp_up_months=2,
            startup_cost=2800.0,
            expected_monthly_revenue=9500.0,
            expected_monthly_expenses=3200.0,
            time_commitment_hours_per_week=20,
            description="3-day intensive workshops for enterprise clients on leadership and productivity.",
        ),
        BusinessIdea(
            name="Technical Interview Prep Platform",
            industry="Education",
            ramp_up_months=2,
            startup_cost=1800.0,
            expected_monthly_revenue=7200.0,
            expected_monthly_expenses=2100.0,
            time_commitment_hours_per_week=15,
            description="1-on-1 coaching and mock interviews for software engineers targeting FAANG.",
        ),

        # PROFESSIONAL SERVICES (Medium Budget)
        BusinessIdea(
            name="Remote Notary Collective",
            industry="Professional Services",
            ramp_up_months=2,
            startup_cost=1800.0,
            expected_monthly_revenue=7800.0,
            expected_monthly_expenses=2600.0,
            time_commitment_hours_per_week=18,
            description="Licensed mobile notaries coordinated through a central scheduling portal.",
        ),
        BusinessIdea(
            name="Virtual Executive Assistant Agency",
            industry="Professional Services",
            ramp_up_months=1,
            startup_cost=1500.0,
            expected_monthly_revenue=8900.0,
            expected_monthly_expenses=3400.0,
            time_commitment_hours_per_week=25,
            description="Curated VAs for C-suite executives with white-glove client management.",
        ),
        BusinessIdea(
            name="Grant Writing Consultancy",
            industry="Professional Services",
            ramp_up_months=2,
            startup_cost=900.0,
            expected_monthly_revenue=11200.0,
            expected_monthly_expenses=2800.0,
            time_commitment_hours_per_week=20,
            description="Success-fee based grant applications for non-profits and research institutions.",
        ),

        # ECOMMERCE (Medium-High Budget)
        BusinessIdea(
            name="Sustainable Office Snack Boxes",
            industry="Ecommerce",
            ramp_up_months=3,
            startup_cost=3400.0,
            expected_monthly_revenue=8700.0,
            expected_monthly_expenses=4300.0,
            time_commitment_hours_per_week=20,
            description="Subscription snack boxes sourced from local suppliers with sustainability metrics.",
        ),
        BusinessIdea(
            name="Premium Pet Supplement Brand",
            industry="Ecommerce",
            ramp_up_months=4,
            startup_cost=5200.0,
            expected_monthly_revenue=13400.0,
            expected_monthly_expenses=6800.0,
            time_commitment_hours_per_week=28,
            description="Vet-formulated supplements with DTC Shopify store and Amazon FBA channel.",
        ),
        BusinessIdea(
            name="Custom Laptop Skins Marketplace",
            industry="Ecommerce",
            ramp_up_months=2,
            startup_cost=2200.0,
            expected_monthly_revenue=6800.0,
            expected_monthly_expenses=2900.0,
            time_commitment_hours_per_week=16,
            description="Print-on-demand laptop decals from independent artists with profit sharing.",
        ),
        BusinessIdea(
            name="Smart Home Starter Kits",
            industry="Ecommerce",
            ramp_up_months=3,
            startup_cost=4800.0,
            expected_monthly_revenue=10200.0,
            expected_monthly_expenses=5100.0,
            time_commitment_hours_per_week=22,
            description="Curated bundles of IoT devices with setup guides for non-technical homeowners.",
        ),

        # FINANCE (Medium-High Budget)
        BusinessIdea(
            name="Fractional CFO Pods",
            industry="Finance",
            ramp_up_months=2,
            startup_cost=2400.0,
            expected_monthly_revenue=10800.0,
            expected_monthly_expenses=5200.0,
            time_commitment_hours_per_week=25,
            description="Shared finance leadership for SaaS founders needing investor-grade reporting.",
        ),
        BusinessIdea(
            name="Tax Prep for Creators",
            industry="Finance",
            ramp_up_months=1,
            startup_cost=1200.0,
            expected_monthly_revenue=9200.0,
            expected_monthly_expenses=2700.0,
            time_commitment_hours_per_week=18,
            description="Specialized tax filing for influencers, YouTubers, and content entrepreneurs.",
        ),
        BusinessIdea(
            name="Real Estate Syndication Platform",
            industry="Finance",
            ramp_up_months=5,
            startup_cost=8200.0,
            expected_monthly_revenue=16500.0,
            expected_monthly_expenses=7200.0,
            time_commitment_hours_per_week=35,
            description="Accredited investor portal for pooled commercial real estate investments.",
        ),

        # HEALTHCARE (Higher Budget)
        BusinessIdea(
            name="Healthcare Compliance Automation",
            industry="Healthcare",
            ramp_up_months=4,
            startup_cost=4200.0,
            expected_monthly_revenue=12600.0,
            expected_monthly_expenses=6100.0,
            time_commitment_hours_per_week=30,
            description="Workflow automation and training bundles to keep small practices audit-ready.",
        ),
        BusinessIdea(
            name="Telemedicine Platform for Mental Health",
            industry="Healthcare",
            ramp_up_months=3,
            startup_cost=6800.0,
            expected_monthly_revenue=15200.0,
            expected_monthly_expenses=7600.0,
            time_commitment_hours_per_week=32,
            description="HIPAA-compliant video therapy marketplace connecting patients with licensed therapists.",
        ),
        BusinessIdea(
            name="Medical Billing Services for Chiropractors",
            industry="Healthcare",
            ramp_up_months=2,
            startup_cost=2200.0,
            expected_monthly_revenue=9800.0,
            expected_monthly_expenses=3900.0,
            time_commitment_hours_per_week=24,
            description="Outsourced revenue cycle management for chiropractic clinics.",
        ),

        # TECH & SOFTWARE (Low-High Budget)
        BusinessIdea(
            name="No-Code App Development Agency",
            industry="Technology",
            ramp_up_months=2,
            startup_cost=1800.0,
            expected_monthly_revenue=11400.0,
            expected_monthly_expenses=3600.0,
            time_commitment_hours_per_week=26,
            description="Build MVPs for startups using Bubble, Webflow, and Airtable.",
        ),
        BusinessIdea(
            name="AI Chatbot Integration Service",
            industry="Technology",
            ramp_up_months=1,
            startup_cost=800.0,
            expected_monthly_revenue=8200.0,
            expected_monthly_expenses=2200.0,
            time_commitment_hours_per_week=18,
            description="Deploy and train ChatGPT-powered customer service bots for small businesses.",
        ),
        BusinessIdea(
            name="SaaS Metrics Dashboard",
            industry="Technology",
            ramp_up_months=4,
            startup_cost=5600.0,
            expected_monthly_revenue=9800.0,
            expected_monthly_expenses=3400.0,
            time_commitment_hours_per_week=22,
            description="Subscription analytics tool for B2B SaaS companies tracking MRR and churn.",
        ),
        BusinessIdea(
            name="Cybersecurity Audits for SMBs",
            industry="Technology",
            ramp_up_months=2,
            startup_cost=2400.0,
            expected_monthly_revenue=12200.0,
            expected_monthly_expenses=4100.0,
            time_commitment_hours_per_week=24,
            description="Penetration testing and compliance reports for businesses with 10-100 employees.",
        ),

        # LOGISTICS & OPERATIONS
        BusinessIdea(
            name="Micro-Fulfilment Analytics",
            industry="Logistics",
            ramp_up_months=3,
            startup_cost=3600.0,
            expected_monthly_revenue=9900.0,
            expected_monthly_expenses=4700.0,
            time_commitment_hours_per_week=22,
            description="Dashboard and advisory services for local retailers adopting micro-warehousing.",
        ),
        BusinessIdea(
            name="Last-Mile Delivery Network",
            industry="Logistics",
            ramp_up_months=4,
            startup_cost=7200.0,
            expected_monthly_revenue=14800.0,
            expected_monthly_expenses=8200.0,
            time_commitment_hours_per_week=35,
            description="Coordinate independent couriers for same-day local deliveries.",
        ),

        # MARKETING & CREATIVE (Low-Medium Budget)
        BusinessIdea(
            name="SEO Content Agency for Local Businesses",
            industry="Marketing",
            ramp_up_months=1,
            startup_cost=600.0,
            expected_monthly_revenue=7800.0,
            expected_monthly_expenses=2100.0,
            time_commitment_hours_per_week=20,
            description="Blog writing, local SEO, and Google My Business optimization.",
        ),
        BusinessIdea(
            name="Social Media Management for Restaurants",
            industry="Marketing",
            ramp_up_months=1,
            startup_cost=800.0,
            expected_monthly_revenue=6400.0,
            expected_monthly_expenses=1600.0,
            time_commitment_hours_per_week=15,
            description="Content calendar, posting, and reputation management for food service.",
        ),
        BusinessIdea(
            name="Podcast Production Studio",
            industry="Creative",
            ramp_up_months=2,
            startup_cost=3800.0,
            expected_monthly_revenue=8900.0,
            expected_monthly_expenses=3200.0,
            time_commitment_hours_per_week=22,
            description="Full-service podcast editing, mixing, and distribution for business podcasters.",
        ),
        BusinessIdea(
            name="UGC Video Creator Network",
            industry="Creative",
            ramp_up_months=2,
            startup_cost=1200.0,
            expected_monthly_revenue=9600.0,
            expected_monthly_expenses=3800.0,
            time_commitment_hours_per_week=20,
            description="Match brands with authentic creators for TikTok and Instagram Reels ads.",
        ),

        # REAL ESTATE & PROPERTY (Medium-High Budget)
        BusinessIdea(
            name="Vacation Rental Management",
            industry="Real Estate",
            ramp_up_months=3,
            startup_cost=4200.0,
            expected_monthly_revenue=11800.0,
            expected_monthly_expenses=5900.0,
            time_commitment_hours_per_week=28,
            description="Full-service Airbnb hosting for property owners: cleaning, guest comms, pricing.",
        ),
        BusinessIdea(
            name="Co-Working Space Operator",
            industry="Real Estate",
            ramp_up_months=6,
            startup_cost=12000.0,
            expected_monthly_revenue=18400.0,
            expected_monthly_expenses=9200.0,
            time_commitment_hours_per_week=40,
            description="Flexible office memberships with meeting rooms and community events.",
        ),

        # HOME SERVICES (Low-Medium Budget)
        BusinessIdea(
            name="Mobile Car Detailing",
            industry="Services",
            ramp_up_months=1,
            startup_cost=2200.0,
            expected_monthly_revenue=8200.0,
            expected_monthly_expenses=3100.0,
            time_commitment_hours_per_week=25,
            description="On-site auto detailing with eco-friendly products for busy professionals.",
        ),
        BusinessIdea(
            name="Smart Home Installation Service",
            industry="Services",
            ramp_up_months=1,
            startup_cost=1800.0,
            expected_monthly_revenue=9400.0,
            expected_monthly_expenses=3600.0,
            time_commitment_hours_per_week=24,
            description="Configure and install smart locks, thermostats, and security cameras.",
        ),
        BusinessIdea(
            name="Junk Removal & Donation Coordination",
            industry="Services",
            ramp_up_months=1,
            startup_cost=3200.0,
            expected_monthly_revenue=10200.0,
            expected_monthly_expenses=4800.0,
            time_commitment_hours_per_week=30,
            description="Haul away unwanted items and handle tax-deductible donation receipts.",
        ),

        # CONSULTING & ADVISORY (Low Budget)
        BusinessIdea(
            name="Sustainability Consulting for Retailers",
            industry="Consulting",
            ramp_up_months=2,
            startup_cost=900.0,
            expected_monthly_revenue=9800.0,
            expected_monthly_expenses=2400.0,
            time_commitment_hours_per_week=18,
            description="Carbon footprint audits and green supply chain recommendations.",
        ),
        BusinessIdea(
            name="Remote Work Transition Coaching",
            industry="Consulting",
            ramp_up_months=1,
            startup_cost=400.0,
            expected_monthly_revenue=6800.0,
            expected_monthly_expenses=1200.0,
            time_commitment_hours_per_week=14,
            description="Help teams adopt async workflows, Zoom hygiene, and distributed collaboration tools.",
        ),
    ]

    return new_models + legacy_models
