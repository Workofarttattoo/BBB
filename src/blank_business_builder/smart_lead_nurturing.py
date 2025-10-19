"""
Smart Lead Nurturing - AI-Driven Lead Qualification and Follow-up
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

Quantum-Recommended Feature #1
Priority Score: 3.21% (Highest)
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np


@dataclass
class Lead:
    """Represents a business lead."""
    id: str
    email: str
    name: str
    company: Optional[str]
    source: str
    created_at: datetime
    last_contact: Optional[datetime] = None
    engagement_score: float = 0.0
    qualification_score: float = 0.0
    stage: str = "new"  # new, qualified, nurturing, hot, converted, lost


@dataclass
class NurturingAction:
    """Recommended action for lead nurturing."""
    action_type: str  # email, call, demo, content
    priority: int  # 1-10
    timing: datetime
    content: str
    expected_impact: float
    confidence: float


class SmartLeadScorer:
    """AI-powered lead scoring using quantum-inspired algorithms."""

    def __init__(self):
        # Scoring weights (can be ML-learned)
        self.weights = {
            'engagement': 0.35,
            'fit': 0.30,
            'intent': 0.25,
            'timing': 0.10
        }

    def score_lead(self, lead: Lead, interactions: List[Dict]) -> float:
        """
        Calculate comprehensive lead score.

        Args:
            lead: The lead to score
            interactions: List of interaction events

        Returns:
            Score from 0.0 to 100.0
        """

        # 1. Engagement score (email opens, clicks, site visits)
        engagement = self._calculate_engagement_score(interactions)

        # 2. Fit score (based on company, role, industry)
        fit = self._calculate_fit_score(lead)

        # 3. Intent score (downloading resources, pricing page views)
        intent = self._calculate_intent_score(interactions)

        # 4. Timing score (recent activity, velocity)
        timing = self._calculate_timing_score(interactions)

        # Weighted combination
        total_score = (
            engagement * self.weights['engagement'] +
            fit * self.weights['fit'] +
            intent * self.weights['intent'] +
            timing * self.weights['timing']
        )

        return min(100.0, max(0.0, total_score))

    def _calculate_engagement_score(self, interactions: List[Dict]) -> float:
        """Calculate engagement based on interactions."""
        if not interactions:
            return 0.0

        email_opens = sum(1 for i in interactions if i.get('type') == 'email_open')
        email_clicks = sum(1 for i in interactions if i.get('type') == 'email_click')
        page_views = sum(1 for i in interactions if i.get('type') == 'page_view')
        demo_requests = sum(1 for i in interactions if i.get('type') == 'demo_request')

        # Weighted scoring
        score = (
            email_opens * 2 +
            email_clicks * 5 +
            page_views * 3 +
            demo_requests * 20
        )

        # Normalize to 0-100
        return min(100.0, score)

    def _calculate_fit_score(self, lead: Lead) -> float:
        """Calculate fit score based on lead attributes."""
        score = 50.0  # Base score

        # Company size (if available, would need enrichment)
        if lead.company:
            score += 20.0

        # Email domain quality
        if lead.email:
            domain = lead.email.split('@')[-1]
            # Penalize free email providers
            if domain in ['gmail.com', 'yahoo.com', 'hotmail.com']:
                score -= 10.0
            else:
                score += 15.0

        return min(100.0, max(0.0, score))

    def _calculate_intent_score(self, interactions: List[Dict]) -> float:
        """Calculate buying intent score."""
        if not interactions:
            return 0.0

        high_intent_actions = {
            'pricing_view': 15,
            'demo_request': 25,
            'contact_sales': 30,
            'trial_signup': 35,
            'whitepaper_download': 10,
            'case_study_view': 12
        }

        score = 0.0
        for interaction in interactions:
            action_type = interaction.get('type', '')
            score += high_intent_actions.get(action_type, 0)

        return min(100.0, score)

    def _calculate_timing_score(self, interactions: List[Dict]) -> float:
        """Calculate timing/velocity score."""
        if not interactions:
            return 0.0

        # Sort by timestamp
        sorted_interactions = sorted(
            [i for i in interactions if 'timestamp' in i],
            key=lambda x: x['timestamp']
        )

        if len(sorted_interactions) < 2:
            return 25.0

        # Calculate velocity (interactions per day)
        first = sorted_interactions[0]['timestamp']
        last = sorted_interactions[-1]['timestamp']

        if isinstance(first, str):
            first = datetime.fromisoformat(first)
        if isinstance(last, str):
            last = datetime.fromisoformat(last)

        time_span = (last - first).days or 1
        velocity = len(sorted_interactions) / time_span

        # Recent activity bonus
        days_since_last = (datetime.utcnow() - last).days
        recency_bonus = max(0, 50 - days_since_last * 2)

        score = min(50, velocity * 10) + recency_bonus

        return min(100.0, score)


class LeadNurturingEngine:
    """AI-powered lead nurturing with personalized follow-up."""

    def __init__(self):
        self.scorer = SmartLeadScorer()

    def generate_nurturing_plan(
        self,
        lead: Lead,
        interactions: List[Dict]
    ) -> List[NurturingAction]:
        """
        Generate personalized nurturing plan for a lead.

        Args:
            lead: The lead to nurture
            interactions: Historical interactions

        Returns:
            List of recommended nurturing actions
        """

        # Calculate lead score
        lead_score = self.scorer.score_lead(lead, interactions)

        # Determine lead stage
        stage = self._determine_stage(lead_score, interactions)

        # Generate actions based on stage
        actions = self._generate_stage_actions(lead, stage, lead_score)

        # Sort by priority
        actions.sort(key=lambda a: a.priority, reverse=True)

        return actions

    def _determine_stage(self, score: float, interactions: List[Dict]) -> str:
        """Determine lead stage based on score and behavior."""
        demo_requested = any(i.get('type') == 'demo_request' for i in interactions)
        trial_started = any(i.get('type') == 'trial_signup' for i in interactions)

        if trial_started:
            return "hot"
        elif demo_requested or score >= 80:
            return "hot"
        elif score >= 60:
            return "qualified"
        elif score >= 40:
            return "nurturing"
        else:
            return "new"

    def _generate_stage_actions(
        self,
        lead: Lead,
        stage: str,
        score: float
    ) -> List[NurturingAction]:
        """Generate actions based on lead stage."""
        actions = []
        now = datetime.utcnow()

        if stage == "new":
            # Welcome sequence
            actions.append(NurturingAction(
                action_type="email",
                priority=8,
                timing=now + timedelta(hours=1),
                content="welcome_email_template",
                expected_impact=0.15,
                confidence=0.85
            ))
            actions.append(NurturingAction(
                action_type="content",
                priority=6,
                timing=now + timedelta(days=2),
                content="getting_started_guide",
                expected_impact=0.12,
                confidence=0.80
            ))

        elif stage == "nurturing":
            # Educational content
            actions.append(NurturingAction(
                action_type="email",
                priority=7,
                timing=now + timedelta(days=1),
                content="case_study_email",
                expected_impact=0.20,
                confidence=0.82
            ))
            actions.append(NurturingAction(
                action_type="content",
                priority=7,
                timing=now + timedelta(days=3),
                content="webinar_invitation",
                expected_impact=0.25,
                confidence=0.78
            ))

        elif stage == "qualified":
            # Sales engagement
            actions.append(NurturingAction(
                action_type="call",
                priority=9,
                timing=now + timedelta(hours=12),
                content="discovery_call_script",
                expected_impact=0.40,
                confidence=0.88
            ))
            actions.append(NurturingAction(
                action_type="demo",
                priority=9,
                timing=now + timedelta(days=2),
                content="product_demo_template",
                expected_impact=0.50,
                confidence=0.90
            ))

        elif stage == "hot":
            # Close the deal
            actions.append(NurturingAction(
                action_type="call",
                priority=10,
                timing=now + timedelta(hours=4),
                content="closing_call_script",
                expected_impact=0.60,
                confidence=0.92
            ))
            actions.append(NurturingAction(
                action_type="email",
                priority=10,
                timing=now + timedelta(hours=6),
                content="trial_offer_template",
                expected_impact=0.55,
                confidence=0.90
            ))

        return actions

    def predict_conversion_probability(
        self,
        lead: Lead,
        interactions: List[Dict]
    ) -> float:
        """
        Predict probability of lead converting to customer.

        Uses logistic regression-style model.
        """
        score = self.scorer.score_lead(lead, interactions)

        # Logistic function
        z = (score - 50) / 10  # Center around 50
        probability = 1 / (1 + np.exp(-z))

        return probability


class AutomatedFollowUpSystem:
    """Automated follow-up system with AI-optimized timing."""

    def __init__(self):
        self.nurturing_engine = LeadNurturingEngine()

    def schedule_follow_ups(
        self,
        leads: List[Lead],
        all_interactions: Dict[str, List[Dict]]
    ) -> Dict[str, List[NurturingAction]]:
        """
        Schedule follow-ups for multiple leads.

        Args:
            leads: List of leads to process
            all_interactions: Dictionary mapping lead_id to interactions

        Returns:
            Dictionary mapping lead_id to scheduled actions
        """
        scheduled_actions = {}

        for lead in leads:
            interactions = all_interactions.get(lead.id, [])

            # Skip if lead was contacted very recently
            if lead.last_contact:
                hours_since = (datetime.utcnow() - lead.last_contact).total_seconds() / 3600
                if hours_since < 24:
                    continue

            # Generate nurturing plan
            actions = self.nurturing_engine.generate_nurturing_plan(lead, interactions)

            if actions:
                scheduled_actions[lead.id] = actions

        return scheduled_actions

    def get_next_action(
        self,
        lead_id: str,
        scheduled_actions: Dict[str, List[NurturingAction]]
    ) -> Optional[NurturingAction]:
        """Get next action to execute for a lead."""
        actions = scheduled_actions.get(lead_id, [])

        if not actions:
            return None

        # Return highest priority action that's due
        now = datetime.utcnow()
        due_actions = [a for a in actions if a.timing <= now]

        if due_actions:
            return max(due_actions, key=lambda a: a.priority)

        return None
