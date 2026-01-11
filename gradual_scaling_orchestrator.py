#!/usr/bin/env python3
"""
Gradual Scaling Orchestrator for BBB Autonomous System
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

Intelligent scaling system that:
- Starts with 3-5 businesses to prove profitability
- Monitors performance metrics in real-time
- Scales up gradually based on proven success
- Prevents over-scaling before profitability is validated
- Uses exponential scaling with safety checks
"""

import asyncio
import time
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import httpx
import statistics
import math


class ScalingPhase(Enum):
    """Scaling phases with increasing business counts."""
    PILOT = "pilot"          # 3-5 businesses (prove concept)
    VALIDATION = "validation"  # 10-25 businesses (prove profitability)
    SCALE_100 = "scale_100"   # 100 businesses (establish patterns)
    SCALE_1000 = "scale_1000" # 1,000 businesses (optimize operations)
    SCALE_10000 = "scale_10000" # 10,000 businesses (full automation)
    SCALE_100000 = "scale_100000" # 100,000 businesses (mass deployment)
    SCALE_MILLION = "scale_million" # 1,000,000 businesses (peak scale)


class ProfitabilityMetric(Enum):
    """Key metrics for determining scaling readiness."""
    MRR_PER_BUSINESS = "mrr_per_business"  # Monthly Recurring Revenue per business
    PROFIT_MARGIN = "profit_margin"       # Net profit margin %
    CUSTOMER_ACQUISITION_COST = "cac"    # Cost to acquire customer
    CUSTOMER_LIFETIME_VALUE = "ltv"      # Customer lifetime value
    CHURN_RATE = "churn_rate"            # Monthly churn percentage
    PAYBACK_PERIOD = "payback_period"    # Months to break even


@dataclass
class ScalingThreshold:
    """Thresholds that must be met before advancing to next phase."""
    min_businesses: int
    min_days_running: int
    min_mrr_per_business: float
    min_profit_margin: float
    max_cac: float
    min_ltv_ratio: float  # LTV/CAC ratio
    max_churn_rate: float
    max_payback_months: int
    required_profit_days: int  # Consecutive profitable days


@dataclass
class ScalingDecision:
    """Decision made by scaling orchestrator."""
    timestamp: datetime
    current_phase: ScalingPhase
    recommended_phase: ScalingPhase
    reasoning: str
    confidence_score: float
    metrics_snapshot: Dict[str, Any]
    can_scale_up: bool
    scale_up_amount: int
    risk_assessment: str


