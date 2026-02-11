"""
Magic R&D Lab Rental Business - Advanced Computing as a Service
================================================================

Turnkey BBB business allowing companies to rent time on our advanced
R&D computing platform. Use our "magic machine" to create whatever
you need - from quantum simulations to AI models to complex analysis.

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
from collections import Counter

logger = logging.getLogger(__name__)


class RentalPackage(Enum):
    """R&D Lab rental packages."""
    FEW_HOURS = "few_hours"    # 2-4 hours - $299
    FULL_DAY = "full_day"      # 24 hours - $1,000
    FULL_WEEK = "full_week"    # 7 days - $5,000


class JobPriority(Enum):
    """Job queue priority levels."""
    STANDARD = "standard"      # Standard queue
    EXPRESS = "express"        # Priority processing (+50%)
    DEDICATED = "dedicated"    # Exclusive time slot (+100%)
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class SubscriptionTier(Enum):
    """Subscription tier levels."""
    RESEARCH = "research"
    STARTUP = "startup"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    DEDICATED = "dedicated"


@dataclass
class PricingPlan:
    """Pricing plan for QuLab rental."""
    tier: SubscriptionTier
    base_price: Decimal  # Monthly base
    per_qubit_hour: Decimal
    per_simulation_minute: Decimal
    priority_multiplier: float
    included_hours: int  # Free hours per month
    max_qubits: int
    queue_priority: JobPriority
    support_level: str

    def calculate_job_cost(
        self,
        num_qubits: int,
        simulation_minutes: float,
        priority: JobPriority
    ) -> Decimal:
        """Calculate cost for a quantum job."""
        # Base cost
        qubit_hours = Decimal(num_qubits * simulation_minutes / 60)
        cost = qubit_hours * self.per_qubit_hour
        cost += Decimal(simulation_minutes) * self.per_simulation_minute

        # Priority multiplier
        priority_costs = {
            JobPriority.LOW: 0.7,
            JobPriority.NORMAL: 1.0,
            JobPriority.HIGH: 1.5,
            JobPriority.URGENT: 2.5,
            JobPriority.DEDICATED: 5.0
        }
        cost *= Decimal(str(priority_costs[priority]))

        return cost.quantize(Decimal('0.01'))


# Pricing plans
PRICING_PLANS = {
    SubscriptionTier.RESEARCH: PricingPlan(
        tier=SubscriptionTier.RESEARCH,
        base_price=Decimal('497.00'),
        per_qubit_hour=Decimal('2.50'),
        per_simulation_minute=Decimal('0.50'),
        priority_multiplier=1.0,
        included_hours=20,
        max_qubits=20,
        queue_priority=JobPriority.NORMAL,
        support_level="Email support (48h response)"
    ),
    SubscriptionTier.STARTUP: PricingPlan(
        tier=SubscriptionTier.STARTUP,
        base_price=Decimal('1497.00'),
        per_qubit_hour=Decimal('2.00'),
        per_simulation_minute=Decimal('0.40'),
        priority_multiplier=1.2,
        included_hours=100,
        max_qubits=35,
        queue_priority=JobPriority.HIGH,
        support_level="Email + Chat (24h response)"
    ),
    SubscriptionTier.PROFESSIONAL: PricingPlan(
        tier=SubscriptionTier.PROFESSIONAL,
        base_price=Decimal('4997.00'),
        per_qubit_hour=Decimal('1.50'),
        per_simulation_minute=Decimal('0.30'),
        priority_multiplier=1.5,
        included_hours=500,
        max_qubits=50,
        queue_priority=JobPriority.HIGH,
        support_level="Priority support (12h response)"
    ),
    SubscriptionTier.ENTERPRISE: PricingPlan(
        tier=SubscriptionTier.ENTERPRISE,
        base_price=Decimal('14997.00'),
        per_qubit_hour=Decimal('1.00'),
        per_simulation_minute=Decimal('0.20'),
        priority_multiplier=2.0,
        included_hours=2000,
        max_qubits=50,
        queue_priority=JobPriority.URGENT,
        support_level="24/7 dedicated support"
    ),
    SubscriptionTier.DEDICATED: PricingPlan(
        tier=SubscriptionTier.DEDICATED,
        base_price=Decimal('49997.00'),
        per_qubit_hour=Decimal('0.50'),
        per_simulation_minute=Decimal('0.10'),
        priority_multiplier=5.0,
        included_hours=10000,
        max_qubits=50,
        queue_priority=JobPriority.DEDICATED,
        support_level="24/7 white-glove support + dedicated scientist"
    )
}


@dataclass
class QuantumJob:
    """Quantum computing job."""
    job_id: str
    customer_id: str
    num_qubits: int
    circuit_description: str
    priority: JobPriority
    submitted_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "queued"  # queued, running, completed, failed
    result: Optional[Dict] = None
    cost: Decimal = Decimal('0.00')
    simulation_minutes: float = 0.0


@dataclass
class CustomerAccount:
    """Customer account for QuLab rental."""
    customer_id: str
    company_name: str
    tier: SubscriptionTier
    billing_email: str
    created_at: datetime = field(default_factory=datetime.now)

    # Usage tracking
    current_period_start: datetime = field(default_factory=datetime.now)
    qubit_hours_used: float = 0.0
    jobs_submitted: int = 0
    total_spent: Decimal = Decimal('0.00')

    # Billing
    subscription_status: str = "active"  # active, suspended, cancelled
    payment_method: Optional[str] = None
    last_invoice_date: Optional[datetime] = None


class QuLabRentalBusiness:
    """
    R&D Lab as a Service - Quantum computing rental business.

    Allows companies to rent time on QuLab Infinite for quantum computing tasks.
    """

    def __init__(self):
        self.customers: Dict[str, CustomerAccount] = {}
        self.jobs: List[QuantumJob] = []
        self.job_queue: List[QuantumJob] = []
        self.revenue = Decimal('0.00')
        self.total_qubit_hours = 0.0

    def create_customer(
        self,
        company_name: str,
        tier: SubscriptionTier,
        billing_email: str
    ) -> CustomerAccount:
        """Create new customer account."""
        customer_id = f"cust_{len(self.customers) + 1:06d}"

        customer = CustomerAccount(
            customer_id=customer_id,
            company_name=company_name,
            tier=tier,
            billing_email=billing_email
        )

        self.customers[customer_id] = customer

        logger.info(f"Created customer: {company_name} ({tier.value} tier)")
        return customer

    def submit_job(
        self,
        customer_id: str,
        num_qubits: int,
        circuit_description: str,
        priority: Optional[JobPriority] = None
    ) -> QuantumJob:
        """Submit quantum computing job."""
        customer = self.customers.get(customer_id)
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")

        plan = PRICING_PLANS[customer.tier]

        # Check qubit limit
        if num_qubits > plan.max_qubits:
            raise ValueError(
                f"Job requires {num_qubits} qubits but tier limit is {plan.max_qubits}"
            )

        # Default priority based on tier
        if priority is None:
            priority = plan.queue_priority

        # Create job
        job_id = f"job_{len(self.jobs) + 1:08d}"
        job = QuantumJob(
            job_id=job_id,
            customer_id=customer_id,
            num_qubits=num_qubits,
            circuit_description=circuit_description,
            priority=priority,
            submitted_at=datetime.now()
        )

        self.jobs.append(job)
        self.job_queue.append(job)

        # Sort queue by priority
        priority_order = {
            JobPriority.DEDICATED: 0,
            JobPriority.URGENT: 1,
            JobPriority.HIGH: 2,
            JobPriority.NORMAL: 3,
            JobPriority.LOW: 4
        }
        self.job_queue.sort(key=lambda j: priority_order[j.priority])

        customer.jobs_submitted += 1

        logger.info(
            f"Job {job_id} submitted: {num_qubits} qubits, "
            f"priority {priority.value}"
        )

        return job

    async def execute_job(self, job: QuantumJob) -> Dict:
        """Execute quantum job (simulated)."""
        customer = self.customers[job.customer_id]
        plan = PRICING_PLANS[customer.tier]

        # Simulate execution time based on qubit count
        simulation_minutes = job.num_qubits * 0.5  # 30s per qubit

        job.status = "running"
        job.started_at = datetime.now()

        logger.info(f"Executing job {job.job_id}...")

        # Simulate quantum computation
        await asyncio.sleep(min(simulation_minutes * 0.1, 5.0))  # Capped for demo

        job.status = "completed"
        job.completed_at = datetime.now()
        job.simulation_minutes = simulation_minutes

        # Calculate cost
        job.cost = plan.calculate_job_cost(
            job.num_qubits,
            simulation_minutes,
            job.priority
        )

        # Update customer usage
        qubit_hours = job.num_qubits * simulation_minutes / 60
        customer.qubit_hours_used += qubit_hours
        customer.total_spent += job.cost

        self.total_qubit_hours += qubit_hours
        self.revenue += job.cost

        # Simulated result
        job.result = {
            "success": True,
            "qubit_count": job.num_qubits,
            "circuit": job.circuit_description,
            "execution_time": simulation_minutes,
            "measurements": [0, 1] * (job.num_qubits // 2)
        }

        logger.info(
            f"Job {job.job_id} completed: "
            f"{simulation_minutes:.2f} min, "
            f"${job.cost}"
        )

        return job.result

    async def process_queue(self, max_concurrent: int = 3) -> None:
        """Process job queue."""
        logger.info(f"Processing queue with {len(self.job_queue)} jobs...")

        tasks = []
        while self.job_queue and len(tasks) < max_concurrent:
            job = self.job_queue.pop(0)
            tasks.append(self.execute_job(job))

        if tasks:
            await asyncio.gather(*tasks)

    def generate_invoice(self, customer_id: str) -> Dict[str, Any]:
        """Generate monthly invoice for customer."""
        customer = self.customers.get(customer_id)
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")

        plan = PRICING_PLANS[customer.tier]

        # Calculate charges
        base_charge = plan.base_price

        # Usage charges (beyond included hours)
        included_qubit_hours = plan.included_hours
        overage_hours = max(0, customer.qubit_hours_used - included_qubit_hours)
        overage_charge = Decimal(str(overage_hours)) * plan.per_qubit_hour

        total = base_charge + overage_charge

        invoice = {
            "invoice_id": f"inv_{customer_id}_{datetime.now().strftime('%Y%m')}",
            "customer_id": customer_id,
            "company_name": customer.company_name,
            "billing_email": customer.billing_email,
            "period_start": customer.current_period_start.isoformat(),
            "period_end": datetime.now().isoformat(),
            "line_items": [
                {
                    "description": f"{customer.tier.value.title()} Plan",
                    "amount": float(base_charge)
                },
                {
                    "description": f"Overage: {overage_hours:.2f} qubit-hours @ ${plan.per_qubit_hour}/hr",
                    "amount": float(overage_charge)
                }
            ],
            "subtotal": float(total),
            "tax": float(total * Decimal('0.08')),  # 8% tax
            "total": float(total * Decimal('1.08')),
            "jobs_count": customer.jobs_submitted,
            "qubit_hours_used": customer.qubit_hours_used,
            "included_hours": included_qubit_hours,
            "overage_hours": overage_hours
        }

        customer.last_invoice_date = datetime.now()

        return invoice

    def get_usage_analytics(self, customer_id: str) -> Dict[str, Any]:
        """Get usage analytics for customer."""
        customer = self.customers.get(customer_id)
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")

        plan = PRICING_PLANS[customer.tier]
        customer_jobs = [j for j in self.jobs if j.customer_id == customer_id]

        completed_jobs = [j for j in customer_jobs if j.status == "completed"]
        failed_jobs = [j for j in customer_jobs if j.status == "failed"]

        return {
            "customer_id": customer_id,
            "company_name": customer.company_name,
            "tier": customer.tier.value,
            "subscription_status": customer.subscription_status,
            "current_period": {
                "start": customer.current_period_start.isoformat(),
                "qubit_hours_used": customer.qubit_hours_used,
                "included_hours": plan.included_hours,
                "overage_hours": max(0, customer.qubit_hours_used - plan.included_hours),
                "jobs_submitted": customer.jobs_submitted,
                "jobs_completed": len(completed_jobs),
                "jobs_failed": len(failed_jobs),
                "total_spent": float(customer.total_spent)
            },
            "usage_breakdown": {
                "avg_qubits_per_job": sum(j.num_qubits for j in completed_jobs) / max(1, len(completed_jobs)),
                "total_simulation_minutes": sum(j.simulation_minutes for j in completed_jobs),
                "most_used_priority": max(
                    [j.priority.value for j in customer_jobs],
                    key=[j.priority.value for j in customer_jobs].count
                ) if customer_jobs else "none"
            },
            "recommendations": self._generate_recommendations(customer)
        }

    def _generate_recommendations(self, customer: CustomerAccount) -> List[str]:
        """Generate tier upgrade/downgrade recommendations."""
        recommendations = []

        plan = PRICING_PLANS[customer.tier]
        overage_hours = max(0, customer.qubit_hours_used - plan.included_hours)

        # Check if customer should upgrade
        if overage_hours > plan.included_hours * 0.5:
            next_tier = self._get_next_tier(customer.tier)
            if next_tier:
                recommendations.append(
                    f"Consider upgrading to {next_tier.value} tier for better value "
                    f"(current overage: {overage_hours:.1f} hours)"
                )

        # Check if customer should downgrade
        elif customer.qubit_hours_used < plan.included_hours * 0.3:
            prev_tier = self._get_previous_tier(customer.tier)
            if prev_tier:
                recommendations.append(
                    f"Consider downgrading to {prev_tier.value} tier to save costs "
                    f"(using only {customer.qubit_hours_used:.1f} of {plan.included_hours} included hours)"
                )

        return recommendations

    def _get_next_tier(self, current: SubscriptionTier) -> Optional[SubscriptionTier]:
        """Get next subscription tier."""
        tier_order = [
            SubscriptionTier.RESEARCH,
            SubscriptionTier.STARTUP,
            SubscriptionTier.PROFESSIONAL,
            SubscriptionTier.ENTERPRISE,
            SubscriptionTier.DEDICATED
        ]
        try:
            idx = tier_order.index(current)
            return tier_order[idx + 1] if idx < len(tier_order) - 1 else None
        except ValueError:
            return None

    def _get_previous_tier(self, current: SubscriptionTier) -> Optional[SubscriptionTier]:
        """Get previous subscription tier."""
        tier_order = [
            SubscriptionTier.RESEARCH,
            SubscriptionTier.STARTUP,
            SubscriptionTier.PROFESSIONAL,
            SubscriptionTier.ENTERPRISE,
            SubscriptionTier.DEDICATED
        ]
        try:
            idx = tier_order.index(current)
            return tier_order[idx - 1] if idx > 0 else None
        except ValueError:
            return None

    def get_business_metrics(self) -> Dict[str, Any]:
        """Get overall business metrics."""
        tier_counts = Counter([c.tier for c in self.customers.values()])

        return {
            "total_customers": len(self.customers),
            "active_customers": len([c for c in self.customers.values() if c.subscription_status == "active"]),
            "tier_distribution": {
                tier.value: tier_counts.get(tier, 0)
                for tier in SubscriptionTier
            },
            "total_jobs": len(self.jobs),
            "completed_jobs": len([j for j in self.jobs if j.status == "completed"]),
            "total_qubit_hours": self.total_qubit_hours,
            "total_revenue": float(self.revenue),
            "avg_revenue_per_customer": float(self.revenue / max(1, len(self.customers))),
            "queue_length": len(self.job_queue)
        }


# Demonstration
async def demo_qulab_rental():
    """Demonstrate QuLab rental business."""
    print("="*80)
    print("QuLab Infinite Rental Business Demo")
    print("R&D Lab as a Service")
    print("="*80)

    business = QuLabRentalBusiness()

    # Create customers
    print("\n1. Creating customers...")
    print("-"*80)

    customers = [
        business.create_customer("QuantumTech Research", SubscriptionTier.RESEARCH, "research@quantumtech.edu"),
        business.create_customer("AI Startup Inc", SubscriptionTier.STARTUP, "billing@aistartup.com"),
        business.create_customer("Enterprise Corp", SubscriptionTier.ENTERPRISE, "finance@enterprise.com")
    ]

    for customer in customers:
        plan = PRICING_PLANS[customer.tier]
        print(f"✓ {customer.company_name}")
        print(f"  Tier: {customer.tier.value}")
        print(f"  Base: ${plan.base_price}/month")
        print(f"  Included: {plan.included_hours} qubit-hours")
        print(f"  Max qubits: {plan.max_qubits}")

    # Submit jobs
    print("\n2. Submitting quantum jobs...")
    print("-"*80)

    jobs = [
        business.submit_job(customers[0].customer_id, 10, "VQE for H2 molecule", JobPriority.NORMAL),
        business.submit_job(customers[1].customer_id, 20, "QAOA max-cut problem", JobPriority.HIGH),
        business.submit_job(customers[2].customer_id, 35, "Quantum ML classification", JobPriority.URGENT),
        business.submit_job(customers[0].customer_id, 15, "Grover's algorithm", JobPriority.NORMAL),
        business.submit_job(customers[1].customer_id, 25, "Quantum annealing", JobPriority.HIGH)
    ]

    for job in jobs:
        print(f"✓ Job {job.job_id}: {job.num_qubits} qubits, priority {job.priority.value}")

    # Process queue
    print("\n3. Processing job queue...")
    print("-"*80)

    await business.process_queue(max_concurrent=3)

    # Generate invoices
    print("\n4. Generating invoices...")
    print("-"*80)

    for customer in customers:
        invoice = business.generate_invoice(customer.customer_id)
        print(f"\nInvoice for {customer.company_name}:")
        print(f"  Jobs: {invoice['jobs_count']}")
        print(f"  Qubit-hours: {invoice['qubit_hours_used']:.2f}")
        print(f"  Overage: {invoice['overage_hours']:.2f} hours")
        print(f"  Total: ${invoice['total']:.2f}")

    # Usage analytics
    print("\n5. Usage Analytics...")
    print("-"*80)

    for customer in customers:
        analytics = business.get_usage_analytics(customer.customer_id)
        print(f"\n{analytics['company_name']} ({analytics['tier']}):")
        print(f"  Qubit-hours used: {analytics['current_period']['qubit_hours_used']:.2f}")
        print(f"  Jobs completed: {analytics['current_period']['jobs_completed']}")
        print(f"  Total spent: ${analytics['current_period']['total_spent']:.2f}")

        if analytics['recommendations']:
            print(f"  Recommendations:")
            for rec in analytics['recommendations']:
                print(f"    • {rec}")

    # Business metrics
    print("\n6. Business Metrics...")
    print("-"*80)

    metrics = business.get_business_metrics()
    print(f"Total customers: {metrics['total_customers']}")
    print(f"Total jobs: {metrics['total_jobs']}")
    print(f"Total qubit-hours: {metrics['total_qubit_hours']:.2f}")
    print(f"Total revenue: ${metrics['total_revenue']:.2f}")
    print(f"Avg revenue/customer: ${metrics['avg_revenue_per_customer']:.2f}")

    print("\nTier distribution:")
    for tier, count in metrics['tier_distribution'].items():
        if count > 0:
            print(f"  {tier}: {count} customers")

    print("\n" + "="*80)
    print("Demo complete!")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(demo_qulab_rental())
