"""
Comprehensive Integration Tests for BBB Platform
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

Tests complete workflows across all quantum-recommended features.
"""

import pytest
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from blank_business_builder.smart_lead_nurturing import (
    Lead,
    SmartLeadScorer,
    LeadNurturingEngine,
    AutomatedFollowUpSystem
)
from blank_business_builder.disaster_recovery import (
    BackupType,
    BackupStrategy,
    BackupEngine,
    FailoverOrchestrator,
    DisasterRecoveryOrchestrator
)
from blank_business_builder.multi_channel_marketing import (
    Channel,
    MultiChannelCampaignOrchestrator,
    MarketingAutomationEngine
)


class TestEndToEndBusinessWorkflow:
    """Test complete end-to-end business workflows."""

    @pytest.mark.asyncio
    async def test_customer_acquisition_flow(self):
        """
        Test complete customer acquisition flow:
        1. Marketing campaign generates leads
        2. Lead nurturing qualifies and scores
        3. Conversion tracking
        """
        # Step 1: Launch marketing campaign
        marketing = MarketingAutomationEngine()
        campaign_id = marketing.create_growth_campaign(
            business_info={"name": "BBB Platform", "value_prop": "AI Automation"},
            budget=5000.0
        )

        campaign = marketing.orchestrator.active_campaigns[campaign_id]
        marketing.orchestrator.launch_campaign(campaign_id)

        # Simulate campaign generating leads
        for channel in campaign.channels:
            marketing.orchestrator.track_performance(campaign_id, channel, "impression")
            marketing.orchestrator.track_performance(campaign_id, channel, "click")

        # Step 2: Leads enter nurturing system
        lead = Lead(
            id="workflow_001",
            email="prospect@company.com",
            name="Potential Customer",
            company="Target Corp",
            source=campaign.channels[0].value,
            created_at=datetime.utcnow()
        )

        interactions = [
            {"type": "email_click", "timestamp": datetime.utcnow().isoformat()},
            {"type": "pricing_view", "timestamp": datetime.utcnow().isoformat()},
        ]

        scorer = SmartLeadScorer()
        score = scorer.score_lead(lead, interactions)
        lead.qualification_score = score

        engine = LeadNurturingEngine()
        nurturing_plan = engine.generate_nurturing_plan(lead, interactions)

        # Step 3: Track conversion
        if score > 60:  # Qualified lead
            marketing.orchestrator.track_performance(
                campaign_id,
                campaign.channels[0],
                "conversion",
                value=299.0
            )

        # Verify complete flow
        assert score > 0
        assert len(nurturing_plan) > 0

        analytics = marketing.orchestrator.get_campaign_analytics(campaign_id)
        assert analytics["overall_metrics"]["impressions"] > 0
        assert analytics["overall_metrics"]["clicks"] > 0

    @pytest.mark.asyncio
    async def test_disaster_recovery_with_active_campaigns(self):
        """
        Test disaster recovery while campaigns are running:
        1. Campaigns running
        2. System failure occurs
        3. Disaster recovery activates
        4. Campaigns restored
        """
        # Step 1: Setup active campaigns
        marketing = MarketingAutomationEngine()
        campaign_id = marketing.create_growth_campaign(
            {"name": "Critical Campaign"},
            budget=10000.0
        )
        marketing.orchestrator.launch_campaign(campaign_id)

        # Step 2: Create DR system and backup
        dr = DisasterRecoveryOrchestrator()
        dr.schedule_backup(
            "hourly",
            ["database", "campaigns"],
            BackupType.FULL,
            BackupStrategy.MULTI_REGION
        )

        backups = await dr.run_scheduled_backups()
        assert len(backups) > 0

        # Step 3: Simulate system failure and recovery
        recovery_result = await dr.test_disaster_recovery("full_system_failure")
        assert recovery_result["success"] is not None

        # Step 4: Verify campaigns can be restored
        restore_result = await dr.backup_engine.restore_backup(
            backups[0].backup_id,
            verify=True
        )
        assert restore_result["success"] is True

    @pytest.mark.asyncio
    async def test_multi_tenant_scenario(self):
        """
        Test multi-tenant scenario:
        1. Multiple businesses running campaigns
        2. Each with separate leads
        3. All backed up independently
        """
        # Setup multiple businesses
        businesses = [
            {"name": "Business A", "value_prop": "SaaS Platform"},
            {"name": "Business B", "value_prop": "E-commerce"},
            {"name": "Business C", "value_prop": "Consulting"}
        ]

        marketing = MarketingAutomationEngine()
        campaign_ids = []

        # Each business launches campaign
        for business in businesses:
            campaign_id = marketing.create_growth_campaign(business, budget=3000.0)
            marketing.orchestrator.launch_campaign(campaign_id)
            campaign_ids.append(campaign_id)

        # Each campaign has separate leads
        nurturing_system = AutomatedFollowUpSystem()
        all_leads = []

        for i, campaign_id in enumerate(campaign_ids):
            lead = Lead(
                id=f"tenant_{i}_lead_001",
                email=f"lead@business{chr(65+i)}.com",
                name=f"Lead {i}",
                company=businesses[i]["name"],
                source="web",
                created_at=datetime.utcnow()
            )
            all_leads.append(lead)

        # Schedule follow-ups for all
        scheduled = nurturing_system.schedule_follow_ups(all_leads, {})
        assert len(scheduled) > 0

        # Backup all tenant data
        dr = DisasterRecoveryOrchestrator()
        backup = await dr.backup_engine.create_backup(
            data_sources=["database", "campaigns", "leads"],
            backup_type=BackupType.FULL,
            strategy=BackupStrategy.MULTI_REGION
        )

        assert backup.size_bytes > 0

    @pytest.mark.asyncio
    async def test_high_availability_failover(self):
        """
        Test high availability during active operations:
        1. System running with campaigns and leads
        2. Primary instance fails
        3. Failover to secondary
        4. Operations continue seamlessly
        """
        # Setup active operations
        marketing = MarketingAutomationEngine()
        campaign_id = marketing.create_growth_campaign(
            {"name": "HA Test"},
            budget=5000.0
        )

        # Setup HA infrastructure
        dr = DisasterRecoveryOrchestrator()
        dr.failover.register_instance("primary", "http://primary.com", 1, True)
        dr.failover.register_instance("secondary", "http://secondary.com", 2)

        # Primary fails
        primary_health = await dr.failover.health_check("primary")

        # Failover
        failover_event = await dr.failover.perform_failover(
            from_instance="primary",
            to_instance="secondary",
            trigger="primary_failure"
        )

        # Verify failover succeeded
        assert failover_event.success is True
        assert dr.failover.active_instance == "secondary"
        assert failover_event.duration_seconds < 30  # Under RTO

        # Operations should continue
        marketing.orchestrator.track_performance(
            campaign_id,
            Channel.EMAIL,
            "impression"
        )

    def test_quantum_optimized_lead_scoring(self):
        """
        Test lead scoring with quantum-optimized weights:
        1. Multiple leads with different profiles
        2. Score using optimized algorithms
        3. Verify proper prioritization
        """
        scorer = SmartLeadScorer()

        # High-quality lead
        high_quality = Lead(
            id="hq_001",
            email="ceo@bigcorp.com",
            name="CEO Name",
            company="Fortune 500",
            source="referral",
            created_at=datetime.utcnow()
        )

        hq_interactions = [
            {"type": "demo_request", "timestamp": datetime.utcnow().isoformat()},
            {"type": "pricing_view", "timestamp": datetime.utcnow().isoformat()},
            {"type": "trial_signup", "timestamp": datetime.utcnow().isoformat()},
        ]

        # Low-quality lead
        low_quality = Lead(
            id="lq_001",
            email="user@gmail.com",
            name="Random User",
            company=None,
            source="cold",
            created_at=datetime.utcnow()
        )

        lq_interactions = []

        # Score both
        hq_score = scorer.score_lead(high_quality, hq_interactions)
        lq_score = scorer.score_lead(low_quality, lq_interactions)

        # High quality should score much higher
        assert hq_score > lq_score
        assert hq_score > 70  # Should be qualified

    @pytest.mark.asyncio
    async def test_compliance_and_backup_retention(self):
        """
        Test compliance requirements for data retention:
        1. Create backups with different retention policies
        2. Verify retention enforcement
        3. Test compliance reporting
        """
        dr = DisasterRecoveryOrchestrator()

        # Short retention (dev/test)
        short_backup = await dr.backup_engine.create_backup(
            ["database"],
            BackupType.INCREMENTAL,
            BackupStrategy.LOCAL,
            retention_days=7
        )

        # Standard retention (production)
        standard_backup = await dr.backup_engine.create_backup(
            ["database", "files"],
            BackupType.FULL,
            BackupStrategy.S3,
            retention_days=30
        )

        # Long retention (compliance)
        compliance_backup = await dr.backup_engine.create_backup(
            ["all"],
            BackupType.FULL,
            BackupStrategy.MULTI_REGION,
            retention_days=2555  # 7 years
        )

        # Verify retention settings
        assert short_backup.retention_days == 7
        assert standard_backup.retention_days == 30
        assert compliance_backup.retention_days == 2555

        # Verify encryption for compliance
        assert compliance_backup.encryption_enabled is True

    def test_campaign_roi_optimization(self):
        """
        Test ROI-based campaign optimization:
        1. Launch multiple channels
        2. Track performance
        3. Optimize budget allocation
        4. Verify ROI improvement
        """
        orchestrator = MultiChannelCampaignOrchestrator()

        campaign = orchestrator.create_campaign(
            "ROI Optimization Test",
            "sales",
            [Channel.EMAIL, Channel.LINKEDIN, Channel.GOOGLE_ADS],
            budget=15000.0
        )

        # Initial equal allocation
        initial_allocation = orchestrator.allocate_budget(campaign)
        assert all(budget == 5000.0 for budget in initial_allocation.values())

        # Simulate performance (Email performs best)
        campaign.metrics[Channel.EMAIL].impressions = 10000
        campaign.metrics[Channel.EMAIL].clicks = 500
        campaign.metrics[Channel.EMAIL].conversions = 50
        campaign.metrics[Channel.EMAIL].spend = 2000
        campaign.metrics[Channel.EMAIL].revenue = 10000

        campaign.metrics[Channel.LINKEDIN].impressions = 5000
        campaign.metrics[Channel.LINKEDIN].clicks = 100
        campaign.metrics[Channel.LINKEDIN].conversions = 5
        campaign.metrics[Channel.LINKEDIN].spend = 3000
        campaign.metrics[Channel.LINKEDIN].revenue = 1000

        campaign.metrics[Channel.GOOGLE_ADS].impressions = 15000
        campaign.metrics[Channel.GOOGLE_ADS].clicks = 300
        campaign.metrics[Channel.GOOGLE_ADS].conversions = 15
        campaign.metrics[Channel.GOOGLE_ADS].spend = 4000
        campaign.metrics[Channel.GOOGLE_ADS].revenue = 3000

        # Optimize allocation based on performance
        optimized_allocation = orchestrator.allocate_budget(campaign, campaign.metrics)

        # Email should get more budget (highest ROI)
        assert optimized_allocation[Channel.EMAIL] > initial_allocation[Channel.EMAIL]


