"""
Auto Judge Loop — Revision Cycle with Max Attempts
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

Implements the ReAct + Reflection loop:
- Run worker agent
- Judge evaluates output
- If revise: send back with feedback (max 3 attempts)
- If pass: proceed to approval or execution
- If fail: escalate to human

Usage:
    judge_loop = AutoJudgeLoop(company_pack="saas-micro-tools")
    result = await judge_loop.execute_with_judge(
        role="sales",
        task_description="Generate 10 leads for SaaS tools",
        context={}
    )
    
    if result["success"]:
        # Output passed judge, ready for approval/execution
    else:
        # Failed after max revises, needs human intervention
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from .role_agent_runner import RoleAgentRunner, AgentOutput
from .judge_service import JudgeService, JudgeVerdict

logger = logging.getLogger(__name__)


@dataclass
class RevisionAttempt:
    """Record of a single revision attempt."""
    attempt_number: int
    agent_output: Dict[str, Any]
    verdict: JudgeVerdict
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class JudgeLoopResult:
    """Final result from auto-judge loop."""
    success: bool
    final_output: Optional[Dict[str, Any]]
    total_attempts: int
    revision_history: List[RevisionAttempt]
    final_verdict: Optional[JudgeVerdict]
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "final_output": self.final_output,
            "total_attempts": self.total_attempts,
            "revision_history": [
                {
                    "attempt": r.attempt_number,
                    "verdict": r.verdict.to_dict() if r.verdict else None,
                    "timestamp": r.timestamp.isoformat()
                }
                for r in self.revision_history
            ],
            "final_verdict": self.final_verdict.to_dict() if self.final_verdict else None,
            "error_message": self.error_message
        }


class AutoJudgeLoop:
    """
    Autonomous judge loop with revision cycles.
    
    This is the core Viktor-style execution engine:
    1. Worker produces output
    2. Judge evaluates deterministically
    3. If revise: worker tries again with feedback (max N times)
    4. Track all attempts for training data
    5. Surface errors clearly, never silently fail
    """
    
    def __init__(
        self,
        company_pack: str = "saas-micro-tools",
        max_revises: int = 3,
        collect_training_data: bool = True
    ):
        self.company_pack = company_pack
        self.max_revises = max_revises
        self.collect_training_data = collect_training_data
        
        self.agent_runner = RoleAgentRunner(company_pack=company_pack)
        self.judge = JudgeService(company_pack=company_pack)
        
        # Training data collection
        self.logs_path = Path(__file__).parent.parent.parent / "logs" / "judge.jsonl"
        self.logs_path.parent.mkdir(parents=True, exist_ok=True)
    
    async def execute_with_judge(
        self,
        role: str,
        task_description: str,
        context: Optional[Dict[str, Any]] = None,
        task_id: Optional[str] = None
    ) -> JudgeLoopResult:
        """
        Execute worker with automatic judge revision loop.
        
        Args:
            role: Agent role (sales, engineer, marketer, etc.)
            task_description: Natural language task
            context: Optional context dict (previous outputs, constraints, etc.)
            task_id: Optional task ID for tracking
            
        Returns:
            JudgeLoopResult with success status and final output
        """
        context = context or {}
        revision_history: List[RevisionAttempt] = []
        last_error = None
        
        logger.info(f"Starting judge loop for {role}: {task_description[:100]}...")
        
        for attempt in range(self.max_revises + 1):  # +1 for initial attempt
            try:
                # Step 1: Run worker agent
                logger.info(f"Attempt {attempt + 1}/{self.max_revises + 1}")
                
                # Build prompt with revision feedback if this is a retry
                if attempt > 0 and revision_history:
                    last_verdict = revision_history[-1].verdict
                    context["revision_feedback"] = {
                        "attempt": attempt,
                        "feedback": last_verdict.feedback,
                        "suggested_revisions": last_verdict.suggested_revisions
                    }
                
                agent_output = await self.agent_runner.run_role(
                    role=role,
                    task_description=task_description,
                    context=context,
                    task_id=task_id
                )
                
                # Step 2: Judge evaluates output
                verdict = self.judge.evaluate(
                    agent_output=agent_output.content if isinstance(agent_output, AgentOutput) else agent_output,
                    role=role,
                    task_description=task_description
                )
                
                # Record attempt
                revision_attempt = RevisionAttempt(
                    attempt_number=attempt + 1,
                    agent_output=agent_output.content if isinstance(agent_output, AgentOutput) else agent_output,
                    verdict=verdict
                )
                revision_history.append(revision_attempt)
                
                # Step 3: Check verdict
                if verdict.verdict == "pass":
                    logger.info(f"Judge PASS on attempt {attempt + 1}")
                    
                    # Collect training data
                    if self.collect_training_data:
                        self._log_training_sample(
                            input=task_description,
                            output=agent_output.content if isinstance(agent_output, AgentOutput) else agent_output,
                            verdict="pass",
                            policy_flags=verdict.policy_flags
                        )
                    
                    return JudgeLoopResult(
                        success=True,
                        final_output=agent_output.content if isinstance(agent_output, AgentOutput) else agent_output,
                        total_attempts=attempt + 1,
                        revision_history=revision_history,
                        final_verdict=verdict
                    )
                
                elif verdict.verdict == "revise":
                    logger.info(f"Judge REVISE on attempt {attempt + 1}: {verdict.feedback}")
                    
                    if attempt >= self.max_revises:
                        # Max attempts reached
                        logger.warning(f"Max revises ({self.max_revises}) reached, failing task")
                        
                        if self.collect_training_data:
                            self._log_training_sample(
                                input=task_description,
                                output=agent_output.content if isinstance(agent_output, AgentOutput) else agent_output,
                                verdict="revise_max_attempts",
                                policy_flags=verdict.policy_flags
                            )
                        
                        return JudgeLoopResult(
                            success=False,
                            final_output=None,
                            total_attempts=attempt + 1,
                            revision_history=revision_history,
                            final_verdict=verdict,
                            error_message=f"Failed after {self.max_revises} revision attempts: {verdict.feedback}"
                        )
                    
                    # Continue to next attempt with feedback
                    continue
                
                else:  # fail
                    logger.error(f"Judge FAIL on attempt {attempt + 1}: {verdict.feedback}")
                    
                    if self.collect_training_data:
                        self._log_training_sample(
                            input=task_description,
                            output=agent_output.content if isinstance(agent_output, AgentOutput) else agent_output,
                            verdict="fail",
                            policy_flags=verdict.policy_flags
                        )
                    
                    return JudgeLoopResult(
                        success=False,
                        final_output=None,
                        total_attempts=attempt + 1,
                        revision_history=revision_history,
                        final_verdict=verdict,
                        error_message=f"Critical failure: {verdict.feedback}"
                    )
                
            except Exception as e:
                logger.exception(f"Error in judge loop attempt {attempt + 1}: {e}")
                last_error = str(e)
                
                if attempt >= self.max_revises:
                    return JudgeLoopResult(
                        success=False,
                        final_output=None,
                        total_attempts=attempt + 1,
                        revision_history=revision_history,
                        final_verdict=None,
                        error_message=f"System error after {attempt + 1} attempts: {e}"
                    )
        
        # Should not reach here, but safety fallback
        return JudgeLoopResult(
            success=False,
            final_output=None,
            total_attempts=self.max_revises + 1,
            revision_history=revision_history,
            final_verdict=None,
            error_message=last_error or "Unknown error in judge loop"
        )
    
    def _log_training_sample(
        self,
        input: str,
        output: Dict[str, Any],
        verdict: str,
        policy_flags: List[str]
    ):
        """Log sample to judge.jsonl for future training."""
        sample = {
            "timestamp": datetime.now().isoformat(),
            "company_pack": self.company_pack,
            "input": input,
            "output": output,
            "verdict": verdict,
            "policy_flags": policy_flags
        }
        
        try:
            with open(self.logs_path, "a") as f:
                f.write(json.dumps(sample) + "\n")
        except Exception as e:
            logger.warning(f"Failed to log training sample: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get judge loop statistics from logs."""
        if not self.logs_path.exists():
            return {"total": 0, "pass": 0, "revise": 0, "fail": 0, "revise_rate": 0.0}
        
        total = 0
        pass_count = 0
        revise_count = 0
        fail_count = 0
        
        try:
            with open(self.logs_path) as f:
                for line in f:
                    sample = json.loads(line.strip())
                    total += 1
                    verdict = sample.get("verdict", "")
                    if verdict == "pass":
                        pass_count += 1
                    elif verdict.startswith("revise"):
                        revise_count += 1
                    elif verdict == "fail":
                        fail_count += 1
        except Exception as e:
            logger.warning(f"Failed to read stats: {e}")
        
        revise_rate = (revise_count / total * 100) if total > 0 else 0.0
        
        return {
            "total": total,
            "pass": pass_count,
            "revise": revise_count,
            "fail": fail_count,
            "revise_rate": round(revise_rate, 2)
        }
