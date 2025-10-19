"""
Comprehensive Tests for Smart Lead Nurturing System
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from blank_business_builder.smart_lead_nurturing import (
    Lead,
    NurturingAction,
    SmartLeadScorer,
    LeadNurturingEngine,
    AutomatedFollowUpSystem
)


class TestSmartLeadScorer:
    """Test suite for SmartLeadScorer."""

    def test_scorer_initialization(self):
        """Test scorer initializes with correct weights."""
        scorer = SmartLeadScorer()

        assert scorer.weights['engagement'] == 0.35
        assert scorer.weights['fit'] == 0.30
        assert scorer.weights['intent'] == 0.25
        assert scorer.weights['timing'] == 0.10

        # Weights should sum to 1.0
        assert abs(sum(scorer.weights.values()) - 1.0) < 0.01

    def test_score_new_lead_zero_interactions(self):
        """Test scoring a new lead with no interactions."""
        scorer = SmartLeadScorer()
        lead = Lead(
            id="lead_001",
            email="john@example.com",
            name="John Doe",
            company="Example Corp",
            source="website",
            created_at=datetime.utcnow()
        )

        score = scorer.score_lead(lead, [])

        # Should get base score from fit component only
        assert 0 <= score <= 100
        assert score > 0  # Should have some base score

    def test_score_with_email_interactions(self):
        """Test scoring with email engagement."""
        scorer = SmartLeadScorer()
        lead = Lead(
            id="lead_002",
            email="jane@company.com",
            name="Jane Smith",
            company="Tech Inc",
            source="linkedin",
            created_at=datetime.utcnow()
        )

        interactions = [
            {"type": "email_open", "timestamp": datetime.utcnow().isoformat()},
            {"type": "email_open", "timestamp": datetime.utcnow().isoformat()},
            {"type": "email_click", "timestamp": datetime.utcnow().isoformat()},
        ]

        score = scorer.score_lead(lead, interactions)

        assert score > 0
        assert score <= 100

    def test_score_with_high_intent_actions(self):
        """Test scoring with high-intent actions."""
        scorer = SmartLeadScorer()
        lead = Lead(
            id="lead_003",
            email="ceo@bigcorp.com",
            name="CEO Name",
            company="Big Corp",
            source="referral",
            created_at=datetime.utcnow()
        )

        interactions = [
            {"type": "pricing_view", "timestamp": datetime.utcnow().isoformat()},
            {"type": "demo_request", "timestamp": datetime.utcnow().isoformat()},
            {"type": "trial_signup", "timestamp": datetime.utcnow().isoformat()},
        ]

        score = scorer.score_lead(lead, interactions)

        # High-intent actions should result in high score
        assert score > 50

    def test_fit_score_corporate_email(self):
        """Test fit scoring favors corporate emails."""
        scorer = SmartLeadScorer()

        corporate_lead = Lead(
            id="lead_004",
            email="user@company.com",
            name="User",
            company="Company",
            source="web",
            created_at=datetime.utcnow()
        )

        gmail_lead = Lead(
            id="lead_005",
            email="user@gmail.com",
            name="User",
            company=None,
            source="web",
            created_at=datetime.utcnow()
        )

        corporate_score = scorer._calculate_fit_score(corporate_lead)
        gmail_score = scorer._calculate_fit_score(gmail_lead)

        # Corporate email should score higher
        assert corporate_score > gmail_score

    def test_timing_score_recent_activity(self):
        """Test timing score favors recent activity."""
        scorer = SmartLeadScorer()

        # Recent interactions
        recent_interactions = [
            {"type": "page_view", "timestamp": (datetime.utcnow() - timedelta(hours=1)).isoformat()},
            {"type": "page_view", "timestamp": datetime.utcnow().isoformat()},
        ]

        # Old interactions
        old_interactions = [
            {"type": "page_view", "timestamp": (datetime.utcnow() - timedelta(days=30)).isoformat()},
            {"type": "page_view", "timestamp": (datetime.utcnow() - timedelta(days=25)).isoformat()},
        ]

        recent_score = scorer._calculate_timing_score(recent_interactions)
        old_score = scorer._calculate_timing_score(old_interactions)

        # Recent activity should score higher
        assert recent_score > old_score


class TestLeadNurturingEngine:
    """Test suite for LeadNurturingEngine."""

    def test_engine_initialization(self):
        """Test engine initializes correctly."""
        engine = LeadNurturingEngine()
        assert engine.scorer is not None

    def test_generate_plan_new_lead(self):
        """Test nurturing plan for new lead."""
        engine = LeadNurturingEngine()
        lead = Lead(
            id="lead_006",
            email="new@example.com",
            name="New Lead",
            company=None,
            source="web",
            created_at=datetime.utcnow()
        )

        actions = engine.generate_nurturing_plan(lead, [])

        assert len(actions) > 0
        assert all(isinstance(action, NurturingAction) for action in actions)

        # Should have welcome sequence actions
        action_types = [a.action_type for a in actions]
        assert "email" in action_types

    def test_generate_plan_hot_lead(self):
        """Test nurturing plan for hot lead."""
        engine = LeadNurturingEngine()
        lead = Lead(
            id="lead_007",
            email="hot@example.com",
            name="Hot Lead",
            company="Big Company",
            source="referral",
            created_at=datetime.utcnow()
        )

        interactions = [
            {"type": "trial_signup", "timestamp": datetime.utcnow().isoformat()},
            {"type": "demo_request", "timestamp": datetime.utcnow().isoformat()},
            {"type": "pricing_view", "timestamp": datetime.utcnow().isoformat()},
        ]

        actions = engine.generate_nurturing_plan(lead, interactions)

        assert len(actions) > 0

        # Hot leads should have high-priority actions
        priorities = [a.priority for a in actions]
        assert max(priorities) >= 9

    def test_stage_determination(self):
        """Test correct stage determination."""
        engine = LeadNurturingEngine()

        # New lead
        assert engine._determine_stage(30, []) == "new"

        # Nurturing stage
        assert engine._determine_stage(50, []) == "nurturing"

        # Qualified stage
        assert engine._determine_stage(70, []) == "qualified"

        # Hot stage
        assert engine._determine_stage(85, []) == "hot"

        # Trial signup makes it hot regardless of score
        trial_interactions = [
            {"type": "trial_signup", "timestamp": datetime.utcnow().isoformat()}
        ]
        assert engine._determine_stage(40, trial_interactions) == "hot"

    def test_conversion_probability_prediction(self):
        """Test conversion probability calculation."""
        engine = LeadNurturingEngine()
        lead = Lead(
            id="lead_008",
            email="test@example.com",
            name="Test",
            company="Test Co",
            source="web",
            created_at=datetime.utcnow()
        )

        # Low score lead
        low_interactions = []
        low_prob = engine.predict_conversion_probability(lead, low_interactions)

        # High score lead
        high_interactions = [
            {"type": "demo_request", "timestamp": datetime.utcnow().isoformat()},
            {"type": "trial_signup", "timestamp": datetime.utcnow().isoformat()},
        ]
        high_prob = engine.predict_conversion_probability(lead, high_interactions)

        # Both should be valid probabilities
        assert 0 <= low_prob <= 1
        assert 0 <= high_prob <= 1

        # High score should have higher probability
        assert high_prob > low_prob


class TestAutomatedFollowUpSystem:
    """Test suite for AutomatedFollowUpSystem."""

    def test_system_initialization(self):
        """Test system initializes correctly."""
        system = AutomatedFollowUpSystem()
        assert system.nurturing_engine is not None

    def test_schedule_follow_ups_single_lead(self):
        """Test scheduling follow-ups for a single lead."""
        system = AutomatedFollowUpSystem()

        lead = Lead(
            id="lead_009",
            email="follow@example.com",
            name="Follow Test",
            company="Test",
            source="web",
            created_at=datetime.utcnow(),
            last_contact=None
        )

        interactions = {
            "lead_009": [
                {"type": "email_open", "timestamp": datetime.utcnow().isoformat()}
            ]
        }

        scheduled = system.schedule_follow_ups([lead], interactions)

        assert "lead_009" in scheduled
        assert len(scheduled["lead_009"]) > 0

    def test_skip_recently_contacted_leads(self):
        """Test that recently contacted leads are skipped."""
        system = AutomatedFollowUpSystem()

        # Lead contacted 1 hour ago
        recent_lead = Lead(
            id="lead_010",
            email="recent@example.com",
            name="Recent",
            company="Test",
            source="web",
            created_at=datetime.utcnow(),
            last_contact=datetime.utcnow() - timedelta(hours=1)
        )

        # Lead contacted 3 days ago
        old_lead = Lead(
            id="lead_011",
            email="old@example.com",
            name="Old",
            company="Test",
            source="web",
            created_at=datetime.utcnow(),
            last_contact=datetime.utcnow() - timedelta(days=3)
        )

        interactions = {}
        scheduled = system.schedule_follow_ups([recent_lead, old_lead], interactions)

        # Recent lead should be skipped
        assert "lead_010" not in scheduled

        # Old lead should be scheduled
        assert "lead_011" in scheduled

    def test_get_next_action_priority(self):
        """Test getting next action based on priority and timing."""
        system = AutomatedFollowUpSystem()

        now = datetime.utcnow()

        scheduled_actions = {
            "lead_012": [
                NurturingAction(
                    action_type="email",
                    priority=5,
                    timing=now - timedelta(hours=1),  # Due
                    content="low_priority",
                    expected_impact=0.1,
                    confidence=0.8
                ),
                NurturingAction(
                    action_type="call",
                    priority=9,
                    timing=now - timedelta(hours=2),  # Due
                    content="high_priority",
                    expected_impact=0.5,
                    confidence=0.9
                ),
                NurturingAction(
                    action_type="demo",
                    priority=10,
                    timing=now + timedelta(hours=1),  # Not due yet
                    content="future",
                    expected_impact=0.6,
                    confidence=0.95
                ),
            ]
        }

        next_action = system.get_next_action("lead_012", scheduled_actions)

        # Should return highest priority action that is due
        assert next_action is not None
        assert next_action.priority == 9
        assert next_action.action_type == "call"

    def test_multiple_leads_scheduling(self):
        """Test scheduling for multiple leads."""
        system = AutomatedFollowUpSystem()

        leads = [
            Lead(
                id=f"lead_{i:03d}",
                email=f"lead{i}@example.com",
                name=f"Lead {i}",
                company="Test",
                source="web",
                created_at=datetime.utcnow(),
                last_contact=None
            )
            for i in range(100, 110)
        ]

        interactions = {}
        scheduled = system.schedule_follow_ups(leads, interactions)

        # Should schedule for all leads
        assert len(scheduled) == len(leads)


class TestLeadModel:
    """Test suite for Lead data model."""

    def test_lead_creation(self):
        """Test creating a lead."""
        lead = Lead(
            id="lead_999",
            email="test@example.com",
            name="Test Lead",
            company="Test Company",
            source="website",
            created_at=datetime.utcnow()
        )

        assert lead.id == "lead_999"
        assert lead.email == "test@example.com"
        assert lead.stage == "new"
        assert lead.engagement_score == 0.0
        assert lead.qualification_score == 0.0

    def test_lead_optional_fields(self):
        """Test lead with optional fields."""
        lead = Lead(
            id="lead_998",
            email="minimal@example.com",
            name="Minimal",
            company=None,
            source="unknown",
            created_at=datetime.utcnow(),
            last_contact=None
        )

        assert lead.company is None
        assert lead.last_contact is None


class TestNurturingActionModel:
    """Test suite for NurturingAction data model."""

    def test_action_creation(self):
        """Test creating a nurturing action."""
        action = NurturingAction(
            action_type="email",
            priority=8,
            timing=datetime.utcnow(),
            content="welcome_email",
            expected_impact=0.25,
            confidence=0.85
        )

        assert action.action_type == "email"
        assert action.priority == 8
        assert 0 <= action.expected_impact <= 1
        assert 0 <= action.confidence <= 1


# Integration Tests
class TestLeadNurturingIntegration:
    """Integration tests for complete lead nurturing flow."""

    def test_complete_nurturing_flow(self):
        """Test complete flow from lead creation to action scheduling."""
        # Create lead
        lead = Lead(
            id="integration_001",
            email="flow@example.com",
            name="Integration Test",
            company="Flow Co",
            source="web",
            created_at=datetime.utcnow()
        )

        # Simulate interactions
        interactions = [
            {"type": "email_open", "timestamp": datetime.utcnow().isoformat()},
            {"type": "page_view", "timestamp": datetime.utcnow().isoformat()},
            {"type": "pricing_view", "timestamp": datetime.utcnow().isoformat()},
        ]

        # Score lead
        scorer = SmartLeadScorer()
        score = scorer.score_lead(lead, interactions)
        lead.qualification_score = score

        # Generate nurturing plan
        engine = LeadNurturingEngine()
        actions = engine.generate_nurturing_plan(lead, interactions)

        # Schedule follow-ups
        system = AutomatedFollowUpSystem()
        scheduled = system.schedule_follow_ups(
            [lead],
            {"integration_001": interactions}
        )

        # Verify complete flow
        assert score > 0
        assert len(actions) > 0
        assert "integration_001" in scheduled
        assert len(scheduled["integration_001"]) > 0

    def test_lead_progression_through_stages(self):
        """Test lead progressing through nurturing stages."""
        lead = Lead(
            id="progression_001",
            email="progress@example.com",
            name="Progression Test",
            company="Test",
            source="web",
            created_at=datetime.utcnow()
        )

        engine = LeadNurturingEngine()

        # Stage 1: New lead
        new_interactions = []
        stage1 = engine._determine_stage(
            engine.scorer.score_lead(lead, new_interactions),
            new_interactions
        )
        assert stage1 == "new"

        # Stage 2: Nurturing (some engagement)
        nurturing_interactions = [
            {"type": "email_open", "timestamp": datetime.utcnow().isoformat()},
            {"type": "page_view", "timestamp": datetime.utcnow().isoformat()},
        ]
        stage2 = engine._determine_stage(
            engine.scorer.score_lead(lead, nurturing_interactions),
            nurturing_interactions
        )

        # Stage 3: High intent (demo request)
        hot_interactions = nurturing_interactions + [
            {"type": "demo_request", "timestamp": datetime.utcnow().isoformat()},
        ]
        stage3 = engine._determine_stage(
            engine.scorer.score_lead(lead, hot_interactions),
            hot_interactions
        )
        assert stage3 == "hot"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
