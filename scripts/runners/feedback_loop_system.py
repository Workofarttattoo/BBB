#!/usr/bin/env python3
"""
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

FEEDBACK LOOP SYSTEM - Continuous Learning and Improvement

Implements a comprehensive feedback loop where all agents:
- Monitor their own performance
- Learn from successes and failures
- Share improvements with the hive
- Adapt strategies based on feedback
- Evolve capabilities over time
"""

import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import random

from hive_mind_coordinator import HiveMindCoordinator, AgentType, HiveMessage, DecisionPriority

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
LOG = logging.getLogger(__name__)


class FeedbackType(Enum):
    """Types of feedback in the system"""
    SUCCESS = "success"
    FAILURE = "failure"
    IMPROVEMENT = "improvement"
    PERFORMANCE_METRIC = "performance_metric"
    USER_FEEDBACK = "user_feedback"
    SYSTEM_OBSERVATION = "system_observation"


@dataclass
class FeedbackEvent:
    """A single feedback event in the system"""
    agent_id: str
    feedback_type: FeedbackType
    timestamp: float
    metric_name: str
    metric_value: float
    context: Dict[str, Any]
    improvement_suggestion: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            'agent_id': self.agent_id,
            'feedback_type': self.feedback_type.value,
            'timestamp': self.timestamp,
            'metric_name': self.metric_name,
            'metric_value': self.metric_value,
            'context': self.context,
            'improvement_suggestion': self.improvement_suggestion
        }


