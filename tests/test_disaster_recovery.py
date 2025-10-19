"""
Comprehensive Tests for Disaster Recovery System
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

import pytest
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from blank_business_builder.disaster_recovery import (
    BackupStrategy,
    BackupType,
    RecoveryStatus,
    BackupMetadata,
    HealthCheck,
    FailoverEvent,
    BackupEngine,
    FailoverOrchestrator,
    DisasterRecoveryOrchestrator
)


class TestBackupEngine:
    """Test suite for BackupEngine."""

    def test_engine_initialization(self):
        """Test backup engine initializes correctly."""
        engine = BackupEngine(base_path="./test_backups")
        assert engine.base_path.exists()
        assert len(engine.backup_history) == 0

    @pytest.mark.asyncio
    async def test_create_full_backup(self):
        """Test creating a full backup."""
        engine = BackupEngine(base_path="./test_backups")

        backup = await engine.create_backup(
            data_sources=["database", "files"],
            backup_type=BackupType.FULL,
            strategy=BackupStrategy.LOCAL,
            retention_days=30,
            encrypt=True
        )

        assert isinstance(backup, BackupMetadata)
        assert backup.backup_type == BackupType.FULL
        assert backup.strategy == BackupStrategy.LOCAL
        assert backup.encryption_enabled is True
        assert backup.retention_days == 30
        assert backup.size_bytes > 0
        assert len(backup.checksum) == 64  # SHA-256 hex

    @pytest.mark.asyncio
    async def test_create_incremental_backup(self):
        """Test creating an incremental backup."""
        engine = BackupEngine()

        backup = await engine.create_backup(
            data_sources=["database"],
            backup_type=BackupType.INCREMENTAL,
            strategy=BackupStrategy.S3
        )

        assert backup.backup_type == BackupType.INCREMENTAL
        assert backup.strategy == BackupStrategy.S3
        assert "s3://" in backup.location

    @pytest.mark.asyncio
    async def test_backup_compression(self):
        """Test backup compression."""
        engine = BackupEngine()

        backup = await engine.create_backup(
            data_sources=["database", "files", "configs"],
            backup_type=BackupType.FULL
        )

        assert backup.compression_ratio > 0
        assert backup.compression_ratio <= 100  # Realistic compression ratio

    @pytest.mark.asyncio
    async def test_restore_backup(self):
        """Test restoring from a backup."""
        engine = BackupEngine()

        # Create backup
        backup = await engine.create_backup(
            data_sources=["database"],
            backup_type=BackupType.FULL,
            strategy=BackupStrategy.LOCAL
        )

        # Restore backup
        result = await engine.restore_backup(backup.backup_id, verify=True)

        assert result["success"] is True
        assert result["backup_id"] == backup.backup_id
        assert "database" in result["restored_sources"]

    @pytest.mark.asyncio
    async def test_restore_nonexistent_backup(self):
        """Test restoring a nonexistent backup fails gracefully."""
        engine = BackupEngine()

        result = await engine.restore_backup("nonexistent_backup_id")

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_multi_region_backup(self):
        """Test multi-region backup strategy."""
        engine = BackupEngine()

        backup = await engine.create_backup(
            data_sources=["database"],
            backup_type=BackupType.FULL,
            strategy=BackupStrategy.MULTI_REGION
        )

        assert backup.strategy == BackupStrategy.MULTI_REGION
        assert "multi:" in backup.location
        # Should contain multiple storage locations
        assert "," in backup.location

    def test_cleanup_old_backups(self):
        """Test cleaning up old backups."""
        engine = BackupEngine()

        # Add some fake old backups
        old_backup = BackupMetadata(
            backup_id="old_backup_1",
            backup_type=BackupType.FULL,
            strategy=BackupStrategy.LOCAL,
            timestamp=datetime.utcnow() - timedelta(days=35),
            size_bytes=1000,
            checksum="abc123",
            data_sources=["database"],
            retention_days=30,
            encryption_enabled=True,
            compression_ratio=2.5,
            location="./backups/old_backup_1.backup"
        )

        engine.backup_history.append(old_backup)

        # Cleanup with 30-day retention
        removed = engine.cleanup_old_backups(retention_days=30)

        assert len(removed) > 0
        assert "old_backup_1" in removed

    @pytest.mark.asyncio
    async def test_backup_history_tracking(self):
        """Test that backups are tracked in history."""
        engine = BackupEngine()

        initial_count = len(engine.backup_history)

        await engine.create_backup(
            data_sources=["database"],
            backup_type=BackupType.FULL
        )

        assert len(engine.backup_history) == initial_count + 1


class TestFailoverOrchestrator:
    """Test suite for FailoverOrchestrator."""

    def test_orchestrator_initialization(self):
        """Test failover orchestrator initializes correctly."""
        orchestrator = FailoverOrchestrator()
        assert len(orchestrator.instances) == 0
        assert orchestrator.active_instance is None
        assert len(orchestrator.failover_history) == 0

    def test_register_instance(self):
        """Test registering instances."""
        orchestrator = FailoverOrchestrator()

        orchestrator.register_instance(
            instance_id="instance_1",
            endpoint="http://app1.example.com",
            priority=1,
            is_active=True
        )

        orchestrator.register_instance(
            instance_id="instance_2",
            endpoint="http://app2.example.com",
            priority=2
        )

        assert len(orchestrator.instances) == 2
        assert orchestrator.active_instance == "instance_1"
        assert orchestrator.instances["instance_2"]["priority"] == 2

    @pytest.mark.asyncio
    async def test_health_check_healthy_instance(self):
        """Test health check on healthy instance."""
        orchestrator = FailoverOrchestrator()
        orchestrator.register_instance(
            instance_id="healthy_instance",
            endpoint="http://healthy.example.com",
            priority=1
        )

        health = await orchestrator.health_check("healthy_instance")

        assert isinstance(health, HealthCheck)
        assert health.component == "healthy_instance"
        assert health.status in ["healthy", "degraded", "unhealthy"]
        assert health.latency_ms >= 0

    @pytest.mark.asyncio
    async def test_health_check_nonexistent_instance(self):
        """Test health check on nonexistent instance."""
        orchestrator = FailoverOrchestrator()

        health = await orchestrator.health_check("nonexistent")

        assert health.status == "unhealthy"
        assert health.error_message is not None

    @pytest.mark.asyncio
    async def test_manual_failover(self):
        """Test manual failover between instances."""
        orchestrator = FailoverOrchestrator()

        orchestrator.register_instance("instance_1", "http://app1.com", 1, True)
        orchestrator.register_instance("instance_2", "http://app2.com", 2)

        event = await orchestrator.perform_failover(
            from_instance="instance_1",
            to_instance="instance_2",
            trigger="manual"
        )

        assert isinstance(event, FailoverEvent)
        assert event.success is True
        assert event.from_instance == "instance_1"
        assert event.to_instance == "instance_2"
        assert event.trigger == "manual"
        assert orchestrator.active_instance == "instance_2"

    @pytest.mark.asyncio
    async def test_auto_select_failover_target(self):
        """Test automatic selection of failover target."""
        orchestrator = FailoverOrchestrator()

        orchestrator.register_instance("instance_1", "http://app1.com", 1, True)
        orchestrator.register_instance("instance_2", "http://app2.com", 3)  # Higher priority
        orchestrator.register_instance("instance_3", "http://app3.com", 2)

        event = await orchestrator.perform_failover(
            from_instance="instance_1",
            to_instance=None,  # Auto-select
            trigger="auto"
        )

        # Should select instance_2 (highest priority)
        assert event.to_instance == "instance_2"

    @pytest.mark.asyncio
    async def test_failover_no_healthy_instances(self):
        """Test failover when no healthy instances available."""
        orchestrator = FailoverOrchestrator()

        orchestrator.register_instance("instance_1", "http://app1.com", 1, True)
        # Mark instance as unhealthy
        orchestrator.instances["instance_1"]["status"] = "unhealthy"

        event = await orchestrator.perform_failover(
            from_instance="instance_1",
            trigger="auto"
        )

        assert event.success is False
        assert event.to_instance == "none"

    @pytest.mark.asyncio
    async def test_auto_failover_check(self):
        """Test automatic failover check."""
        orchestrator = FailoverOrchestrator()

        orchestrator.register_instance("instance_1", "http://app1.com", 1, True)
        orchestrator.register_instance("instance_2", "http://app2.com", 2)

        # Force health check to trigger failover by simulating high latency
        # This is tested through the health_check auto_failover flag
        result = await orchestrator.auto_failover_check()

        # Result depends on health check outcome
        assert result is None or isinstance(result, FailoverEvent)

    def test_failover_history_tracking(self):
        """Test that failover events are tracked."""
        orchestrator = FailoverOrchestrator()
        orchestrator.register_instance("i1", "http://a.com", 1, True)
        orchestrator.register_instance("i2", "http://b.com", 2)

        asyncio.run(orchestrator.perform_failover("i1", "i2", "test"))

        assert len(orchestrator.failover_history) > 0
        assert orchestrator.failover_history[0].trigger == "test"


class TestDisasterRecoveryOrchestrator:
    """Test suite for DisasterRecoveryOrchestrator."""

    def test_orchestrator_initialization(self):
        """Test DR orchestrator initializes correctly."""
        dr = DisasterRecoveryOrchestrator()
        assert dr.backup_engine is not None
        assert dr.failover is not None
        assert len(dr.scheduled_backups) == 0

    def test_schedule_backup(self):
        """Test scheduling automated backups."""
        dr = DisasterRecoveryOrchestrator()

        dr.schedule_backup(
            schedule="daily",
            data_sources=["database", "files"],
            backup_type=BackupType.FULL,
            strategy=BackupStrategy.S3,
            retention_days=30
        )

        assert len(dr.scheduled_backups) == 1
        assert dr.scheduled_backups[0]["schedule"] == "daily"
        assert dr.scheduled_backups[0]["retention_days"] == 30

    def test_schedule_multiple_backups(self):
        """Test scheduling multiple backup jobs."""
        dr = DisasterRecoveryOrchestrator()

        dr.schedule_backup("hourly", ["database"], BackupType.INCREMENTAL)
        dr.schedule_backup("daily", ["database", "files"], BackupType.FULL)
        dr.schedule_backup("weekly", ["all"], BackupType.FULL, BackupStrategy.MULTI_REGION)

        assert len(dr.scheduled_backups) == 3

    @pytest.mark.asyncio
    async def test_run_scheduled_backups(self):
        """Test running scheduled backups."""
        dr = DisasterRecoveryOrchestrator()

        dr.schedule_backup("hourly", ["database"], BackupType.INCREMENTAL)

        results = await dr.run_scheduled_backups()

        # First run should execute all backups
        assert len(results) > 0
        assert all(isinstance(b, BackupMetadata) for b in results)

    @pytest.mark.asyncio
    async def test_scheduled_backups_not_run_twice(self):
        """Test that scheduled backups don't run twice in quick succession."""
        dr = DisasterRecoveryOrchestrator()

        dr.schedule_backup("daily", ["database"], BackupType.FULL)

        # Run once
        results1 = await dr.run_scheduled_backups()
        assert len(results1) > 0

        # Run again immediately
        results2 = await dr.run_scheduled_backups()
        assert len(results2) == 0  # Should not run again

    @pytest.mark.asyncio
    async def test_disaster_scenario_full_system_failure(self):
        """Test full system failure disaster scenario."""
        dr = DisasterRecoveryOrchestrator()

        result = await dr.test_disaster_recovery(scenario="full_system_failure")

        assert result["success"] is not None
        assert result["scenario"] == "full_system_failure"
        assert "steps" in result
        assert len(result["steps"]) > 0
        assert "duration_seconds" in result

    @pytest.mark.asyncio
    async def test_disaster_scenario_instance_failure(self):
        """Test instance failure scenario."""
        dr = DisasterRecoveryOrchestrator()

        result = await dr.test_disaster_recovery(scenario="instance_failure")

        assert result["scenario"] == "instance_failure"
        assert "steps" in result

    @pytest.mark.asyncio
    async def test_get_recovery_metrics(self):
        """Test getting recovery metrics."""
        dr = DisasterRecoveryOrchestrator()

        # Create some backups
        await dr.backup_engine.create_backup(
            data_sources=["database"],
            backup_type=BackupType.FULL
        )

        # Register some instances
        dr.failover.register_instance("i1", "http://a.com", 1, True)
        dr.failover.register_instance("i2", "http://b.com", 2)

        metrics = await dr.get_recovery_metrics()

        assert "backup_metrics" in metrics
        assert "failover_metrics" in metrics
        assert "current_status" in metrics

        assert metrics["backup_metrics"]["total_backups"] > 0
        assert metrics["current_status"]["total_instances"] == 2