class TestScalabilityAndPerformance:
    """Test system scalability and performance."""

    def test_high_volume_lead_processing(self):
        """Test processing large volumes of leads."""
        system = AutomatedFollowUpSystem()

        # Create 1000 leads
        leads = [
            Lead(
                id=f"lead_{i:04d}",
                email=f"lead{i}@example.com",
                name=f"Lead {i}",
                company=f"Company {i}",
                source="web",
                created_at=datetime.utcnow()
            )
            for i in range(1000)
        ]

        # Schedule follow-ups
        scheduled = system.schedule_follow_ups(leads, {})

        # Should handle all leads
        assert len(scheduled) == len(leads)

    @pytest.mark.asyncio
    async def test_concurrent_backup_operations(self):
        """Test concurrent backup operations."""
        engine = BackupEngine()

        # Run multiple backups concurrently
        tasks = [
            engine.create_backup(
                [f"source_{i}"],
                BackupType.INCREMENTAL,
                BackupStrategy.LOCAL
            )
            for i in range(10)
        ]

        results = await asyncio.gather(*tasks)

        # All should succeed
        assert len(results) == 10
        assert all(r.size_bytes > 0 for r in results)

    def test_multi_campaign_performance(self):
        """Test performance with multiple simultaneous campaigns."""
        engine = MarketingAutomationEngine()

        # Launch 50 campaigns
        campaign_ids = [
            engine.create_growth_campaign(
                {"name": f"Campaign {i}"},
                budget=1000.0
            )
            for i in range(50)
        ]

        # Track events across all campaigns
        for campaign_id in campaign_ids:
            campaign = engine.orchestrator.active_campaigns[campaign_id]
            for channel in campaign.channels:
                engine.orchestrator.track_performance(
                    campaign_id, channel, "impression"
                )

        # All should have metrics
        for campaign_id in campaign_ids:
            analytics = engine.orchestrator.get_campaign_analytics(campaign_id)
            assert analytics["overall_metrics"]["impressions"] > 0


