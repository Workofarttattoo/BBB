"""
Magic R&D Lab Rental Business
==============================

Use our magic R&D machine to create whatever you need:
- $299 for a few hours (2-4 hours)
- $1,000 for a full day (24 hours)
- $5,000 for a full week (7 days)

From quantum simulations to AI models to complex scientific analysis -
our advanced computing platform can handle it all.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
from decimal import Decimal

logger = logging.getLogger(__name__)


class RentalPackage(Enum):
    """R&D Lab rental packages - Simple pricing!"""
    FEW_HOURS = "few_hours"    # 2-4 hours - $299
    FULL_DAY = "full_day"      # 24 hours - $1,000
    FULL_WEEK = "full_week"    # 7 days - $5,000


# Simple pricing structure
PACKAGE_PRICING = {
    RentalPackage.FEW_HOURS: {
        "price": Decimal('299.00'),
        "hours": 4,
        "description": "Perfect for quick experiments and proof-of-concepts"
    },
    RentalPackage.FULL_DAY: {
        "price": Decimal('1000.00'),
        "hours": 24,
        "description": "Full day of computing power for serious R&D"
    },
    RentalPackage.FULL_WEEK: {
        "price": Decimal('5000.00'),
        "hours": 168,  # 7 days
        "description": "Week-long access for major projects and research"
    }
}


@dataclass
class RDSession:
    """R&D Lab session."""
    session_id: str
    customer_name: str
    customer_email: str
    package: RentalPackage
    project_description: str
    started_at: datetime
    expires_at: datetime
    status: str = "active"  # active, completed, expired
    results: List[Dict] = field(default_factory=list)
    hours_used: float = 0.0
    amount_paid: Decimal = Decimal('0.00')


@dataclass
class Customer:
    """Customer using Magic R&D Lab."""
    customer_id: str
    name: str
    company: str
    email: str
    created_at: datetime = field(default_factory=datetime.now)
    total_spent: Decimal = Decimal('0.00')
    sessions_count: int = 0
    referral_code: Optional[str] = None


class MagicRDLab:
    """
    Magic R&D Lab - Advanced Computing as a Service

    Simple pricing: Rent our "magic machine" by the hour, day, or week.
    Perfect for:
    - Quantum computing research
    - AI/ML model training
    - Complex scientific simulations
    - Data analysis at scale
    - Computational chemistry/physics
    - Custom R&D projects
    """

    def __init__(self):
        self.customers: Dict[str, Customer] = {}
        self.sessions: List[RDSession] = []
        self.revenue = Decimal('0.00')

    def create_customer(self, name: str, company: str, email: str) -> Customer:
        """Create new customer account."""
        customer_id = f"CUST{len(self.customers) + 1:04d}"

        customer = Customer(
            customer_id=customer_id,
            name=name,
            company=company,
            email=email
        )

        # Generate referral code
        customer.referral_code = f"RDL-{customer_id}"

        self.customers[customer_id] = customer
        logger.info(f"Created customer: {name} from {company}")

        return customer

    def book_session(
        self,
        customer_id: str,
        package: RentalPackage,
        project_description: str
    ) -> RDSession:
        """Book an R&D Lab session."""
        customer = self.customers.get(customer_id)
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")

        pricing = PACKAGE_PRICING[package]
        session_id = f"SES{len(self.sessions) + 1:06d}"

        started_at = datetime.now()
        expires_at = started_at + timedelta(hours=pricing["hours"])

        session = RDSession(
            session_id=session_id,
            customer_name=customer.name,
            customer_email=customer.email,
            package=package,
            project_description=project_description,
            started_at=started_at,
            expires_at=expires_at,
            amount_paid=pricing["price"]
        )

        self.sessions.append(session)

        # Update customer
        customer.sessions_count += 1
        customer.total_spent += pricing["price"]

        # Update revenue
        self.revenue += pricing["price"]

        logger.info(
            f"Booked {package.value} session for {customer.name}: "
            f"${pricing['price']} for {pricing['hours']} hours"
        )

        return session

    async def run_computation(
        self,
        session_id: str,
        task_description: str
    ) -> Dict[str, Any]:
        """
        Run computation on the Magic R&D Machine.

        This is the magic part - customers submit what they want to compute,
        and the system handles it. The actual implementation (QuLab Infinite)
        is kept proprietary.
        """
        session = next((s for s in self.sessions if s.session_id == session_id), None)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        if session.status != "active":
            raise ValueError(f"Session {session_id} is not active")

        if datetime.now() > session.expires_at:
            session.status = "expired"
            raise ValueError(f"Session {session_id} has expired")

        logger.info(f"Running computation: {task_description}")

        # Simulate processing (actual implementation would call QuLab Infinite)
        await asyncio.sleep(2.0)  # Simulate computation time

        # Mock result (real implementation returns actual computation results)
        result = {
            "task": task_description,
            "status": "completed",
            "computation_time": 2.0,
            "timestamp": datetime.now().isoformat(),
            "result_summary": f"Successfully completed: {task_description}",
            "data": {
                "success": True,
                "message": "Computation completed on Magic R&D Machine"
            }
        }

        session.results.append(result)
        session.hours_used += 2.0 / 60  # Track usage

        logger.info(f"Computation completed for session {session_id}")

        return result

    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get status of an R&D session."""
        session = next((s for s in self.sessions if s.session_id == session_id), None)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        time_remaining = (session.expires_at - datetime.now()).total_seconds() / 3600
        time_remaining = max(0, time_remaining)

        pricing = PACKAGE_PRICING[session.package]

        return {
            "session_id": session.session_id,
            "customer": session.customer_name,
            "package": session.package.value,
            "status": session.status,
            "project": session.project_description,
            "started_at": session.started_at.isoformat(),
            "expires_at": session.expires_at.isoformat(),
            "time_remaining_hours": round(time_remaining, 2),
            "hours_purchased": pricing["hours"],
            "hours_used": round(session.hours_used, 2),
            "amount_paid": float(session.amount_paid),
            "computations_run": len(session.results),
            "results_available": len(session.results)
        }

    def get_customer_dashboard(self, customer_id: str) -> Dict[str, Any]:
        """Get customer dashboard with all sessions and stats."""
        customer = self.customers.get(customer_id)
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")

        customer_sessions = [s for s in self.sessions if s.customer_email == customer.email]
        active_sessions = [s for s in customer_sessions if s.status == "active"]
        completed_sessions = [s for s in customer_sessions if s.status == "completed"]

        total_hours = sum(PACKAGE_PRICING[s.package]["hours"] for s in customer_sessions)
        total_computations = sum(len(s.results) for s in customer_sessions)

        return {
            "customer_id": customer.customer_id,
            "name": customer.name,
            "company": customer.company,
            "email": customer.email,
            "referral_code": customer.referral_code,
            "member_since": customer.created_at.isoformat(),
            "total_spent": float(customer.total_spent),
            "sessions": {
                "total": len(customer_sessions),
                "active": len(active_sessions),
                "completed": len(completed_sessions)
            },
            "usage": {
                "total_hours_purchased": total_hours,
                "total_computations": total_computations,
                "avg_computations_per_session": total_computations / max(1, len(customer_sessions))
            },
            "active_sessions": [
                {
                    "session_id": s.session_id,
                    "package": s.package.value,
                    "expires_in_hours": round((s.expires_at - datetime.now()).total_seconds() / 3600, 1),
                    "project": s.project_description
                }
                for s in active_sessions
            ]
        }

    def get_pricing_info(self) -> Dict[str, Any]:
        """Get pricing information for marketing."""
        return {
            "tagline": "Use our magic R&D machine to create whatever you need",
            "packages": [
                {
                    "name": "Quick Experiment",
                    "package": RentalPackage.FEW_HOURS.value,
                    "price": "$299",
                    "duration": "2-4 hours",
                    "description": PACKAGE_PRICING[RentalPackage.FEW_HOURS]["description"],
                    "perfect_for": [
                        "Proof of concepts",
                        "Quick experiments",
                        "Testing ideas",
                        "Small projects"
                    ]
                },
                {
                    "name": "Full Day Access",
                    "package": RentalPackage.FULL_DAY.value,
                    "price": "$1,000",
                    "duration": "24 hours",
                    "description": PACKAGE_PRICING[RentalPackage.FULL_DAY]["description"],
                    "perfect_for": [
                        "Serious R&D work",
                        "Medium-sized projects",
                        "Complex simulations",
                        "Multiple experiments"
                    ],
                    "savings": "Save $197 vs hourly rate"
                },
                {
                    "name": "Full Week Access",
                    "package": RentalPackage.FULL_WEEK.value,
                    "price": "$5,000",
                    "duration": "7 days",
                    "description": PACKAGE_PRICING[RentalPackage.FULL_WEEK]["description"],
                    "perfect_for": [
                        "Major research projects",
                        "Extensive simulations",
                        "AI model training",
                        "Complex analysis"
                    ],
                    "savings": "Save $2,000 vs daily rate"
                }
            ],
            "capabilities": [
                "Quantum computing simulations",
                "AI/ML model training",
                "Scientific computing at scale",
                "Data analysis & visualization",
                "Computational chemistry/physics",
                "Custom R&D projects"
            ],
            "guarantee": "100% satisfaction or money back"
        }

    def get_business_metrics(self) -> Dict[str, Any]:
        """Get business performance metrics."""
        active_sessions = [s for s in self.sessions if s.status == "active"]
        completed_sessions = [s for s in self.sessions if s.status == "completed"]

        # Package distribution
        package_dist = {}
        for package in RentalPackage:
            count = len([s for s in self.sessions if s.package == package])
            package_dist[package.value] = count

        return {
            "total_revenue": float(self.revenue),
            "total_customers": len(self.customers),
            "total_sessions": len(self.sessions),
            "active_sessions": len(active_sessions),
            "completed_sessions": len(completed_sessions),
            "package_distribution": package_dist,
            "avg_revenue_per_customer": float(self.revenue / max(1, len(self.customers))),
            "total_computations": sum(len(s.results) for s in self.sessions)
        }