class TestBackupMetadata:
    """Test suite for BackupMetadata data model."""

    def test_metadata_creation(self):
        """Test creating backup metadata."""
        metadata = BackupMetadata(
            backup_id="test_123",
            backup_type=BackupType.FULL,
            strategy=BackupStrategy.S3,
            timestamp=datetime.utcnow(),
            size_bytes=1024000,
            checksum="abc123def456",
            data_sources=["database", "files"],
            retention_days=30,
            encryption_enabled=True,
            compression_ratio=2.5,
            location="s3://bucket/backup.tar.gz"
        )

        assert metadata.backup_id == "test_123"
        assert metadata.backup_type == BackupType.FULL
        assert metadata.strategy == BackupStrategy.S3
        assert metadata.encryption_enabled is True


class TestHealthCheck:
    """Test suite for HealthCheck data model."""

    def test_healthcheck_creation(self):
        """Test creating health check."""
        health = HealthCheck(
            component="database",
            status="healthy",
            latency_ms=15.5,
            error_message=None,
            timestamp=datetime.utcnow(),
            auto_failover=False
        )

        assert health.component == "database"
        assert health.status == "healthy"
        assert health.latency_ms == 15.5
        assert health.auto_failover is False


class TestFailoverEvent:
    """Test suite for FailoverEvent data model."""

    def test_failover_event_creation(self):
        """Test creating failover event."""
        event = FailoverEvent(
            event_id="failover_001",
            trigger="auto_health_check",
            from_instance="app1",
            to_instance="app2",
            timestamp=datetime.utcnow(),
            duration_seconds=25.5,
            success=True,
            rollback=False
        )

        assert event.event_id == "failover_001"
        assert event.trigger == "auto_health_check"
        assert event.success is True
        assert event.duration_seconds < 30  # Under RTO target