@dataclass
class AgentPerformanceTracker:
    """Tracks an agent's performance over time"""
    agent_id: str
    metrics: Dict[str, List[float]] = field(default_factory=dict)
    successes: int = 0
    failures: int = 0
    improvements_applied: List[str] = field(default_factory=list)
    feedback_received: List[FeedbackEvent] = field(default_factory=list)
    learning_rate: float = 0.1  # How quickly the agent adapts

    def add_metric(self, metric_name: str, value: float):
        """Add a performance metric"""
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        self.metrics[metric_name].append(value)

    def get_metric_trend(self, metric_name: str, window: int = 10) -> str:
        """Get trend for a metric (improving, declining, stable)"""
        if metric_name not in self.metrics or len(self.metrics[metric_name]) < 2:
            return "unknown"

        recent = self.metrics[metric_name][-window:]
        if len(recent) < 2:
            return "insufficient_data"

        # Calculate trend
        first_half = sum(recent[:len(recent)//2]) / (len(recent)//2)
        second_half = sum(recent[len(recent)//2:]) / (len(recent) - len(recent)//2)

        change_pct = ((second_half - first_half) / first_half * 100) if first_half > 0 else 0

        if change_pct > 5:
            return "improving"
        elif change_pct < -5:
            return "declining"
        else:
            return "stable"

    def success_rate(self) -> float:
        """Calculate success rate"""
        total = self.successes + self.failures
        return self.successes / total if total > 0 else 0.0


class FeedbackLoopSystem:
    """
    Comprehensive feedback loop for continuous improvement

    Features:
    - Real-time performance monitoring
    - Automatic success/failure detection
    - Cross-agent learning propagation
    - Adaptive strategy adjustment
    - Performance trend analysis
    - Improvement recommendation engine
    """

    def __init__(self, hive: HiveMindCoordinator):
        self.hive = hive
        self.performance_trackers: Dict[str, AgentPerformanceTracker] = {}
        self.feedback_history: List[FeedbackEvent] = []
        self.improvement_patterns: Dict[str, List[str]] = {}  # What works for each metric

        LOG.warning("🔄 FEEDBACK LOOP SYSTEM INITIALIZED")
        LOG.info("   Continuous learning and improvement enabled for all agents")

    def register_agent_tracker(self, agent_id: str):
        """Register performance tracker for an agent"""
        if agent_id not in self.performance_trackers:
            self.performance_trackers[agent_id] = AgentPerformanceTracker(agent_id=agent_id)
            LOG.info(f"Performance tracker registered for {agent_id}")

    def record_feedback(self, feedback: FeedbackEvent):
        """Record a feedback event"""
        self.feedback_history.append(feedback)

        # Update agent's tracker
        if feedback.agent_id not in self.performance_trackers:
            self.register_agent_tracker(feedback.agent_id)

        tracker = self.performance_trackers[feedback.agent_id]
        tracker.feedback_received.append(feedback)

        # Update metrics
        if feedback.feedback_type == FeedbackType.PERFORMANCE_METRIC:
            tracker.add_metric(feedback.metric_name, feedback.metric_value)

        elif feedback.feedback_type == FeedbackType.SUCCESS:
            tracker.successes += 1
            tracker.add_metric('success_rate', tracker.success_rate())

            # Learn from success
            self._learn_from_success(feedback)

        elif feedback.feedback_type == FeedbackType.FAILURE:
            tracker.failures += 1
            tracker.add_metric('success_rate', tracker.success_rate())

            # Learn from failure
            self._learn_from_failure(feedback)

        elif feedback.feedback_type == FeedbackType.IMPROVEMENT:
            tracker.improvements_applied.append(feedback.improvement_suggestion or "unknown")

        # Check if agent needs help
        self._check_and_provide_assistance(feedback.agent_id)

    def _learn_from_success(self, feedback: FeedbackEvent):
        """Learn from successful actions"""
        # Record what worked
        context_key = feedback.context.get('action_type', 'unknown')
        if context_key not in self.improvement_patterns:
            self.improvement_patterns[context_key] = []

        self.improvement_patterns[context_key].append(
            feedback.context.get('strategy', 'unknown_strategy')
        )

        # Share success with hive
        self.hive.share_learning(
            feedback.agent_id,
            "successful_strategy",
            {
                'action': context_key,
                'strategy': feedback.context.get('strategy', 'unknown'),
                'metric': feedback.metric_name,
                'value': feedback.metric_value,
                'timestamp': feedback.timestamp
            }
        )

        LOG.info(f"✓ {feedback.agent_id} success learned and shared with hive")

    def _learn_from_failure(self, feedback: FeedbackEvent):
        """Learn from failures to avoid repeating them"""
        # Share failure with hive
        self.hive.share_learning(
            feedback.agent_id,
            "failed_strategy",
            {
                'action': feedback.context.get('action_type', 'unknown'),
                'strategy': feedback.context.get('strategy', 'unknown'),
                'metric': feedback.metric_name,
                'value': feedback.metric_value,
                'reason': feedback.context.get('failure_reason', 'unknown'),
                'timestamp': feedback.timestamp
            }
        )

        LOG.info(f"✗ {feedback.agent_id} failure learned, hive will avoid this strategy")

    def _check_and_provide_assistance(self, agent_id: str):
        """Check if agent is struggling and provide assistance"""
        tracker = self.performance_trackers[agent_id]

        # Check if performance is declining
        for metric_name, values in tracker.metrics.items():
            if len(values) < 5:
                continue

            trend = tracker.get_metric_trend(metric_name)

            if trend == "declining":
                LOG.warning(f"⚠️  {agent_id} performance declining in {metric_name}")

                # Generate improvement recommendation
                recommendation = self._generate_improvement_recommendation(
                    agent_id, metric_name, tracker
                )

                if recommendation:
                    # Send improvement message to agent
                    message = HiveMessage(
                        sender="feedback_loop_system",
                        agent_type=AgentType.ECH0_OVERSEER,
                        message_type="improvement_recommendation",
                        payload={
                            'target_agent': agent_id,
                            'metric': metric_name,
                            'trend': trend,
                            'recommendation': recommendation
                        },
                        priority=DecisionPriority.HIGH,
                        timestamp=time.time(),
                        requires_consensus=False
                    )

                    self.hive.send_message(message)
                    LOG.info(f"   Sent improvement recommendation to {agent_id}")

    def _generate_improvement_recommendation(
        self,
        agent_id: str,
        metric_name: str,
        tracker: AgentPerformanceTracker
    ) -> Optional[str]:
        """Generate improvement recommendation based on hive knowledge"""

        # Look at successful strategies from other agents
        successful_strategies = self.hive.shared_knowledge.get('successful_strategies', [])

        for strategy in successful_strategies:
            # Find strategies that improved similar metrics
            if strategy.get('data', {}).get('metric') == metric_name:
                strategy_name = strategy.get('data', {}).get('strategy', 'unknown')

                # Check if this agent hasn't tried this yet
                if strategy_name not in tracker.improvements_applied:
                    return f"Try '{strategy_name}' - worked well for {strategy.get('agent_id')}"

        return None

    def get_agent_performance_report(self, agent_id: str) -> Dict:
        """Get comprehensive performance report for an agent"""
        if agent_id not in self.performance_trackers:
            return {"error": "Agent not tracked"}

        tracker = self.performance_trackers[agent_id]

        # Calculate trends for all metrics
        trends = {}
        for metric_name in tracker.metrics.keys():
            trends[metric_name] = tracker.get_metric_trend(metric_name)

        return {
            'agent_id': agent_id,
            'success_rate': tracker.success_rate(),
            'successes': tracker.successes,
            'failures': tracker.failures,
            'metrics': {
                name: {
                    'current': values[-1] if values else 0,
                    'average': sum(values) / len(values) if values else 0,
                    'trend': trends.get(name, 'unknown')
                }
                for name, values in tracker.metrics.items()
            },
            'improvements_applied': len(tracker.improvements_applied),
            'feedback_events': len(tracker.feedback_received),
            'learning_rate': tracker.learning_rate
        }

    def get_hive_performance_summary(self) -> Dict:
        """Get performance summary for entire hive"""
        total_agents = len(self.performance_trackers)

        if total_agents == 0:
            return {"message": "No agents tracked yet"}

        # Aggregate stats
        total_successes = sum(t.successes for t in self.performance_trackers.values())
        total_failures = sum(t.failures for t in self.performance_trackers.values())
        avg_success_rate = sum(t.success_rate() for t in self.performance_trackers.values()) / total_agents

        # Find top performers
        top_performers = sorted(
            self.performance_trackers.items(),
            key=lambda x: x[1].success_rate(),
            reverse=True
        )[:3]

        # Find agents needing help
        struggling_agents = []
        for agent_id, tracker in self.performance_trackers.items():
            for metric_name in tracker.metrics.keys():
                if tracker.get_metric_trend(metric_name) == "declining":
                    struggling_agents.append(agent_id)
                    break

        return {
            'total_agents_tracked': total_agents,
            'total_successes': total_successes,
            'total_failures': total_failures,
            'average_success_rate': avg_success_rate,
            'total_feedback_events': len(self.feedback_history),
            'improvement_patterns_learned': len(self.improvement_patterns),
            'top_performers': [
                {'agent_id': aid, 'success_rate': tracker.success_rate()}
                for aid, tracker in top_performers
            ],
            'agents_needing_help': struggling_agents,
            'hive_knowledge': {
                'successful_strategies': len(self.hive.shared_knowledge.get('successful_strategies', [])),
                'failed_strategies': len(self.hive.shared_knowledge.get('failed_strategies', [])),
                'customer_insights': len(self.hive.shared_knowledge.get('customer_insights', []))
            }
        }

    def simulate_feedback_loop(self, duration_days: int = 30):
        """Simulate feedback loop over time"""
        LOG.info(f"Simulating feedback loop for {duration_days} days...")

        # Register some agents
        test_agents = [
            "acquisition_agent_1",
            "product_agent_1",
            "optimization_agent_1",
            "monitoring_agent_1"
        ]

        for agent_id in test_agents:
            self.register_agent_tracker(agent_id)

        # Simulate daily feedback
        for day in range(duration_days):
            for agent_id in test_agents:
                # Simulate some successes and failures
                num_actions = random.randint(5, 15)

                for _ in range(num_actions):
                    # Success rate improves over time (learning)
                    base_success_rate = 0.60
                    learning_bonus = (day / duration_days) * 0.20  # Up to 20% improvement
                    success_rate = min(base_success_rate + learning_bonus, 0.95)

                    is_success = random.random() < success_rate

                    feedback = FeedbackEvent(
                        agent_id=agent_id,
                        feedback_type=FeedbackType.SUCCESS if is_success else FeedbackType.FAILURE,
                        timestamp=time.time() + (day * 86400),
                        metric_name="action_success_rate",
                        metric_value=1.0 if is_success else 0.0,
                        context={
                            'action_type': random.choice(['acquisition', 'conversion', 'retention']),
                            'strategy': random.choice(['strategy_a', 'strategy_b', 'strategy_c']),
                            'day': day
                        }
                    )

                    self.record_feedback(feedback)

                # Simulate performance metrics
                conversion_rate = 0.02 + (day / duration_days) * 0.03  # Improves from 2% to 5%
                metric_feedback = FeedbackEvent(
                    agent_id=agent_id,
                    feedback_type=FeedbackType.PERFORMANCE_METRIC,
                    timestamp=time.time() + (day * 86400),
                    metric_name="conversion_rate",
                    metric_value=conversion_rate + random.uniform(-0.005, 0.005),
                    context={'day': day}
                )

                self.record_feedback(metric_feedback)

        LOG.info(f"Simulation complete for {duration_days} days")

        # Print summary
        summary = self.get_hive_performance_summary()
        LOG.info("")
        LOG.info("=== FEEDBACK LOOP SIMULATION RESULTS ===")
        LOG.info(f"Total Agents: {summary['total_agents_tracked']}")
        LOG.info(f"Total Successes: {summary['total_successes']}")
        LOG.info(f"Total Failures: {summary['total_failures']}")
        LOG.info(f"Average Success Rate: {summary['average_success_rate']:.1%}")
        LOG.info(f"Feedback Events Processed: {summary['total_feedback_events']}")
        LOG.info(f"Improvement Patterns Learned: {summary['improvement_patterns_learned']}")
        LOG.info("")


if __name__ == "__main__":
    """Demonstrate feedback loop system"""

    LOG.info("=" * 80)
    LOG.info("FEEDBACK LOOP SYSTEM DEMONSTRATION")
    LOG.info("=" * 80)

    # Initialize hive
    hive = HiveMindCoordinator()

    # Initialize feedback loop
    feedback_system = FeedbackLoopSystem(hive)

    # Run simulation
    feedback_system.simulate_feedback_loop(duration_days=30)

    # Get individual agent report
    LOG.info("")
    LOG.info("=== AGENT PERFORMANCE REPORT ===")
    report = feedback_system.get_agent_performance_report("acquisition_agent_1")
    LOG.info(json.dumps(report, indent=2))

    LOG.info("")
    LOG.info("=" * 80)
    LOG.info("FEEDBACK LOOP DEMONSTRATION COMPLETE")
    LOG.info("=" * 80)