# Demonstration
async def demo_magic_rd_lab():
    """Demonstrate Magic R&D Lab business."""
    print("="*80)
    print("MAGIC R&D LAB - Advanced Computing as a Service")
    print("="*80)
    print("\nUse our magic R&D machine to create whatever you need!")
    print("\nPricing:")
    print("  💫 Few Hours (2-4 hrs):  $299")
    print("  ⭐ Full Day (24 hrs):    $1,000")
    print("  🌟 Full Week (7 days):   $5,000")
    print("="*80)

    lab = MagicRDLab()

    # Show pricing
    print("\n1. PRICING INFORMATION")
    print("-"*80)
    pricing = lab.get_pricing_info()
    for pkg in pricing["packages"]:
        print(f"\n{pkg['name']} - {pkg['price']}")
        print(f"  Duration: {pkg['duration']}")
        print(f"  {pkg['description']}")
        if 'savings' in pkg:
            print(f"  💰 {pkg['savings']}")

    # Create customers
    print("\n\n2. CUSTOMER ONBOARDING")
    print("-"*80)
    customers = [
        lab.create_customer("Dr. Sarah Chen", "QuantumTech Research", "sarah@quantumtech.edu"),
        lab.create_customer("Alex Martinez", "AI Innovations Inc", "alex@aiinnovations.com"),
        lab.create_customer("Prof. James Wilson", "MIT Physics Dept", "wilson@mit.edu")
    ]

    for customer in customers:
        print(f"✓ {customer.name} from {customer.company}")
        print(f"  Referral code: {customer.referral_code}")

    # Book sessions
    print("\n\n3. BOOKING SESSIONS")
    print("-"*80)
    sessions = [
        lab.book_session(
            customers[0].customer_id,
            RentalPackage.FEW_HOURS,
            "Quantum drug discovery simulation"
        ),
        lab.book_session(
            customers[1].customer_id,
            RentalPackage.FULL_DAY,
            "Train large language model on proprietary data"
        ),
        lab.book_session(
            customers[2].customer_id,
            RentalPackage.FULL_WEEK,
            "Complex particle physics simulations"
        )
    ]

    for session in sessions:
        print(f"\n✓ Session {session.session_id}")
        print(f"  Customer: {session.customer_name}")
        print(f"  Package: {session.package.value}")
        print(f"  Project: {session.project_description}")
        print(f"  Amount: ${session.amount_paid}")
        print(f"  Expires: {session.expires_at.strftime('%Y-%m-%d %H:%M')}")

    # Run computations
    print("\n\n4. RUNNING COMPUTATIONS")
    print("-"*80)

    computations = [
        ("SES000001", "Simulate H2 molecule quantum states"),
        ("SES000001", "Optimize drug binding affinity"),
        ("SES000002", "Train GPT model on medical texts"),
        ("SES000002", "Fine-tune model for diagnosis"),
        ("SES000003", "Simulate particle collisions"),
        ("SES000003", "Analyze decay patterns")
    ]

    for session_id, task in computations:
        result = await lab.run_computation(session_id, task)
        print(f"\n✓ {task}")
        print(f"  Session: {session_id}")
        print(f"  Status: {result['status']}")
        print(f"  Time: {result['computation_time']:.1f}s")

    # Customer dashboards
    print("\n\n5. CUSTOMER DASHBOARDS")
    print("-"*80)

    for customer in customers:
        dashboard = lab.get_customer_dashboard(customer.customer_id)
        print(f"\n{dashboard['name']} - {dashboard['company']}")
        print(f"  Total spent: ${dashboard['total_spent']:.2f}")
        print(f"  Sessions: {dashboard['sessions']['total']} total, {dashboard['sessions']['active']} active")
        print(f"  Computations: {dashboard['usage']['total_computations']}")

        if dashboard['active_sessions']:
            print(f"  Active sessions:")
            for sess in dashboard['active_sessions']:
                print(f"    • {sess['session_id']}: {sess['project']} ({sess['expires_in_hours']:.1f}h remaining)")

    # Business metrics
    print("\n\n6. BUSINESS METRICS")
    print("-"*80)

    metrics = lab.get_business_metrics()
    print(f"\nRevenue: ${metrics['total_revenue']:,.2f}")
    print(f"Customers: {metrics['total_customers']}")
    print(f"Sessions: {metrics['total_sessions']} ({metrics['active_sessions']} active)")
    print(f"Avg revenue/customer: ${metrics['avg_revenue_per_customer']:,.2f}")
    print(f"Total computations: {metrics['total_computations']}")

    print("\nPackage distribution:")
    for package, count in metrics['package_distribution'].items():
        if count > 0:
            print(f"  {package}: {count} bookings")

    print("\n" + "="*80)
    print("MAGIC R&D LAB DEMO COMPLETE")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(demo_magic_rd_lab())