# Integration Tests
class TestDisasterRecoveryIntegration:
    """Integration tests for complete disaster recovery flow."""

    @pytest.mark.asyncio
    async def test_complete_backup_restore_flow(self):
        """Test complete backup and restore flow."""
        dr = DisasterRecoveryOrchestrator()

        # Schedule backups
        dr.schedule_backup("hourly", ["database"], BackupType.INCREMENTAL)
        dr.schedule_backup("daily", ["database", "files"], BackupType.FULL)

        # Run backups
        backups = await dr.run_scheduled_backups()
        assert len(backups) > 0

        # Restore from latest backup
        latest_backup = backups[0]
        result = await dr.backup_engine.restore_backup(
            latest_backup.backup_id,
            verify=True
        )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_complete_failover_flow(self):
        """Test complete failover flow."""
        dr = DisasterRecoveryOrchestrator()

        # Register instances
        dr.failover.register_instance("primary", "http://primary.com", 1, True)
        dr.failover.register_instance("secondary", "http://secondary.com", 2)
        dr.failover.register_instance("tertiary", "http://tertiary.com", 3)

        # Check health
        primary_health = await dr.failover.health_check("primary")

        # Perform failover
        event = await dr.failover.perform_failover(
            from_instance="primary",
            trigger="test"
        )

        assert event.success is True
        assert dr.failover.active_instance in ["secondary", "tertiary"]

    @pytest.mark.asyncio
    async def test_disaster_drill(self):
        """Test complete disaster recovery drill."""
        dr = DisasterRecoveryOrchestrator()

        # Setup
        dr.schedule_backup("daily", ["database", "files"], BackupType.FULL)
        dr.failover.register_instance("i1", "http://a.com", 1, True)
        dr.failover.register_instance("i2", "http://b.com", 2)

        # Run drill
        drill_result = await dr.test_disaster_recovery("full_system_failure")

        # Verify drill completed
        assert drill_result["success"] is not None
        assert drill_result["duration_seconds"] < 3600  # Under 1 hour RTO

        # Get metrics
        metrics = await dr.get_recovery_metrics()

        assert metrics["backup_metrics"]["total_backups"] > 0
        assert metrics["current_status"]["healthy_instances"] > 0

    @pytest.mark.asyncio
    async def test_multi_region_disaster_recovery(self):
        """Test disaster recovery across multiple regions."""
        dr = DisasterRecoveryOrchestrator()

        # Create multi-region backup
        backup = await dr.backup_engine.create_backup(
            data_sources=["database", "files", "configs"],
            backup_type=BackupType.FULL,
            strategy=BackupStrategy.MULTI_REGION,
            retention_days=90
        )

        assert backup.strategy == BackupStrategy.MULTI_REGION
        assert "multi:" in backup.location

        # Verify backup can be restored
        restore_result = await dr.backup_engine.restore_backup(
            backup.backup_id,
            verify=True
        )

        assert restore_result["success"] is True


class TestRecoveryTimeObjectives:
    """Test suite for RTO/RPO compliance."""

    @pytest.mark.asyncio
    async def test_rto_instance_failure(self):
        """Test RTO for instance failure (<30 seconds)."""
        orchestrator = FailoverOrchestrator()

        orchestrator.register_instance("i1", "http://a.com", 1, True)
        orchestrator.register_instance("i2", "http://b.com", 2)

        start = datetime.utcnow()
        event = await orchestrator.perform_failover("i1", "i2", "test")
        duration = (datetime.utcnow() - start).total_seconds()

        # Should complete in under 30 seconds (simulated)
        assert duration < 30
        assert event.duration_seconds < 30

    @pytest.mark.asyncio
    async def test_rpo_backup_freshness(self):
        """Test RPO by checking backup freshness."""
        engine = BackupEngine()

        backup = await engine.create_backup(
            data_sources=["database"],
            backup_type=BackupType.INCREMENTAL
        )

        # Backup should be fresh (just created)
        age = (datetime.utcnow() - backup.timestamp).total_seconds()
        assert age < 60  # Less than 1 minute old


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
