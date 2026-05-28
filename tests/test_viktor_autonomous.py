"""
Test Viktor-Style Autonomous Execution Chain
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

Tests the canonical P0 flow:
Paperclip issue → Task lock → Judge loop → Approval gate → Closure
"""

import pytest
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


class TestTaskLockManager:
    """Test task deduplication."""
    
    def test_acquire_lock_success(self):
        from blank_business_builder.task_locks import TaskLockManager
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "locks.json"
            locks = TaskLockManager(state_path=state_path)
            
            # First acquire should succeed
            assert locks.acquire_lock("task-123", "executor", "Test task") is True
            
            # Second acquire should fail (already locked)
            assert locks.acquire_lock("task-123", "executor", "Test task") is False
    
    def test_similar_task_detection(self):
        from blank_business_builder.task_locks import TaskLockManager
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "locks.json"
            locks = TaskLockManager(state_path=state_path)
            
            # Lock a task
            locks.acquire_lock("task-123", "executor", "Generate 10 leads for SaaS")
            
            # Similar description should be detected
            assert locks.is_similar_task_locked("Generate 10 leads for SaaS") is True
            assert locks.is_similar_task_locked("generate 10 leads for saas") is True  # Case insensitive
            
            # Different description should not be locked
            assert locks.is_similar_task_locked("Write code for API") is False


class TestEnterpriseAgentPolicy:
    """Test approval gates."""
    
    def test_requires_approval_for_outbound_email(self):
        from blank_business_builder.enterprise_agent_policy import EnterpriseAgentPolicy
        
        policy = EnterpriseAgentPolicy(company_pack="saas-micro-tools")
        
        # Outbound email always requires approval
        assert policy.requires_approval("sales", "outbound_email") is True
    
    def test_threshold_based_approval(self):
        from blank_business_builder.enterprise_agent_policy import EnterpriseAgentPolicy
        
        policy = EnterpriseAgentPolicy(company_pack="saas-micro-tools")
        
        # Bulk CRM ingest always requires approval (required=true)
        assert policy.requires_approval("sales", "bulk_crm_ingest", quantity=5) is True
        assert policy.requires_approval("sales", "bulk_crm_ingest", quantity=15) is True
        
        # Apollo bulk search always requires approval (required=true)
        # Threshold is informational only
        assert policy.requires_approval("sales", "apollo_bulk_search", quantity=40) is True
        assert policy.requires_approval("sales", "apollo_bulk_search", quantity=60) is True
        
        # Social posting only requires approval over threshold (required=false)
        assert policy.requires_approval("sales", "social_posting", quantity=3) is False
        assert policy.requires_approval("sales", "social_posting", quantity=10) is True
    
    def test_create_approval_request(self):
        from blank_business_builder.enterprise_agent_policy import EnterpriseAgentPolicy
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            approvals_path = os.path.join(tmpdir, "approvals.json")
            
            policy = EnterpriseAgentPolicy(company_pack="saas-micro-tools")
            policy.approvals_path = approvals_path
            
            approval_id = policy.create_approval_request(
                role="sales",
                action="outbound_email",
                description="Send 10 cold emails",
                payload={"leads": ["test@example.com"]},
                quantity=10
            )
            
            assert approval_id is not None
            
            # Should be in pending list
            pending = policy.get_pending_approvals()
            assert len(pending) == 1
            assert pending[0].approval_id == approval_id
            
            # Resolve approval
            assert policy.resolve_approval(approval_id, approved=True, resolved_by="ceo") is True
            
            # Should no longer be pending
            pending = policy.get_pending_approvals()
            assert len(pending) == 0


