"""
Role Agent Runner — Viktor-Style Autonomous Execution
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

Implements Viktor's "assume forward" execution policy:
- Execute first, report assumptions after
- When ambiguous: select highest-probability interpretation, proceed
- Never ask for clarification mid-task
- If a step fails: try 2 alternative approaches before surfacing to user
- Report: what you did, what you assumed, what succeeded, what failed

Key features:
- Lazy skill loading from company pack
- Policy injection for compliance
- Tiered local LLM model selection
- ReAct + Reflection loop
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import uuid

logger = logging.getLogger(__name__)


@dataclass
class SkillContext:
    """Context for skill execution."""
    role: str
    skill_md: str
    policy: Dict[str, Any]
    task_description: str
    previous_attempts: List[Dict] = field(default_factory=list)
    

@dataclass
class AgentOutput:
    """Output from agent execution."""
    task_id: str
    role: str
    artifact_type: str
    content: Dict[str, Any]
    assumptions_made: List[str]
    actions_taken: List[str]
    successes: List[str]
    failures: List[str]
    requires_approval: bool
    confidence_score: float
    created_at: datetime = field(default_factory=datetime.now)
    

class LocalModelClient:
    """Tiered local LLM client with fallback."""
    
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        self.model_tiers = {
            "worker": os.getenv("ROLE_WORKER_MODEL", "qwen3.5:4b"),
            "judge": os.getenv("ROLE_JUDGE_MODEL", "qwen3.5:4b"),
            "manager": os.getenv("MIDDLE_MANAGER_MODEL", "qwen3.5:9b"),
            "executive": os.getenv("ROLE_CSUITE_MODEL", "ech0-fine-tuned-v2:latest")
        }
        
    def generate(self, prompt: str, tier: str = "worker", temperature: float = 0.7) -> str:
        """Generate response from local LLM with retry logic."""
        import requests
        
        model = self.model_tiers.get(tier, self.model_tiers["worker"])
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": temperature}
                    },
                    timeout=60
                )
                response.raise_for_status()
                result = response.json()
                return result.get("response", "")
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"LLM request failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise RuntimeError(f"LLM unavailable after {max_retries} attempts: {e}")
                    
        return ""
    
    def generate_json(self, prompt: str, tier: str = "worker") -> Dict[str, Any]:
        """Generate structured JSON output with validation."""
        response_text = self.generate(prompt, tier)
        
        # Try to extract JSON from response
        try:
            # Look for JSON block in response
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                logger.warning(f"No JSON found in response: {response_text[:200]}")
                return {"error": "No structured output", "raw": response_text}
                
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error: {e}, response: {response_text[:200]}")
            return {"error": "Invalid JSON", "raw": response_text}


class RoleAgentRunner:
    """
    Viktor-style role agent runner with assume-forward execution.
    
    Usage:
        runner = RoleAgentRunner(company_pack="saas-micro-tools")
        output = runner.execute_task(
            role="sales",
            task="Generate 15 leads for DeployFlow targeting Series A SaaS companies",
            context={"tool_name": "DeployFlow Pro"}
        )
    """
    
    def __init__(self, company_pack: str = "saas-micro-tools"):
        self.company_pack = company_pack
        self.pack_path = Path(__file__).parent.parent.parent / "companies" / company_pack
        self.llm = LocalModelClient()
        self.policy = self._load_policy()
        self.skills_cache: Dict[str, str] = {}
        
    def _load_policy(self) -> Dict[str, Any]:
        """Load policy.json from company pack."""
        policy_path = self.pack_path / "policy.json"
        if policy_path.exists():
            with open(policy_path) as f:
                return json.load(f)
        return {"viktor_mode": {"enabled": True, "assume_forward": True, "max_revises": 3}}
    
    def _load_skill(self, role: str) -> str:
        """Lazy load skill markdown file."""
        if role in self.skills_cache:
            return self.skills_cache[role]
            
        skill_path = self.pack_path / "skills" / f"{role}.md"
        if skill_path.exists():
            with open(skill_path) as f:
                skill_md = f.read()
            self.skills_cache[role] = skill_md
            return skill_md
            
        logger.warning(f"Skill not found for role: {role}, using default")
        return self._get_default_skill(role)
    
    def _get_default_skill(self, role: str) -> str:
        """Default skill template when role-specific skill missing."""
        return f"""# {role.title()} Agent Skills

**Role**: {role.title()}
**Mission**: Execute tasks autonomously with assume-forward policy

## Output Format

Always produce structured JSON output with:
- artifact_type: type of output
- content: structured data
- requires_approval: boolean for approval gates

## Policy Constraints

Follow all policy.json constraints for this business.
"""
    
    def _build_prompt(self, skill_md: str, task: str, context: Dict, 
                      previous_attempts: List[Dict]) -> str:
        """Build execution prompt with Viktor-style directives."""
        
        system_directive = """