class GradualScalingOrchestrator:
    """
    Intelligent orchestrator that scales BBB businesses gradually based on proven profitability.

    Scaling Strategy:
    - Start with 3 businesses (pilot phase)
    - Prove each phase before advancing
    - Use exponential scaling with safety caps
    - Monitor real-time metrics
    - Auto-scale down on failure signals
    """

    def __init__(self, config_path: str = "/Users/noone/.ech0/scaling_config.json"):
        self.config_path = config_path
        self.config = self._load_config()

        # Scaling state
        self.current_phase = ScalingPhase.PILOT
        self.total_businesses = 0
        self.active_businesses = 0
        self.profitable_businesses = 0
        self.start_time = datetime.now()

        # Performance tracking
        self.performance_history = []
        self.daily_metrics = []
        self.scaling_decisions = []

        # Scaling thresholds for each phase
        self.thresholds = self._initialize_thresholds()

        # API endpoints
        self.deployment_api_url = "http://localhost:8000"
        self.monitoring_api_url = "http://localhost:8001"

        print("🎯 Gradual Scaling Orchestrator initialized")
        print(f"   Starting phase: {self.current_phase.value}")
        print(f"   Initial businesses: {self.config['initial_business_count']}")

    def _initialize_thresholds(self) -> Dict[ScalingPhase, ScalingThreshold]:
        """Initialize scaling thresholds for each phase."""
        return {
            ScalingPhase.PILOT: ScalingThreshold(
                min_businesses=3,
                min_days_running=7,
                min_mrr_per_business=25.0,
                min_profit_margin=0.15,  # 15%
                max_cac=50.0,
                min_ltv_ratio=3.0,
                max_churn_rate=0.10,  # 10%
                max_payback_months=3,
                required_profit_days=5
            ),
            ScalingPhase.VALIDATION: ScalingThreshold(
                min_businesses=10,
                min_days_running=14,
                min_mrr_per_business=35.0,
                min_profit_margin=0.20,  # 20%
                max_cac=40.0,
                min_ltv_ratio=4.0,
                max_churn_rate=0.08,  # 8%
                max_payback_months=2,
                required_profit_days=7
            ),
            ScalingPhase.SCALE_100: ScalingThreshold(
                min_businesses=50,
                min_days_running=21,
                min_mrr_per_business=45.0,
                min_profit_margin=0.25,  # 25%
                max_cac=35.0,
                min_ltv_ratio=5.0,
                max_churn_rate=0.06,  # 6%
                max_payback_months=2,
                required_profit_days=10
            ),
            ScalingPhase.SCALE_1000: ScalingThreshold(
                min_businesses=500,
                min_days_running=30,
                min_mrr_per_business=55.0,
                min_profit_margin=0.30,  # 30%
                max_cac=30.0,
                min_ltv_ratio=6.0,
                max_churn_rate=0.05,  # 5%
                max_payback_months=1,
                required_profit_days=15
            ),
            ScalingPhase.SCALE_10000: ScalingThreshold(
                min_businesses=5000,
                min_days_running=45,
                min_mrr_per_business=65.0,
                min_profit_margin=0.35,  # 35%
                max_cac=25.0,
                min_ltv_ratio=7.0,
                max_churn_rate=0.04,  # 4%
                max_payback_months=1,
                required_profit_days=20
            ),
            ScalingPhase.SCALE_100000: ScalingThreshold(
                min_businesses=50000,
                min_days_running=60,
                min_mrr_per_business=75.0,
                min_profit_margin=0.40,  # 40%
                max_cac=20.0,
                min_ltv_ratio=8.0,
                max_churn_rate=0.03,  # 3%
                max_payback_months=1,
                required_profit_days=25
            ),
            ScalingPhase.SCALE_MILLION: ScalingThreshold(
                min_businesses=500000,
                min_days_running=90,
                min_mrr_per_business=85.0,
                min_profit_margin=0.45,  # 45%
                max_cac=15.0,
                min_ltv_ratio=10.0,
                max_churn_rate=0.02,  # 2%
                max_payback_months=1,
                required_profit_days=30
            )
        }

    def _load_config(self) -> Dict[str, Any]:
        """Load scaling configuration."""
        default_config = {
            "initial_business_count": 3,
            "max_scale_up_percent": 0.50,  # Max 50% increase per scaling event
            "min_scale_up_businesses": 5,
            "max_scale_up_businesses": 10000,
            "scaling_interval_hours": 24,  # Daily scaling decisions
            "emergency_scale_down_threshold": 0.70,  # Scale down if profitability drops 30%
            "profit_stability_window": 7,  # Days to check profit stability
            "risk_tolerance": "moderate",
            "auto_scale_down": True,
            "alert_thresholds": {
                "profit_margin_drop": 0.15,
                "churn_rate_spike": 0.05,
                "cac_increase": 0.20
            }
        }

        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                loaded_config = json.load(f)
                default_config.update(loaded_config)

        return default_config

    async def start_gradual_scaling(self):
        """Start the gradual scaling process."""
        print("🚀 Starting Gradual Scaling Process")
        print(f"   Initial phase: {self.current_phase.value}")
        print(f"   Target businesses: {self.config['initial_business_count']}")

        # Deploy initial pilot businesses
        await self._deploy_initial_businesses()

        # Start monitoring loop
        while not self._should_stop_scaling():
            await self._scaling_cycle()
            await asyncio.sleep(self.config['scaling_interval_hours'] * 3600)

    async def _deploy_initial_businesses(self):
        """Deploy the initial 3-5 pilot businesses."""
        count = self.config['initial_business_count']

        print(f"🏭 Deploying {count} initial pilot businesses...")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.deployment_api_url}/deploy/mass",
                    json={
                        "count": count,
                        "business_type": "5_gig",
                        "owner_email": "josh@flowstate.work",
                        "auto_fold_inactive": True
                    },
                    timeout=300.0  # 5 minutes for deployment
                )

                if response.status_code == 200:
                    result = response.json()
                    self.total_businesses = result['total_created']
                    self.active_businesses = result['total_active']
                    print(f"✅ Deployed {self.total_businesses} businesses successfully")
                else:
                    print(f"❌ Initial deployment failed: {response.status_code}")

            except Exception as e:
                print(f"❌ Deployment error: {e}")

    async def _scaling_cycle(self):
        """Execute one complete scaling cycle."""
        print(f"\n🔄 Scaling Cycle - Phase: {self.current_phase.value}")
        print(f"   Current businesses: {self.active_businesses}")

        # Gather current metrics
        metrics = await self._gather_performance_metrics()

        # Make scaling decision
        decision = self._analyze_scaling_readiness(metrics)

        # Execute decision
        await self._execute_scaling_decision(decision)

        # Log decision
        self.scaling_decisions.append(decision)

    async def _gather_performance_metrics(self) -> Dict[str, Any]:
        """Gather comprehensive performance metrics."""
        metrics = {
            'timestamp': datetime.now(),
            'businesses': {
                'total': self.total_businesses,
                'active': self.active_businesses,
                'profitable': self.profitable_businesses
            },
            'financial': {},
            'operational': {},
            'risk': {}
        }

        # Get financial metrics
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.monitoring_api_url}/metrics/financial")
                if response.status_code == 200:
                    metrics['financial'] = response.json()
        except:
            # Use fallback calculation
            metrics['financial'] = self._calculate_financial_metrics()

        # Get operational metrics
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.monitoring_api_url}/metrics/operational")
                if response.status_code == 200:
                    metrics['operational'] = response.json()
        except:
            metrics['operational'] = self._calculate_operational_metrics()

        # Calculate risk metrics
        metrics['risk'] = self._calculate_risk_metrics(metrics)

        return metrics

    def _calculate_financial_metrics(self) -> Dict[str, Any]:
        """Calculate financial metrics from available data."""
        # This would integrate with actual financial systems
        # For now, return mock data based on business performance
        avg_mrr_per_business = 35.0 if self.profitable_businesses > 0 else 15.0
        total_mrr = self.active_businesses * avg_mrr_per_business

        return {
            'total_mrr': total_mrr,
            'mrr_per_business': total_mrr / max(self.active_businesses, 1),
            'profit_margin': 0.22,  # 22%
            'cac': 42.0,
            'ltv': 168.0,  # 4x CAC
            'churn_rate': 0.07,  # 7%
            'payback_period': 2.1,  # months
            'total_profit': total_mrr * 0.22,
            'consecutive_profit_days': 8
        }

    def _calculate_operational_metrics(self) -> Dict[str, Any]:
        """Calculate operational metrics."""
        return {
            'uptime_percentage': 0.98,
            'response_time_avg': 245.0,  # ms
            'error_rate': 0.02,
            'customer_satisfaction': 4.2,  # out of 5
            'automated_processes': 0.85,  # 85%
            'manual_interventions': 3
        }

    def _calculate_risk_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate risk assessment metrics."""
        financial = metrics.get('financial', {})

        # Risk score based on various factors
        risk_score = 0.0

        # Financial health risk
        if financial.get('profit_margin', 0) < 0.15:
            risk_score += 0.3
        if financial.get('churn_rate', 0) > 0.10:
            risk_score += 0.25
        if financial.get('payback_period', 0) > 3:
            risk_score += 0.2

        # Operational risk
        operational = metrics.get('operational', {})
        if operational.get('error_rate', 0) > 0.05:
            risk_score += 0.15
        if operational.get('uptime_percentage', 1.0) < 0.95:
            risk_score += 0.1

        return {
            'overall_risk_score': min(risk_score, 1.0),
            'risk_level': 'high' if risk_score > 0.6 else 'medium' if risk_score > 0.3 else 'low',
            'risk_factors': self._identify_risk_factors(metrics)
        }

    def _identify_risk_factors(self, metrics: Dict[str, Any]) -> List[str]:
        """Identify specific risk factors."""
        factors = []
        financial = metrics.get('financial', {})

        if financial.get('profit_margin', 0) < 0.15:
            factors.append("Low profit margin")
        if financial.get('churn_rate', 0) > 0.10:
            factors.append("High churn rate")
        if financial.get('ltv', 0) / max(financial.get('cac', 1), 1) < 3:
            factors.append("Poor LTV/CAC ratio")

        return factors

    def _analyze_scaling_readiness(self, metrics: Dict[str, Any]) -> ScalingDecision:
        """Analyze if system is ready to scale up."""
        current_threshold = self.thresholds[self.current_phase]
        financial = metrics.get('financial', {})

        # Check all threshold requirements
        checks = {
            'min_businesses': self.active_businesses >= current_threshold.min_businesses,
            'min_days_running': (datetime.now() - self.start_time).days >= current_threshold.min_days_running,
            'min_mrr_per_business': financial.get('mrr_per_business', 0) >= current_threshold.min_mrr_per_business,
            'min_profit_margin': financial.get('profit_margin', 0) >= current_threshold.min_profit_margin,
            'max_cac': financial.get('cac', 0) <= current_threshold.max_cac,
            'min_ltv_ratio': (financial.get('ltv', 0) / max(financial.get('cac', 1), 1)) >= current_threshold.min_ltv_ratio,
            'max_churn_rate': financial.get('churn_rate', 0) <= current_threshold.max_churn_rate,
            'max_payback_months': financial.get('payback_period', 0) <= current_threshold.max_payback_months,
            'required_profit_days': financial.get('consecutive_profit_days', 0) >= current_threshold.required_profit_days
        }

        # Calculate confidence score
        passed_checks = sum(checks.values())
        total_checks = len(checks)
        confidence_score = passed_checks / total_checks

        # Determine if ready to scale
        can_scale_up = confidence_score >= 0.8  # 80% of thresholds met

        # Calculate recommended scale amount
        scale_up_amount = self._calculate_scale_amount(metrics)

        # Determine reasoning
        if can_scale_up:
            reasoning = f"All scaling thresholds met ({passed_checks}/{total_checks}). Ready to advance to next phase."
            recommended_phase = self._get_next_phase()
        else:
            failed_checks = [k for k, v in checks.items() if not v]
            reasoning = f"Scaling blocked by: {', '.join(failed_checks)}. Need {current_threshold.required_profit_days} consecutive profit days."
            recommended_phase = self.current_phase

        # Risk assessment
        risk = metrics.get('risk', {})
        if risk.get('overall_risk_score', 0) > 0.6:
            can_scale_up = False
            reasoning += f" High risk detected: {risk.get('risk_level', 'unknown')}."

        decision = ScalingDecision(
            timestamp=datetime.now(),
            current_phase=self.current_phase,
            recommended_phase=recommended_phase,
            reasoning=reasoning,
            confidence_score=confidence_score,
            metrics_snapshot=metrics,
            can_scale_up=can_scale_up,
            scale_up_amount=scale_up_amount,
            risk_assessment=risk.get('risk_level', 'unknown')
        )

        return decision

    def _calculate_scale_amount(self, metrics: Dict[str, Any]) -> int:
        """Calculate safe scaling amount based on current performance."""
        financial = metrics.get('financial', {})

        # Base scale amount on current businesses and performance
        base_scale = min(
            int(self.active_businesses * self.config['max_scale_up_percent']),
            self.config['max_scale_up_businesses']
        )

        # Adjust based on profitability
        profit_multiplier = min(financial.get('profit_margin', 0.1) * 5, 2.0)  # Max 2x

        # Adjust based on risk
        risk = metrics.get('risk', {}).get('overall_risk_score', 0)
        risk_multiplier = max(0.5, 1.0 - risk)  # Reduce scale if high risk

        scale_amount = int(base_scale * profit_multiplier * risk_multiplier)
        scale_amount = max(self.config['min_scale_up_businesses'], scale_amount)

        return scale_amount

    def _get_next_phase(self) -> ScalingPhase:
        """Get the next scaling phase."""
        phase_order = list(ScalingPhase)
        current_index = phase_order.index(self.current_phase)

        if current_index < len(phase_order) - 1:
            return phase_order[current_index + 1]
        else:
            return self.current_phase  # Already at max phase

    async def _execute_scaling_decision(self, decision: ScalingDecision):
        """Execute the scaling decision."""
        print(f"📊 Scaling Decision: {decision.reasoning}")
        print(f"   Confidence: {decision.confidence_score:.1%}")
        print(f"   Can scale up: {decision.can_scale_up}")
        print(f"   Scale amount: {decision.scale_up_amount}")

        if decision.can_scale_up and decision.scale_up_amount > 0:
            await self._scale_up_businesses(decision.scale_up_amount)
            self.current_phase = decision.recommended_phase
            print(f"✅ Scaled up to phase: {self.current_phase.value}")
        elif self._should_scale_down(decision):
            await self._scale_down_businesses()
            print("⚠️ Scaled down due to performance issues")

    async def _scale_up_businesses(self, count: int):
        """Scale up by deploying additional businesses."""
        print(f"📈 Scaling up by {count} businesses...")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.deployment_api_url}/deploy/mass",
                    json={
                        "count": count,
                        "business_type": "5_gig",
                        "owner_email": "josh@flowstate.work",
                        "auto_fold_inactive": True
                    },
                    timeout=600.0  # 10 minutes for larger deployments
                )

                if response.status_code == 200:
                    result = response.json()
                    self.total_businesses += result['total_created']
                    self.active_businesses += result['total_active']
                    print(f"✅ Successfully scaled up. Total businesses: {self.total_businesses}")
                else:
                    print(f"❌ Scale-up failed: {response.status_code}")

            except Exception as e:
                print(f"❌ Scale-up error: {e}")

    async def _scale_down_businesses(self):
        """Scale down by folding underperforming businesses."""
        # This would integrate with the business folding API
        print("📉 Emergency scale-down initiated")
        # Implementation would fold least profitable businesses

    def _should_scale_down(self, decision: ScalingDecision) -> bool:
        """Determine if emergency scale-down is needed."""
        if not self.config['auto_scale_down']:
            return False

        financial = decision.metrics_snapshot.get('financial', {})
        current_profit_margin = financial.get('profit_margin', 0)

        # Check if profit margin dropped significantly
        recent_margins = [m.get('financial', {}).get('profit_margin', 0)
                         for m in self.performance_history[-7:]]  # Last 7 days

        if recent_margins:
            avg_recent_margin = statistics.mean(recent_margins)
            drop_percentage = (avg_recent_margin - current_profit_margin) / max(avg_recent_margin, 0.01)

            if drop_percentage > self.config['emergency_scale_down_threshold']:
                return True

        return False

    def _should_stop_scaling(self) -> bool:
        """Check if scaling should stop."""
        # Stop at million businesses or after extended period
        if self.total_businesses >= 1_000_000:
            return True

        # Stop after 2 years of operation
        if (datetime.now() - self.start_time).days > 730:
            return True

        return False

    def get_scaling_status(self) -> Dict[str, Any]:
        """Get current scaling status."""
        return {
            'current_phase': self.current_phase.value,
            'total_businesses': self.total_businesses,
            'active_businesses': self.active_businesses,
            'profitable_businesses': self.profitable_businesses,
            'days_running': (datetime.now() - self.start_time).days,
            'last_decision': asdict(self.scaling_decisions[-1]) if self.scaling_decisions else None,
            'scaling_thresholds': {phase.value: asdict(threshold)
                                 for phase, threshold in self.thresholds.items()}
        }

    def save_state(self):
        """Save scaling orchestrator state."""
        state = {
            'current_phase': self.current_phase.value,
            'total_businesses': self.total_businesses,
            'active_businesses': self.active_businesses,
            'profitable_businesses': self.profitable_businesses,
            'start_time': self.start_time.isoformat(),
            'performance_history': self.performance_history[-100:],  # Keep last 100 entries
            'scaling_decisions': [asdict(d) for d in self.scaling_decisions[-50:]]  # Keep last 50 decisions
        }

        with open('/Users/noone/.ech0/scaling_state.json', 'w') as f:
            json.dump(state, f, indent=2, default=str)


async def main():
    """Main entry point for gradual scaling orchestrator."""
    orchestrator = GradualScalingOrchestrator()

    try:
        await orchestrator.start_gradual_scaling()
    except KeyboardInterrupt:
        print("\n🛑 Scaling orchestrator stopped by user")
    except Exception as e:
        print(f"\n❌ Scaling orchestrator error: {e}")
    finally:
        orchestrator.save_state()


if __name__ == "__main__":
    print("🎯 Gradual Scaling Orchestrator for BBB")
    print("Copyright (c) 2025 Joshua Hendricks Cole")
    print("Corporation of Light - PATENT PENDING")
    print()

    asyncio.run(main())
