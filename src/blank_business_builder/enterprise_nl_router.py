"""Natural-language router for enterprise CEO / agent operations."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .approval_gates import ApprovalGateError, ApprovalStatus, ApprovalStore
from .autonomous_business import AgentRole, AutonomousTask
from .ech0_service import ECH0Service
from .enterprise_agent_policy import resolve_business_policy
from .lead_huntress import LeadHuntress


@dataclass
class NLIntent:
    name: str
    params: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0


ROLE_ALIASES: Dict[str, AgentRole] = {
    "ceo": AgentRole.EXECUTIVE,
    "chief": AgentRole.EXECUTIVE,
    "executive": AgentRole.EXECUTIVE,
    "marketing": AgentRole.MARKETER,
    "marketer": AgentRole.MARKETER,
    "sales": AgentRole.SALES,
    "research": AgentRole.RESEARCHER,
    "researcher": AgentRole.RESEARCHER,
    "finance": AgentRole.FINANCE,
    "support": AgentRole.SUPPORT,
    "orchestrator": AgentRole.ORCHESTRATOR,
}

HELP_TEXT = """You can speak naturally — no commands required. Try:

• "What needs my approval?"
• "Approve the latest request"
• "Show automation policy for SaaS Micro-Tools Empire"
• "Find 5 SaaS founders in the US" (manual Apollo)
• "Have sales search Apollo for B2B marketers" 
• "Add those leads to the CRM"
• "CEO: analyze why sales pipeline stalled this week"
• "Tell marketing to draft a launch email"
• "Is Echo Prime healthy?"
• "Sync these Paperclip issues" (paste JSON in Settings, or include in chat context)
"""


def _extract_count(text: str, default: int = 5) -> int:
    match = re.search(r"\b(\d{1,3})\b", text)
    if match:
        return max(1, min(100, int(match.group(1))))
    return default


def _extract_business_name(message: str, default: str) -> str:
    quoted = re.search(r'["\']([^"\']+)["\']', message)
    if quoted:
        return quoted.group(1).strip()
    for prefix in ("for ", "on ", "in "):
        idx = message.lower().find(prefix)
        if idx >= 0:
            tail = message[idx + len(prefix) :].strip()
            if tail and len(tail.split()) <= 8:
                return tail.rstrip(".?!")
    return default


def _extract_assign_role(message: str) -> Optional[AgentRole]:
    lower = message.lower()
    prefix_patterns = [
        (r"^\s*(?:ceo|chief|executive)\s*[:,-]", AgentRole.EXECUTIVE),
        (r"(?:tell|ask|have|assign)\s+(?:the\s+)?(ceo|chief|executive)\b", AgentRole.EXECUTIVE),
        (r"(?:tell|ask|have|assign)\s+(?:the\s+)?(marketing|marketer)\b", AgentRole.MARKETER),
        (r"(?:tell|ask|have|assign)\s+(?:the\s+)?(sales)\b", AgentRole.SALES),
        (r"(?:tell|ask|have|assign)\s+(?:the\s+)?(research(?:er)?)\b", AgentRole.RESEARCHER),
        (r"assign\s+.+?\s+to\s+(?:the\s+)?(ceo|chief|executive|marketing|marketer|sales|research(?:er)?)\b", None),
    ]
    for pattern, fixed in prefix_patterns:
        match = re.search(pattern, lower)
        if match:
            if fixed is not None:
                return fixed
            alias = match.group(1)
            return ROLE_ALIASES.get(alias, AgentRole.EXECUTIVE)
    if re.match(r"^\s*(?:ceo|chief|executive)\s*[:,-]", lower):
        return AgentRole.EXECUTIVE
    return _extract_role(message)


def _extract_role(text: str) -> Optional[AgentRole]:
    lower = text.lower()
    for alias, role in sorted(ROLE_ALIASES.items(), key=lambda x: -len(x[0])):
        if re.search(rf"\b{re.escape(alias)}\b", lower):
            return role
    return None


def _extract_task_description(message: str) -> Optional[str]:
    patterns = [
        r"(?:tell|ask|have|get|assign)\s+(?:the\s+)?(?:ceo|chief|executive|marketing|marketer|sales|research(?:er)?|finance|support|orchestrator)\s+(?:to\s+)?(.+)",
        r"(?:ceo|chief|executive|marketing|marketer|sales|research(?:er)?|finance|support|orchestrator)\s*[:,-]\s*(.+)",
        r"assign\s+(.+?)\s+to\s+(?:the\s+)?(?:ceo|chief|executive|marketing|marketer|sales|research(?:er)?|finance|support|orchestrator)",
    ]
    for pattern in patterns:
        match = re.search(pattern, message, re.I | re.S)
        if match:
            desc = match.group(1).strip().rstrip(".?!")
            if len(desc) >= 4:
                return desc
    return None


def _find_approval_id(message: str) -> Optional[str]:
    uuid_match = re.search(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        message,
        re.I,
    )
    if uuid_match:
        return uuid_match.group(0)
    return None


def parse_intent(message: str, default_business: str) -> NLIntent:
    text = message.strip()
    lower = text.lower()

    if not text:
        return NLIntent("help")

    if re.search(r"\b(help|what can you do|how do i)\b", lower):
        return NLIntent("help")

    if re.search(r"\b(echo|echo prime).*(health|status|up|running)\b", lower) or re.search(
        r"\b(is echo|check echo)\b", lower
    ):
        return NLIntent("echo_health")

    if re.search(r"\b(routing labels|paperclip labels|label routing)\b", lower):
        return NLIntent("routing_labels")

    if re.search(r"\b(mcp|manifest|hermes)\b", lower) and re.search(
        r"\b(show|view|get|what)\b", lower
    ):
        return NLIntent("mcp_manifest")

    if re.search(r"\b(automation policy|capability matrix|policy for)\b", lower) or (
        re.search(r"\bshow\b", lower) and re.search(r"\bpolicy\b", lower)
    ):
        biz = _extract_business_name(text, default_business)
        return NLIntent("show_policy", {"business_name": biz})

    if re.search(r"\b(reject|deny|decline)\b", lower) and re.search(
        r"\b(approval|request|gate)\b", lower
    ):
        return NLIntent(
            "resolve_approval",
            {"status": "rejected", "approval_id": _find_approval_id(text)},
        )

    if re.search(r"\b(approve|accept|allow)\b", lower) and (
        re.search(r"\b(approval|request|gate|it|that|latest|this)\b", lower)
        or _find_approval_id(text)
    ):
        return NLIntent(
            "resolve_approval",
            {"status": "approved", "approval_id": _find_approval_id(text)},
        )

    if re.search(r"\b(pending|awaiting|needs? my)\b", lower) and re.search(
        r"\b(approval|approvals|sign.?off)\b", lower
    ) or re.search(r"\bwhat needs my approval\b", lower):
        return NLIntent(
            "list_approvals", {"business_name": _extract_business_name(text, default_business)}
        )

    if re.search(r"\b(ingest|import|add).*\b(crm|pipeline|database)\b", lower) or re.search(
        r"\badd (those|these|the) leads\b", lower
    ):
        return NLIntent(
            "ingest_leads",
            {"business_name": _extract_business_name(text, default_business)},
        )

    if re.search(r"\b(sync|import|pull)\b", lower) and re.search(
        r"\b(paperclip|issues)\b", lower
    ):
        return NLIntent(
            "sync_paperclip",
            {"business_name": _extract_business_name(text, default_business)},
        )

    if _extract_task_description(text):
        role = _extract_assign_role(text) or AgentRole.EXECUTIVE
        return NLIntent(
            "assign_task",
            {
                "business_name": _extract_business_name(text, default_business),
                "role": role,
                "description": _extract_task_description(text),
            },
        )

    agent_apollo = re.search(r"\b(agent|auto(?:matic)?)\b", lower) and re.search(
        r"\b(apollo|leads?|prospects?|search)\b", lower
    )
    manual_apollo = re.search(r"\b(find|search|look for|hunt)\b", lower) and re.search(
        r"\b(leads?|prospects?|apollo|founders?|contacts?)\b", lower
    )
    if agent_apollo or manual_apollo:
        criteria = text
        for strip in (
            r"^(please\s+)?(find|search for|look for|have sales|have marketing)\s+",
            r"\b(manually|for me)\s*$",
        ):
            criteria = re.sub(strip, "", criteria, flags=re.I).strip()
        return NLIntent(
            "find_leads",
            {
                "business_name": _extract_business_name(text, default_business),
                "criteria": criteria or "SaaS founders in US",
                "count": _extract_count(text),
                "mode": "agent" if agent_apollo else "manual",
            },
        )

    return NLIntent("general_chat", {"message": text})


async def execute_intent(
    intent: NLIntent,
    *,
    orchestrator: Any,
    business_name: str,
    context: Optional[Dict[str, Any]] = None,
) -> Tuple[str, Dict[str, Any]]:
    ctx = context or {}
    actions: List[str] = []
    data: Dict[str, Any] = {}
    context_updates: Dict[str, Any] = {}

    if intent.name == "help":
        return HELP_TEXT, {"intent": intent.name, "actions": actions, "data": data}

    if intent.name == "echo_health":
        from .bbb_unified_business_library import BBBUnifiedLibrary
        from .config import settings

        summary = BBBUnifiedLibrary().generate_summary_report()
        data = {
            "service": "echo-prime",
            "status": "healthy",
            "businesses_available": summary["total_businesses"],
            "llm_provider": settings.ECH0_LLM_PROVIDER,
            "cloud_inference": "configured" if settings.ECH0_LLM_ENDPOINT else "local",
        }
        actions.append("echo_health")
        status = data.get("status", "unknown")
        return (
            f"Echo Prime is **{status}**. "
            f"LLM provider: {data.get('llm_provider', 'n/a')}. "
            f"{data.get('businesses_available', 0)} business templates loaded.",
            {"intent": intent.name, "actions": actions, "data": data},
        )

    if intent.name == "routing_labels":
        data = {
            "labels": {
                "echo:strategy": {"target": "echo_prime", "mcp_server": "echo_prime"},
                "bbb:execute": {"target": "bbb", "mcp_server": "bbb_ops"},
                "human:apollo": {"target": "human"},
            },
            "role_prefix": "role:<agent_role>",
        }
        actions.append("routing_labels")
        labels = ", ".join(data.get("labels", {}).keys())
        return (
            f"Paperclip routing labels: {labels}. Full map is in the response data.",
            {"intent": intent.name, "actions": actions, "data": data},
        )

    if intent.name == "mcp_manifest":
        data = {
            "name": "bbb_ops",
            "endpoints": {
                "policy": "/api/v1/enterprise/policy/{business_name}",
                "approvals": "/api/v1/enterprise/approvals",
                "leads_search": "/api/v1/enterprise/leads/search",
                "chat": "/api/v1/enterprise/chat",
            },
        }
        actions.append("mcp_manifest")
        return (
            "Hermes can call BBB via the MCP bridge endpoints listed in the response data.",
            {"intent": intent.name, "actions": actions, "data": data},
        )

    if intent.name == "show_policy":
        biz = intent.params.get("business_name", business_name)
        policy = resolve_business_policy(biz).to_dict()
        data = policy
        actions.append("show_policy")
        return (
            f"Automation policy for **{biz}** loaded. "
            f"Roles configured: {', '.join(policy.get('roles', {}).keys()) or 'defaults'}.",
            {"intent": intent.name, "actions": actions, "data": data},
        )

    if intent.name == "list_approvals":
        biz = intent.params.get("business_name", business_name)
        pending = ApprovalStore.list_pending(biz)
        data = {"pending": [r.to_dict() for r in pending]}
        actions.append("list_approvals")
        if not pending:
            return (
                f"No pending approvals for {biz}. You're clear to run gated actions.",
                {"intent": intent.name, "actions": actions, "data": data},
            )
        lines = [
            f"• {r.action.value} ({r.role}) — id `{r.approval_id}`"
            for r in pending[:10]
        ]
        return (
            f"{len(pending)} pending approval(s) for {biz}:\n" + "\n".join(lines)
            + "\n\nSay **approve the latest** or **approve <id>**.",
            {"intent": intent.name, "actions": actions, "data": data},
        )

    if intent.name == "resolve_approval":
        approval_id = intent.params.get("approval_id")
        status = intent.params.get("status", "approved")
        pending = ApprovalStore.list_pending(business_name)
        if not approval_id and pending:
            approval_id = pending[-1].approval_id
        if not approval_id:
            return (
                "I couldn't find an approval to resolve. "
                "Ask **what needs my approval?** first.",
                {"intent": intent.name, "actions": actions, "data": data},
            )
        record = ApprovalStore.resolve(
            approval_id,
            ApprovalStatus.APPROVED if status == "approved" else ApprovalStatus.REJECTED,
        )
        if not record:
            return (
                f"Approval `{approval_id}` was not found.",
                {"intent": intent.name, "actions": actions, "data": data},
            )
        data = record.to_dict()
        actions.append(f"resolve_approval:{status}")
        return (
            f"Done — approval `{approval_id}` is **{record.status.value}**.",
            {"intent": intent.name, "actions": actions, "data": data},
        )

    if intent.name == "find_leads":
        biz = intent.params.get("business_name", business_name)
        huntress = LeadHuntress(orchestrator, business_name=biz)
        mode = intent.params.get("mode", "manual")
        try:
            leads = huntress.find_leads(
                intent.params.get("criteria", "SaaS founders"),
                intent.params.get("count", 5),
                mode=mode,
            )
        except ApprovalGateError as exc:
            data = {"approval_id": exc.approval_id, "blocked": True}
            actions.append("approval_required")
            return (
                f"That action needs board approval first (id `{exc.approval_id}`). "
                f"Say **approve the latest** when you're ready.",
                {"intent": intent.name, "actions": actions, "data": data},
            )
        context_updates["last_leads"] = leads
        data = {"leads": leads, "count": len(leads), "mode": mode}
        actions.append("find_leads")
        return (
            f"Found **{len(leads)}** lead(s) via {mode} Apollo search. "
            f"Say **add those leads to the CRM** to ingest.",
            {
                "intent": intent.name,
                "actions": actions,
                "data": data,
                "context_updates": context_updates,
            },
        )

    if intent.name == "ingest_leads":
        leads = ctx.get("last_leads") or []
        if not leads:
            return (
                "Run a lead search first — e.g. **find 5 SaaS founders in the US**.",
                {"intent": intent.name, "actions": actions, "data": data},
            )
        biz = intent.params.get("business_name", business_name)
        huntress = LeadHuntress(orchestrator, business_name=biz)
        try:
            count = huntress.ingest_leads_to_crm(leads, role="sales")
        except ApprovalGateError as exc:
            data = {"approval_id": exc.approval_id}
            return (
                f"CRM ingest needs approval (id `{exc.approval_id}`). "
                f"Say **approve the latest** to continue.",
                {"intent": intent.name, "actions": actions, "data": data},
            )
        data = {"ingested": count}
        actions.append("ingest_leads")
        return (
            f"Ingested **{count}** lead(s) into the CRM for {biz}.",
            {"intent": intent.name, "actions": actions, "data": data},
        )

    if intent.name == "sync_paperclip":
        issues = ctx.get("paperclip_issues") or []
        if not issues:
            return (
                "To sync Paperclip issues, paste the issues JSON in **Settings → Agent Ops**, "
                "or include `paperclip_issues` in your chat session after exporting from Paperclip. "
                "Then say **sync Paperclip issues** again.",
                {"intent": intent.name, "actions": actions, "data": data},
            )
        biz = intent.params.get("business_name", business_name)
        result = orchestrator.sync_paperclip_issues(issues)
        data = result
        actions.append("sync_paperclip")
        return (
            f"Synced **{len(issues)}** Paperclip issue(s) into the BBB agent queue for {biz}.",
            {"intent": intent.name, "actions": actions, "data": data},
        )

    if intent.name == "assign_task":
        role: AgentRole = intent.params.get("role", AgentRole.EXECUTIVE)
        description = intent.params.get("description") or "Review business priorities"
        task = AutonomousTask(
            task_id=str(uuid.uuid4()),
            role=role,
            description=description,
            priority=7 if role == AgentRole.EXECUTIVE else 6,
        )
        orchestrator.add_task(task)
        data = {
            "task_id": task.task_id,
            "role": role.value,
            "description": description,
        }
        actions.append("assign_task")
        label = "CEO" if role == AgentRole.EXECUTIVE else role.value.replace("_", " ")
        return (
            f"Queued for **{label}**: {description}\n"
            f"Task id `{task.task_id}` — agents will pick this up on the next cycle.",
            {"intent": intent.name, "actions": actions, "data": data},
        )

    # general_chat — Echo with enterprise-aware system prompt
    echo = ECH0Service()
    system = (
        "You are Echo, the BBB enterprise board assistant. "
        "The founder controls CEO and staffed agents through natural language — not CLI commands. "
        "When they ask for operational actions, suggest plain phrases like "
        "'what needs my approval', 'find 5 SaaS leads', or 'CEO: review the pipeline'. "
        "Be concise and actionable."
    )
    reply = await echo._call_ollama(intent.params.get("message", ""), system_prompt=system)
    actions.append("general_chat")
    return reply, {"intent": intent.name, "actions": actions, "data": data}