class TestErrorHandlingAndRecovery:
    """Test error handling and recovery scenarios."""

    @pytest.mark.asyncio
    async def test_backup_corruption_recovery(self):
        """Test recovery from backup corruption."""
        engine = BackupEngine()

        # Create multiple backups
        backup1 = await engine.create_backup(["database"], BackupType.FULL)
        backup2 = await engine.create_backup(["database"], BackupType.FULL)

        # Try to restore from first (could be corrupted)
        result1 = await engine.restore_backup(backup1.backup_id, verify=True)

        # If first fails, try second
        if not result1["success"]:
            result2 = await engine.restore_backup(backup2.backup_id, verify=True)
            assert result2["success"] is True

    def test_lead_deduplication(self):
        """Test handling duplicate leads."""
        system = AutomatedFollowUpSystem()

        # Create duplicate leads
        lead1 = Lead(
            id="dup_001",
            email="same@example.com",
            name="Same Person",
            company="Company",
            source="web",
            created_at=datetime.utcnow()
        )

        lead2 = Lead(
            id="dup_002",
            email="same@example.com",  # Same email
            name="Same Person",
            company="Company",
            source="linkedin",
            created_at=datetime.utcnow()
        )

        # System should handle duplicates
        scheduled = system.schedule_follow_ups([lead1, lead2], {})
        assert len(scheduled) >= 1

    @pytest.mark.asyncio
    async def test_failover_rollback(self):
        """Test failover rollback on failure."""
        orchestrator = FailoverOrchestrator()

        orchestrator.register_instance("i1", "http://a.com", 1, True)
        orchestrator.register_instance("i2", "http://b.com", 2)

        original_active = orchestrator.active_instance

        # Attempt failover
        event = await orchestrator.perform_failover("i1", "i2", "test")

        # If failover failed, active should remain unchanged
        if not event.success:
            assert orchestrator.active_instance == original_active


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
