"""
Comprehensive Tests for Multi-Channel Marketing System
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from blank_business_builder.multi_channel_marketing import (
    Channel,
    CampaignStatus,
    MarketingContent,
    CampaignMetrics,
    Campaign,
    MultiChannelCampaignOrchestrator,
    MarketingAutomationEngine
)


class TestCampaignMetrics:
    """Test suite for CampaignMetrics."""

    def test_metrics_initialization(self):
        """Test metrics initialize with zeros."""
        metrics = CampaignMetrics()

        assert metrics.impressions == 0
        assert metrics.clicks == 0
        assert metrics.conversions == 0
        assert metrics.spend == 0.0
        assert metrics.revenue == 0.0

    def test_ctr_calculation(self):
        """Test click-through rate calculation."""
        metrics = CampaignMetrics(
            impressions=1000,
            clicks=25
        )

        assert metrics.ctr == 2.5  # 25/1000 * 100

    def test_ctr_zero_impressions(self):
        """Test CTR with zero impressions."""
        metrics = CampaignMetrics(clicks=5)
        assert metrics.ctr == 0.0

    def test_conversion_rate_calculation(self):
        """Test conversion rate calculation."""
        metrics = CampaignMetrics(
            clicks=100,
            conversions=5
        )

        assert metrics.conversion_rate == 5.0  # 5/100 * 100

    def test_roi_calculation(self):
        """Test ROI calculation."""
        metrics = CampaignMetrics(
            spend=1000.0,
            revenue=1500.0
        )

        assert metrics.roi == 50.0  # (1500-1000)/1000 * 100

    def test_cost_per_click(self):
        """Test cost per click calculation."""
        metrics = CampaignMetrics(
            spend=500.0,
            clicks=100
        )

        assert metrics.cost_per_click == 5.0  # 500/100

    def test_cost_per_acquisition(self):
        """Test cost per acquisition calculation."""
        metrics = CampaignMetrics(
            spend=1000.0,
            conversions=20
        )

        assert metrics.cost_per_acquisition == 50.0  # 1000/20


class TestMultiChannelCampaignOrchestrator:
    """Test suite for MultiChannelCampaignOrchestrator."""

    def test_orchestrator_initialization(self):
        """Test orchestrator initializes correctly."""
        orchestrator = MultiChannelCampaignOrchestrator()
        assert len(orchestrator.active_campaigns) == 0

    def test_create_campaign(self):
        """Test creating a campaign."""
        orchestrator = MultiChannelCampaignOrchestrator()

        campaign = orchestrator.create_campaign(
            name="Product Launch",
            goal="leads",
            channels=[Channel.EMAIL, Channel.LINKEDIN],
            budget=5000.0,
            duration_days=30
        )

        assert isinstance(campaign, Campaign)
        assert campaign.name == "Product Launch"
        assert campaign.goal == "leads"
        assert campaign.budget == 5000.0
        assert len(campaign.channels) == 2
        assert campaign.status == CampaignStatus.DRAFT

    def test_create_multiple_campaigns(self):
        """Test creating multiple campaigns."""
        orchestrator = MultiChannelCampaignOrchestrator()

        campaign1 = orchestrator.create_campaign(
            "Campaign 1", "awareness", [Channel.TWITTER], 1000.0
        )
        campaign2 = orchestrator.create_campaign(
            "Campaign 2", "sales", [Channel.GOOGLE_ADS], 2000.0
        )

        assert len(orchestrator.active_campaigns) == 2
        assert campaign1.id != campaign2.id

    def test_allocate_budget_equal_split(self):
        """Test budget allocation with no performance data."""
        orchestrator = MultiChannelCampaignOrchestrator()

        campaign = orchestrator.create_campaign(
            "Test Campaign",
            "leads",
            [Channel.EMAIL, Channel.LINKEDIN, Channel.GOOGLE_ADS],
            budget=3000.0
        )

        allocation = orchestrator.allocate_budget(campaign)

        # Should split equally
        assert len(allocation) == 3
        for channel_budget in allocation.values():
            assert channel_budget == 1000.0

    def test_allocate_budget_performance_based(self):
        """Test budget allocation based on performance."""
        orchestrator = MultiChannelCampaignOrchestrator()

        campaign = orchestrator.create_campaign(
            "Test Campaign",
            "leads",
            [Channel.EMAIL, Channel.LINKEDIN],
            budget=10000.0
        )

        # Performance data: Email performs much better
        performance_data = {
            Channel.EMAIL: CampaignMetrics(
                impressions=10000,
                clicks=500,
                conversions=50,
                spend=1000.0,
                revenue=5000.0
            ),
            Channel.LINKEDIN: CampaignMetrics(
                impressions=5000,
                clicks=100,
                conversions=5,
                spend=1000.0,
                revenue=500.0
            )
        }

        allocation = orchestrator.allocate_budget(campaign, performance_data)

        # Email should get more budget due to better ROI
        assert allocation[Channel.EMAIL] > allocation[Channel.LINKEDIN]

    def test_generate_content_email(self):
        """Test generating email content."""
        orchestrator = MultiChannelCampaignOrchestrator()

        campaign = orchestrator.create_campaign(
            "Email Campaign",
            "leads",
            [Channel.EMAIL],
            budget=1000.0
        )

        business_info = {
            "name": "Test Business",
            "value_prop": "AI-Powered Solutions"
        }

        content = orchestrator.generate_content(campaign, business_info)

        assert Channel.EMAIL in content
        assert content[Channel.EMAIL].channel == Channel.EMAIL
        assert content[Channel.EMAIL].subject is not None
        assert "Test Business" in content[Channel.EMAIL].body

    def test_generate_content_linkedin(self):
        """Test generating LinkedIn content."""
        orchestrator = MultiChannelCampaignOrchestrator()

        campaign = orchestrator.create_campaign(
            "LinkedIn Campaign",
            "awareness",
            [Channel.LINKEDIN],
            budget=2000.0
        )

        business_info = {"name": "Tech Startup"}
        content = orchestrator.generate_content(campaign, business_info)

        assert Channel.LINKEDIN in content
        assert "Tech Startup" in content[Channel.LINKEDIN].body
        assert content[Channel.LINKEDIN].call_to_action is not None

    def test_generate_content_all_channels(self):
        """Test generating content for all channels."""
        orchestrator = MultiChannelCampaignOrchestrator()

        campaign = orchestrator.create_campaign(
            "Omnichannel Campaign",
            "sales",
            [Channel.EMAIL, Channel.LINKEDIN, Channel.TWITTER, Channel.GOOGLE_ADS],
            budget=10000.0
        )

        business_info = {"name": "BigCo", "value_prop": "Enterprise Solutions"}
        content = orchestrator.generate_content(campaign, business_info)

        # Should have content for all channels
        assert len(content) == 4
        for channel in campaign.channels:
            assert channel in content
            assert content[channel].body is not None

    def test_launch_campaign(self):
        """Test launching a campaign."""
        orchestrator = MultiChannelCampaignOrchestrator()

        campaign = orchestrator.create_campaign(
            "Launch Test",
            "leads",
            [Channel.EMAIL],
            budget=1000.0
        )

        # Launch should succeed
        success = orchestrator.launch_campaign(campaign.id)
        assert success is True
        assert campaign.status == CampaignStatus.RUNNING

    def test_launch_nonexistent_campaign(self):
        """Test launching nonexistent campaign fails."""
        orchestrator = MultiChannelCampaignOrchestrator()

        success = orchestrator.launch_campaign("nonexistent_id")
        assert success is False

    def test_launch_already_running_campaign(self):
        """Test launching already running campaign."""
        orchestrator = MultiChannelCampaignOrchestrator()

        campaign = orchestrator.create_campaign(
            "Test", "leads", [Channel.EMAIL], 1000.0
        )

        # Launch first time
        orchestrator.launch_campaign(campaign.id)

        # Try to launch again
        success = orchestrator.launch_campaign(campaign.id)
        assert success is False

    def test_track_impression(self):
        """Test tracking impression event."""
        orchestrator = MultiChannelCampaignOrchestrator()

        campaign = orchestrator.create_campaign(
            "Track Test", "awareness", [Channel.EMAIL], 1000.0
        )

        orchestrator.track_performance(
            campaign.id,
            Channel.EMAIL,
            "impression"
        )

        assert campaign.metrics[Channel.EMAIL].impressions == 1

    def test_track_click(self):
        """Test tracking click event."""
        orchestrator = MultiChannelCampaignOrchestrator()

        campaign = orchestrator.create_campaign(
            "Track Test", "leads", [Channel.LINKEDIN], 2000.0
        )

        orchestrator.track_performance(
            campaign.id,
            Channel.LINKEDIN,
            "click"
        )

        assert campaign.metrics[Channel.LINKEDIN].clicks == 1

    def test_track_conversion(self):
        """Test tracking conversion event."""
        orchestrator = MultiChannelCampaignOrchestrator()

        campaign = orchestrator.create_campaign(
            "Track Test", "sales", [Channel.GOOGLE_ADS], 5000.0
        )

        orchestrator.track_performance(
            campaign.id,
            Channel.GOOGLE_ADS,
            "conversion",
            value=299.0
        )

        assert campaign.metrics[Channel.GOOGLE_ADS].conversions == 1
        assert campaign.metrics[Channel.GOOGLE_ADS].revenue == 299.0

    def test_get_campaign_analytics(self):
        """Test getting campaign analytics."""
        orchestrator = MultiChannelCampaignOrchestrator()

        campaign = orchestrator.create_campaign(
            "Analytics Test",
            "leads",
            [Channel.EMAIL, Channel.LINKEDIN],
            budget=10000.0
        )

        # Add some metrics
        campaign.metrics[Channel.EMAIL].impressions = 1000
        campaign.metrics[Channel.EMAIL].clicks = 50
        campaign.metrics[Channel.EMAIL].conversions = 5

        analytics = orchestrator.get_campaign_analytics(campaign.id)

        assert analytics["campaign_id"] == campaign.id
        assert analytics["campaign_name"] == "Analytics Test"
        assert "overall_metrics" in analytics
        assert "by_channel" in analytics
        assert analytics["overall_metrics"]["impressions"] >= 1000


class TestMarketingAutomationEngine:
    """Test suite for MarketingAutomationEngine."""

    def test_engine_initialization(self):
        """Test engine initializes correctly."""
        engine = MarketingAutomationEngine()
        assert engine.orchestrator is not None

    def test_create_growth_campaign_small_budget(self):
        """Test creating growth campaign with small budget."""
        engine = MarketingAutomationEngine()

        business_info = {"name": "Startup", "value_prop": "Innovation"}
        campaign_id = engine.create_growth_campaign(
            business_info,
            budget=300.0,
            duration_days=30
        )

        campaign = engine.orchestrator.active_campaigns[campaign_id]

        # Small budget should have limited channels
        assert len(campaign.channels) >= 1
        assert Channel.EMAIL in campaign.channels  # Always included

    def test_create_growth_campaign_medium_budget(self):
        """Test creating growth campaign with medium budget."""
        engine = MarketingAutomationEngine()

        business_info = {"name": "Growing Company"}
        campaign_id = engine.create_growth_campaign(
            business_info,
            budget=1500.0
        )

        campaign = engine.orchestrator.active_campaigns[campaign_id]

        # Medium budget should have more channels
        assert len(campaign.channels) >= 3
        assert Channel.EMAIL in campaign.channels
        assert Channel.LINKEDIN in campaign.channels

    def test_create_growth_campaign_large_budget(self):
        """Test creating growth campaign with large budget."""
        engine = MarketingAutomationEngine()

        business_info = {"name": "Enterprise", "value_prop": "Scale"}
        campaign_id = engine.create_growth_campaign(
            business_info,
            budget=5000.0
        )

        campaign = engine.orchestrator.active_campaigns[campaign_id]

        # Large budget should use many channels
        assert len(campaign.channels) >= 4

    def test_select_optimal_channels(self):
        """Test optimal channel selection logic."""
        engine = MarketingAutomationEngine()

        business_info = {"name": "Test"}

        # Low budget
        channels_low = engine._select_optimal_channels(business_info, 200.0)
        assert Channel.EMAIL in channels_low
        assert len(channels_low) == 1

        # High budget
        channels_high = engine._select_optimal_channels(business_info, 3000.0)
        assert len(channels_high) > len(channels_low)

    def test_campaign_has_content(self):
        """Test that created campaigns have content."""
        engine = MarketingAutomationEngine()

        business_info = {"name": "ContentTest", "value_prop": "Value"}
        campaign_id = engine.create_growth_campaign(business_info, 1000.0)

        campaign = engine.orchestrator.active_campaigns[campaign_id]

        # Should have content for all channels
        assert len(campaign.content) == len(campaign.channels)

    def test_campaign_budget_allocated(self):
        """Test that budget is allocated across channels."""
        engine = MarketingAutomationEngine()

        business_info = {"name": "BudgetTest"}
        campaign_id = engine.create_growth_campaign(business_info, 2000.0)

        campaign = engine.orchestrator.active_campaigns[campaign_id]

        # All channels should have metrics initialized
        assert len(campaign.metrics) == len(campaign.channels)


class TestMarketingContent:
    """Test suite for MarketingContent data model."""

    def test_content_creation(self):
        """Test creating marketing content."""
        content = MarketingContent(
            channel=Channel.EMAIL,
            subject="Test Email",
            body="This is a test email body",
            media_url=None,
            call_to_action="Click Here",
            target_audience={"segment": "leads"}
        )

        assert content.channel == Channel.EMAIL
        assert content.subject == "Test Email"
        assert content.call_to_action == "Click Here"


class TestCampaign:
    """Test suite for Campaign data model."""

    def test_campaign_creation(self):
        """Test creating a campaign."""
        now = datetime.utcnow()
        campaign = Campaign(
            id="camp_001",
            name="Test Campaign",
            goal="leads",
            channels=[Channel.EMAIL, Channel.LINKEDIN],
            content={},
            start_date=now,
            end_date=now + timedelta(days=30),
            budget=5000.0,
            status=CampaignStatus.DRAFT,
            metrics={
                Channel.EMAIL: CampaignMetrics(),
                Channel.LINKEDIN: CampaignMetrics()
            },
            created_at=now,
            updated_at=now
        )

        assert campaign.id == "camp_001"
        assert campaign.goal == "leads"
        assert len(campaign.channels) == 2
        assert campaign.budget == 5000.0


# Integration Tests
class TestMarketingIntegration:
    """Integration tests for complete marketing flow."""

    def test_complete_campaign_lifecycle(self):
        """Test complete campaign from creation to analytics."""
        engine = MarketingAutomationEngine()

        # Create campaign
        business_info = {"name": "LifecycleTest", "value_prop": "Testing"}
        campaign_id = engine.create_growth_campaign(business_info, 3000.0)

        campaign = engine.orchestrator.active_campaigns[campaign_id]

        # Launch campaign
        success = engine.orchestrator.launch_campaign(campaign_id)
        assert success is True

        # Track some events
        for channel in campaign.channels:
            engine.orchestrator.track_performance(campaign_id, channel, "impression")
            engine.orchestrator.track_performance(campaign_id, channel, "impression")
            engine.orchestrator.track_performance(campaign_id, channel, "click")
            engine.orchestrator.track_performance(campaign_id, channel, "conversion", 100.0)

        # Get analytics
        analytics = engine.orchestrator.get_campaign_analytics(campaign_id)

        assert analytics["overall_metrics"]["impressions"] > 0
        assert analytics["overall_metrics"]["clicks"] > 0
        assert analytics["overall_metrics"]["conversions"] > 0
        assert analytics["overall_metrics"]["revenue"] > 0

    def test_multi_campaign_management(self):
        """Test managing multiple campaigns simultaneously."""
        engine = MarketingAutomationEngine()

        # Create 3 campaigns
        campaigns = []
        for i in range(3):
            campaign_id = engine.create_growth_campaign(
                {"name": f"Campaign {i}"},
                budget=1000.0 * (i + 1)
            )
            campaigns.append(campaign_id)

        # Launch all
        for campaign_id in campaigns:
            engine.orchestrator.launch_campaign(campaign_id)

        # Track performance for each
        for campaign_id in campaigns:
            campaign = engine.orchestrator.active_campaigns[campaign_id]
            for channel in campaign.channels:
                engine.orchestrator.track_performance(
                    campaign_id, channel, "impression"
                )

        # Verify all have metrics
        for campaign_id in campaigns:
            analytics = engine.orchestrator.get_campaign_analytics(campaign_id)
            assert analytics["overall_metrics"]["impressions"] > 0

    def test_budget_optimization_flow(self):
        """Test budget optimization based on performance."""
        orchestrator = MultiChannelCampaignOrchestrator()

        # Create campaign
        campaign = orchestrator.create_campaign(
            "Optimization Test",
            "sales",
            [Channel.EMAIL, Channel.LINKEDIN, Channel.GOOGLE_ADS],
            budget=15000.0
        )

        # Simulate performance over time
        campaign.metrics[Channel.EMAIL] = CampaignMetrics(
            impressions=10000,
            clicks=500,
            conversions=50,
            spend=2000.0,
            revenue=10000.0
        )
        campaign.metrics[Channel.LINKEDIN] = CampaignMetrics(
            impressions=5000,
            clicks=200,
            conversions=10,
            spend=2000.0,
            revenue=2000.0
        )
        campaign.metrics[Channel.GOOGLE_ADS] = CampaignMetrics(
            impressions=20000,
            clicks=1000,
            conversions=100,
            spend=5000.0,
            revenue=20000.0
        )

        # Reallocate budget based on performance
        new_allocation = orchestrator.allocate_budget(campaign, campaign.metrics)

        # Google Ads and Email should get more budget (better ROI)
        assert new_allocation[Channel.GOOGLE_ADS] > new_allocation[Channel.LINKEDIN]
        assert new_allocation[Channel.EMAIL] > new_allocation[Channel.LINKEDIN]


class TestChannelEnum:
    """Test suite for Channel enum."""

    def test_channel_values(self):
        """Test channel enum values."""
        assert Channel.EMAIL.value == "email"
        assert Channel.LINKEDIN.value == "linkedin"
        assert Channel.TWITTER.value == "twitter"
        assert Channel.FACEBOOK.value == "facebook"
        assert Channel.GOOGLE_ADS.value == "google_ads"


class TestCampaignStatusEnum:
    """Test suite for CampaignStatus enum."""

    def test_status_values(self):
        """Test campaign status enum values."""
        assert CampaignStatus.DRAFT.value == "draft"
        assert CampaignStatus.RUNNING.value == "running"
        assert CampaignStatus.COMPLETED.value == "completed"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
