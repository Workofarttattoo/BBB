"""
Judge Service — Deterministic Compliance Checker
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

Deterministic judge for compliance checking after every worker output:
- Tone analysis
- PII detection  
- Policy flag checking
- Structured output validation

Returns: pass | revise | fail with specific feedback
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class JudgeVerdict:
    """Result from judge evaluation."""
    verdict: str  # "pass" | "revise" | "fail"
    confidence: float
    policy_flags: List[str]
    feedback: str
    suggested_revisions: List[str]
    evaluated_at: datetime
    
    def to_dict(self) -> Dict:
        return {
            "verdict": self.verdict,
            "confidence": self.confidence,
            "policy_flags": self.policy_flags,
            "feedback": self.feedback,
            "suggested_revisions": self.suggested_revisions,
            "evaluated_at": self.evaluated_at.isoformat()
        }


class JudgeService:
    """
    Deterministic judge for agent output compliance.
    
    Usage:
        judge = JudgeService(company_pack="saas-micro-tools")
        verdict = judge.evaluate(agent_output, role="sales")
        
        if verdict.verdict == "pass":
            # Proceed to approval or execution
        elif verdict.verdict == "revise":
            # Send back to agent with feedback
        else:  # fail
            # Escalate to human
    """
    
    def __init__(self, company_pack: str = "saas-micro-tools"):
        self.company_pack = company_pack
        self.pack_path = Path(__file__).parent.parent.parent / "companies" / company_pack
        self.policy = self._load_policy()
        self.eval_log_path = Path(__file__).parent.parent.parent / "logs" / "judge.jsonl"
        self.eval_log_path.parent.mkdir(parents=True, exist_ok=True)
        
    def _load_policy(self) -> Dict[str, Any]:
        """Load policy.json from company pack."""
        policy_path = self.pack_path / "policy.json"
        if policy_path.exists():
            with open(policy_path) as f:
                return json.load(f)
        return {"policy_flags": {"pii_detection": True, "tone_check": True}}
    
    def evaluate(self, agent_output: Dict[str, Any], 
                 role: str, task_description: str = "") -> JudgeVerdict:
        """
        Evaluate agent output against policy and quality standards.
        
        Args:
            agent_output: Raw output from RoleAgentRunner
            role: Agent role that produced output
            task_description: Original task for context
            
        Returns:
            JudgeVerdict with pass/revise/fail decision
        """
        policy_flags = []
        suggested_revisions = []
        feedback_parts = []
        
        # 1. Check for structured output
        if not isinstance(agent_output, dict):
            return JudgeVerdict(
                verdict="fail",
                confidence=1.0,
                policy_flags=["invalid_format"],
                feedback="Output is not a dictionary",
                suggested_revisions=["Return structured JSON output"],
                evaluated_at=datetime.now()
            )
        
        # 2. PII Detection (for sales emails especially)
        if self.policy.get("policy_flags", {}).get("pii_detection", True):
            pii_flags = self._check_pii(agent_output)
            if pii_flags:
                policy_flags.extend(pii_flags)
                suggested_revisions.append("Remove or redact PII from output")
        
        # 3. Tone check
        if self.policy.get("policy_flags", {}).get("tone_check", True):
            tone_flags, tone_feedback = self._check_tone(agent_output, role)
            if tone_flags:
                policy_flags.extend(tone_flags)
                feedback_parts.append(tone_feedback)
                suggested_revisions.append("Adjust tone to be more professional/helpful")
        
        # 4. Spam trigger detection (for sales)
        if role == "sales":
            spam_flags = self._check_spam_triggers(agent_output)
            if spam_flags:
                policy_flags.extend(spam_flags)
                feedback_parts.append("Contains spam trigger words")
                suggested_revisions.append("Remove spam trigger words like 'guarantee', 'free', 'act now'")
        
        # 5. Compliance checks
        compliance_flags = self._check_compliance(agent_output, role)
        if compliance_flags:
            policy_flags.extend(compliance_flags)
            feedback_parts.append("Missing required compliance elements")
            if "unsubscribe" in str(compliance_flags):
                suggested_revisions.append("Add unsubscribe mention to email drafts")
        
        # 6. Quality checks based on role
        quality_score, quality_feedback = self._check_quality(agent_output, role)
        
        # 7. Legal review triggers
        legal_flags = self._check_legal_triggers(agent_output)
        if legal_flags:
            policy_flags.extend(legal_flags)
            suggested_revisions.append("Flagged for legal review")
        
        # Determine verdict
        verdict, confidence = self._determine_verdict(
            policy_flags, quality_score, len(suggested_revisions)
        )
        
        # Build feedback
        if not feedback_parts:
            feedback = "Output passes all checks"
        else:
            feedback = "; ".join(feedback_parts)
            
        verdict_obj = JudgeVerdict(
            verdict=verdict,
            confidence=confidence,
            policy_flags=list(set(policy_flags)),  # Dedupe
            feedback=feedback,
            suggested_revisions=suggested_revisions,
            evaluated_at=datetime.now()
        )
        
        # Log evaluation
        self._log_evaluation(agent_output, role, task_description, verdict_obj)
        
        return verdict_obj
    
    def _check_pii(self, output: Dict) -> List[str]:
        """Check for PII in output."""
        flags = []
        output_str = json.dumps(output)
        
        # Email pattern
        if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', output_str):
            # Emails are expected in sales leads, but flag if in wrong context
            if "leads" not in output and "email" not in output.get("artifact_type", ""):
                flags.append("unexpected_email_pii")
                
        # Phone pattern
        if re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', output_str):
            flags.append("phone_pii")
            
        # SSN pattern
        if re.search(r'\b\d{3}-\d{2}-\d{4}\b', output_str):
            flags.append("ssn_pii")
            
        return flags
    
    def _check_tone(self, output: Dict, role: str) -> Tuple[List[str], str]:
        """Check tone appropriateness."""
        flags = []
        feedback = ""
        
        output_str = json.dumps(output).lower()
        
        # Aggressive/pushy language
        pushy_phrases = ["you must", "you need to", "don't miss out", "last chance"]
        for phrase in pushy_phrases:
            if phrase in output_str:
                flags.append("pushy_tone")
                feedback = "Tone is too aggressive/pushy"
                break
                
        # Overly casual for B2B
        casual_phrases = ["hey there", "what's up", "cool", "awesome"]
        for phrase in casual_phrases:
            if phrase in output_str:
                flags.append("too_casual")
                if not feedback:
                    feedback = "Tone is too casual for B2B context"
                break
                
        return flags, feedback
    
    def _check_spam_triggers(self, output: Dict) -> List[str]:
        """Check for spam trigger words in sales content."""
        flags = []
        
        spam_words = [
            "guarantee", "guaranteed", "free", "act now", "limited time",
            "urgent", "congratulations", "winner", "cash bonus", "risk-free",
            "no cost", "instant", "explode", "skyrocket", "miracle"
        ]
        
        output_str = json.dumps(output).lower()
        
        for word in spam_words:
            if word in output_str:
                flags.append(f"spam_trigger:{word}")
                
        return flags[:5]  # Limit to first 5
    
    def _check_compliance(self, output: Dict, role: str) -> List[str]:
        """Check compliance requirements."""
        flags = []
        
        if role == "sales":
            # Check for unsubscribe in email drafts
            if output.get("artifact_type") == "email_draft":
                email_body = output.get("draft_email_body", "")
                if "unsubscribe" not in email_body.lower() and "opt-out" not in email_body.lower():
                    flags.append("missing_unsubscribe")
                    
        return flags
    
    def _check_quality(self, output: Dict, role: str) -> Tuple[float, str]:
        """Check output quality based on role-specific criteria."""
        score = 1.0
        feedback = ""
        
        if role == "sales":
            # Check for personalization
            leads = output.get("leads", [])
            if leads:
                missing_personalization = sum(
                    1 for lead in leads 
                    if not lead.get("personalization_hook")
                )
                if missing_personalization > len(leads) * 0.3:
                    score -= 0.3
                    feedback = ">30% of leads missing personalization hooks"
                    
            # Check fit scores
            if leads:
                low_fit = sum(1 for lead in leads if lead.get("fit_score", 0) < 50)
                if low_fit > len(leads) * 0.2:
                    score -= 0.2
                    if feedback:
                        feedback += "; "
                    feedback += ">20% of leads have low fit scores (<50)"
                    
        elif role == "engineer":
            # Check for tests
            changes = output.get("changes", [])
            if changes:
                missing_tests = sum(
                    1 for change in changes
                    if not change.get("tests_added") and change.get("change_type") == "create"
                )
                if missing_tests > 0:
                    score -= 0.3
                    feedback = "New files without tests"
        
        return score, feedback
    
    def _check_legal_triggers(self, output: Dict) -> List[str]:
        """Check for legal review triggers."""
        flags = []
        triggers = self.policy.get("policy_flags", {}).get("legal_review_trigger", [])
        
        output_str = json.dumps(output).lower()
        
        for trigger in triggers:
            if trigger.lower() in output_str:
                flags.append(f"legal_trigger:{trigger}")
                
        return flags
    
    def _determine_verdict(self, policy_flags: List[str], 
                          quality_score: float, 
                          revision_count: int) -> Tuple[str, float]:
        """Determine final verdict based on all checks."""
        
        # Automatic fail conditions
        fail_flags = ["ssn_pii", "invalid_format"]
        if any(flag in fail_flags for flag in policy_flags):
            return "fail", 0.95
            
        # Revise conditions
        if len(policy_flags) >= 3:
            return "revise", 0.8
            
        if quality_score < 0.6:
            return "revise", 0.75
            
        if revision_count >= 2:
            return "revise", 0.7
            
        # Pass with minor flags
        if policy_flags:
            return "pass", 0.85  # Pass but with flags noted
            
        # Clean pass
        if quality_score >= 0.9:
            return "pass", 0.95
        else:
            return "pass", 0.85
    
    def _log_evaluation(self, output: Dict, role: str, task: str, 
                       verdict: JudgeVerdict) -> None:
        """Log evaluation to JSONL for training/analysis."""
        log_entry = {
            "timestamp": verdict.evaluated_at.isoformat(),
            "role": role,
            "task": task,
            "output_summary": {
                "artifact_type": output.get("artifact_type", "unknown"),
                "content_keys": list(output.keys())
            },
            "verdict": verdict.verdict,
            "confidence": verdict.confidence,
            "policy_flags": verdict.policy_flags,
            "feedback": verdict.feedback
        }
        
        try:
            with open(self.eval_log_path, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to log evaluation: {e}")