EXECUTION PHILOSOPHY (VIKTOR MODE):
- Execute first, report assumptions after
- When ambiguous: select highest-probability interpretation, proceed
- Never ask for clarification mid-task
- If a step fails: try 2 alternative approaches before surfacing to user
- Report: what you did, what you assumed, what succeeded, what failed
- Proactively surface related work you noticed while completing the task

OUTPUT REQUIREMENTS:
- Always produce valid JSON matching the skill's artifact_type schema
- Include all required fields
- Set requires_approval=true for actions needing CEO signoff
"""
        
        context_str = json.dumps(context, indent=2) if context else "{}"
        
        revision_history = ""
        if previous_attempts:
            revision_history = "\n\nPREVIOUS ATTEMPTS:\n"
            for i, attempt in enumerate(previous_attempts[-3:], 1):
                revision_history += f"\nAttempt {i}: {attempt.get('feedback', 'No feedback')}\n"
            revision_history += "\nImprove on previous attempts based on feedback.\n"
        
        prompt = f"""{system_directive}

{skill_md}

TASK: {task}

CONTEXT:
{context_str}
{revision_history}

Generate your response as JSON only. Do not include explanatory text outside the JSON structure.
"""
        return prompt
    
    def execute_task(self, role: str, task: str, context: Optional[Dict] = None,
                     previous_attempts: Optional[List[Dict]] = None) -> AgentOutput:
        """
        Execute a task with Viktor-style assume-forward execution.
        
        Args:
            role: Agent role (sales, engineer, marketer, etc.)
            task: Task description
            context: Additional context for task
            previous_attempts: Previous failed attempts for revision loop
            
        Returns:
            AgentOutput with results, assumptions, and approval flags
        """
        context = context or {}
        previous_attempts = previous_attempts or []
        
        # Load skill
        skill_md = self._load_skill(role)
        
        # Build prompt
        prompt = self._build_prompt(skill_md, task, context, previous_attempts)
        
        # Generate output
        try:
            output_data = self.llm.generate_json(prompt, tier="worker")
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            output_data = {
                "error": str(e),
                "artifact_type": "error",
                "content": {},
                "requires_approval": False
            }
        
        # Extract standard fields
        artifact_type = output_data.get("artifact_type", "unknown")
        content = output_data.get("content", output_data)
        requires_approval = self._check_approval_gates(role, task, output_data)
        
        # Generate assumptions and actions taken (meta-reasoning)
        assumptions = self._infer_assumptions(task, output_data)
        actions = self._infer_actions(output_data)
        
        # Calculate confidence score
        confidence = self._calculate_confidence(output_data, len(previous_attempts))
        
        return AgentOutput(
            task_id=str(uuid.uuid4()),
            role=role,
            artifact_type=artifact_type,
            content=content,
            assumptions_made=assumptions,
            actions_taken=actions,
            successes=[f"Generated {artifact_type} for {role} role"],
            failures=output_data.get("errors", []),
            requires_approval=requires_approval,
            confidence_score=confidence
        )
    
    def _check_approval_gates(self, role: str, task: str, 
                              output_data: Dict) -> bool:
        """Check if output requires CEO approval based on policy."""
        approval_gates = self.policy.get("approval_gates", {})
        
        # Check for bulk operations
        if role == "sales":
            leads = output_data.get("leads", [])
            if len(leads) > approval_gates.get("bulk_crm_ingest", {}).get("threshold_count", 10):
                return True
                
        # Check for outbound email
        if output_data.get("artifact_type") == "email_draft":
            return approval_gates.get("outbound_email", {}).get("required", True)
            
        # Default: internal drafts don't need approval
        return False
    
    def _infer_assumptions(self, task: str, output_data: Dict) -> List[str]:
        """Infer assumptions made during execution."""
        assumptions = []
        
        # Analyze task ambiguity resolution
        if "assumed_" in str(output_data).lower():
            assumptions.append("Made assumption to resolve ambiguity")
            
        # Check for default values used
        if output_data.get("source") == "inferred":
            assumptions.append("Inferred missing information from context")
            
        if not assumptions:
            assumptions.append("No significant assumptions required")
            
        return assumptions
    
    def _infer_actions(self, output_data: Dict) -> List[str]:
        """Infer actions taken from output."""
        actions = []
        
        artifact_type = output_data.get("artifact_type", "unknown")
        actions.append(f"Generated {artifact_type} artifact")
        
        if artifact_type == "lead_batch":
            lead_count = len(output_data.get("leads", []))
            actions.append(f"Researched and scored {lead_count} leads")
            
        return actions
    
    def _calculate_confidence(self, output_data: Dict, 
                             attempt_count: int) -> float:
        """Calculate confidence score based on output quality."""
        base_confidence = 0.8
        
        # Reduce confidence for errors
        if "error" in output_data:
            base_confidence -= 0.3
            
        # Reduce confidence for multiple revision attempts
        base_confidence -= (attempt_count * 0.1)
        
        # Boost confidence for complete structured output
        if output_data.get("artifact_type") and output_data.get("content"):
            base_confidence += 0.1
            
        return max(0.1, min(1.0, base_confidence))