class TestJudgeService:
    """Test deterministic judge."""
    
    def test_spam_trigger_detection(self):
        from blank_business_builder.judge_service import JudgeService
        
        judge = JudgeService(company_pack="saas-micro-tools")
        
        # Output with spam triggers should get revise/fail
        output_with_spam = {
            "draft_email_body": "Act now! Guaranteed results! Free money!"
        }
        
        verdict = judge.evaluate(output_with_spam, role="sales")
        assert verdict.verdict in ["revise", "fail"]
        assert "spam" in str(verdict.policy_flags).lower() or len(verdict.suggested_revisions) > 0
    
    def test_missing_unsubscribe(self):
        from blank_business_builder.judge_service import JudgeService
        
        judge = JudgeService(company_pack="saas-micro-tools")
        
        # Email without unsubscribe mention
        output_no_unsubscribe = {
            "draft_email_body": "Hi, check out our product.",
            "draft_email_subject": "Quick question"
        }
        
        verdict = judge.evaluate(output_no_unsubscribe, role="sales")
        # Should flag for unsubscribe
        assert "unsubscribe" in str(verdict.suggested_revisions).lower() or verdict.verdict in ["revise", "fail"]


class TestPaperclipWorkSourceSync:
    """Test Paperclip issue routing."""
    
    def test_route_bbb_execute_issue(self):
        from blank_business_builder.paperclip_work_source import PaperclipWorkSourceSync, PaperclipIssue
        from datetime import datetime
        
        sync = PaperclipWorkSourceSync()
        
        issue = PaperclipIssue(
            issue_id="issue-123",
            title="Generate leads for SaaS tools",
            description="Find 10 SaaS companies with 10-50 employees",
            labels=["bbb:execute"],
            state="open",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        task = sync.route_issue(issue)
        
        assert task is not None
        assert task["role"] == "sales"  # Default for bbb:execute
        assert task["requires_approval"] is True  # Sales always needs approval
    
    def test_route_human_apollo_escalates(self):
        from blank_business_builder.paperclip_work_source import PaperclipWorkSourceSync, PaperclipIssue
        from datetime import datetime
        
        sync = PaperclipWorkSourceSync()
        
        issue = PaperclipIssue(
            issue_id="issue-456",
            title="Run Apollo search",
            description="Bulk search for 100 leads",
            labels=["human:apollo"],
            state="open",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        task = sync.route_issue(issue)
        
        # human:apollo should NOT create task (requires human)
        assert task is None
    
    def test_parse_paste_mode(self):
        from blank_business_builder.paperclip_work_source import PaperclipWorkSourceSync
        
        sync = PaperclipWorkSourceSync()
        
        paste_json = json.dumps({
            "id": "pasted-123",
            "title": "Test issue",
            "description": "Test description",
            "labels": ["bbb:execute"],
            "state": "open"
        })
        
        issues = sync.parse_paste(paste_json)
        
        assert len(issues) == 1
        assert issues[0].issue_id == "pasted-123"


class TestAutoJudgeLoopIntegration:
    """Test full judge loop (mocked LLM)."""
    
    @pytest.mark.asyncio
    async def test_judge_loop_with_mock_worker(self):
        from blank_business_builder.auto_judge_loop import AutoJudgeLoop
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            logs_path = os.path.join(tmpdir, "judge.jsonl")
            
            # Create with mocked components
            judge_loop = AutoJudgeLoop(
                company_pack="saas-micro-tools",
                max_revises=3,
                collect_training_data=True
            )
            judge_loop.logs_path = logs_path
            
            # Mock the agent runner
            mock_output = {
                "artifact_type": "lead_batch",
                "batch_id": "test-batch",
                "leads": [
                    {
                        "company": "Test Corp",
                        "prospect_name": "John Doe",
                        "email": "john@test.com",
                        "pain_point": "Manual workflows",
                        "personalization_hook": "Recent funding",
                        "fit_score": 85,
                        "draft_email_subject": "Quick question",
                        "draft_email_body": "Hi John,\n\nI noticed Test Corp recently...\n\nBest,\nAgent\n\n(Unsubscribe anytime)"
                    }
                ],
                "requires_approval": True
            }
            
            with patch.object(judge_loop.agent_runner, 'run_role', new_callable=AsyncMock) as mock_run:
                mock_run.return_value = MagicMock(content=mock_output)
                
                result = await judge_loop.execute_with_judge(
                    role="sales",
                    task_description="Generate 1 test lead",
                    task_id="test-123"
                )
                
                # Should complete (may pass or fail depending on judge rules)
                assert result.total_attempts >= 1
                assert result.revision_history is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
