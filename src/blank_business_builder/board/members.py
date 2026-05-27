"""
AI C-Suite Board Members
========================
Each class is a different frontier model specialised for its C-suite role.
All run locally on a VPS via Ollama (OpenAI-compatible API).

VPS setup — pull all models once:
    ollama pull deepseek-r1:14b          # CEO
    ollama pull hermes3:8b               # COO  (already running)
    ollama pull qwen2.5:7b               # CFO
    ollama pull deepseek-coder-v2:16b    # CTO
    ollama pull llama3.2:3b              # CMO
    ollama pull qwen3:30b-a3b            # CSO fallback (MoE, only 3B active)
    # Grok: if you can serve grok-1 GGUF, point GROK_VPS_URL to it
"""
from __future__ import annotations

import os
from typing import List, Optional

from .base_member import BoardMember


# ── CEO ─────────────────────────────────────────────────────────────────────

class CEO(BoardMember):
    """
    Chief Executive Officer — DeepSeek-R1:14b
    Speciality: chain-of-thought reasoning, big-picture strategy, final calls.
    High temperature for bold thinking; extended token budget for deep reasoning.
    """
    role        = "CEO"
    title       = "Chief Executive Officer"
    model       = "deepseek-r1:14b"
    temperature = 0.5
    max_tokens  = 2048
    expertise   = [
        "Strategic vision", "Final decision authority", "Risk assessment",
        "Capital allocation", "M&A and partnerships", "Board reporting",
        "Long-term competitive positioning",
    ]
    personality = (
        "You think in first principles. You challenge assumptions, reason step-by-step "
        "through problems (<think>...</think>), and make decisive calls even under uncertainty. "
        "You own outcomes."
    )

    def __init__(self, **kwargs):
        url = kwargs.pop("vps_url", None) or os.getenv("CEO_VPS_URL") or os.getenv("HERMES_VPS_URL", "http://localhost:11434")
        model = os.getenv("CEO_MODEL", self.model)
        super().__init__(vps_url=url, **kwargs)
        self.model = model


# ── COO ─────────────────────────────────────────────────────────────────────

class COO(BoardMember):
    """
    Chief Operating Officer — Hermes-3:8b
    Speciality: function calling, task orchestration, workflow execution.
    Already running as the primary BBB agent — now promoted to C-suite.
    """
    role        = "COO"
    title       = "Chief Operating Officer"
    model       = "hermes3:8b"
    temperature = 0.3
    max_tokens  = 1024
    expertise   = [
        "Agent orchestration", "Workflow design", "Process optimisation",
        "Resource allocation", "SLA management", "Tool/API execution",
        "Cross-team coordination", "KPI tracking",
    ]
    personality = (
        "You are relentlessly operational. You translate strategy into specific, "
        "measurable, executable steps. You think in workflows and dependencies. "
        "You escalate blockers immediately."
    )

    def __init__(self, **kwargs):
        url = kwargs.pop("vps_url", None) or os.getenv("COO_VPS_URL") or os.getenv("HERMES_VPS_URL", "http://localhost:11434")
        model = os.getenv("COO_MODEL", self.model)
        super().__init__(vps_url=url, **kwargs)
        self.model = model


# ── CFO ─────────────────────────────────────────────────────────────────────

class CFO(BoardMember):
    """
    Chief Financial Officer — Qwen2.5:7b
    Speciality: financial modelling, unit economics, cash flow, revenue ops.
    Low temperature — financial decisions need precision, not creativity.
    """
    role        = "CFO"
    title       = "Chief Financial Officer"
    model       = "qwen2.5:7b"
    temperature = 0.2
    max_tokens  = 1024
    expertise   = [
        "P&L management", "Cash flow forecasting", "Unit economics",
        "Stripe/revenue tracking", "Budget approval", "Tax optimisation",
        "Burn rate analysis", "Fundraising readiness",
    ]
    personality = (
        "You are precise and conservative by default. You always think in numbers: "
        "CAC, LTV, MRR, burn rate, runway. You flag financial risks before they become "
        "problems. You approve spending only when ROI is clear."
    )

    def __init__(self, **kwargs):
        url = kwargs.pop("vps_url", None) or os.getenv("CFO_VPS_URL") or os.getenv("HERMES_VPS_URL", "http://localhost:11434")
        model = os.getenv("CFO_MODEL", self.model)
        super().__init__(vps_url=url, **kwargs)
        self.model = model


# ── CTO ─────────────────────────────────────────────────────────────────────

class CTO(BoardMember):
    """
    Chief Technology Officer — DeepSeek-Coder-V2:16b
    Speciality: system architecture, code review, technical debt, infra.
    """
    role        = "CTO"
    title       = "Chief Technology Officer"
    model       = "deepseek-coder-v2:16b"
    temperature = 0.3
    max_tokens  = 2048
    expertise   = [
        "System architecture", "API design", "Security review",
        "Scalability planning", "Database optimisation", "CI/CD pipelines",
        "AI/ML model selection", "Technical debt prioritisation",
    ]
    personality = (
        "You think in systems. Every technical decision considers security, scalability, "
        "and maintainability. You write and review code directly. You prefer boring, "
        "reliable solutions over clever, fragile ones."
    )

    def __init__(self, **kwargs):
        url = kwargs.pop("vps_url", None) or os.getenv("CTO_VPS_URL") or os.getenv("HERMES_VPS_URL", "http://localhost:11434")
        model = os.getenv("CTO_MODEL", self.model)
        super().__init__(vps_url=url, **kwargs)
        self.model = model


# ── CMO ─────────────────────────────────────────────────────────────────────

class CMO(BoardMember):
    """
    Chief Marketing Officer — Llama3.2:3b
    Speciality: brand voice, campaigns, content, customer acquisition.
    Higher temperature — marketing needs creativity and novelty.
    Fast 3B model for high-volume content generation.
    """
    role        = "CMO"
    title       = "Chief Marketing Officer"
    model       = "llama3.2:3b"
    temperature = 0.7
    max_tokens  = 1024
    expertise   = [
        "Brand strategy", "Content marketing", "SEO", "Paid acquisition",
        "Email campaigns", "Social media", "Conversion optimisation",
        "Customer segmentation", "Viral growth tactics",
    ]
    personality = (
        "You think in stories and audiences. Every decision starts with the customer: "
        "who are they, what do they feel, what action do you want them to take? "
        "You produce punchy, specific copy. You test everything."
    )

    def __init__(self, **kwargs):
        url = kwargs.pop("vps_url", None) or os.getenv("CMO_VPS_URL") or os.getenv("HERMES_VPS_URL", "http://localhost:11434")
        model = os.getenv("CMO_MODEL", self.model)
        super().__init__(vps_url=url, **kwargs)
        self.model = model


# ── CSO (Grok / fallback) ────────────────────────────────────────────────────

class CSO(BoardMember):
    """
    Chief Strategy Officer — Grok-1 (if running) OR Qwen3:30b-a3b (MoE fallback)

    Grok-1 is 314B MoE — serve it if you have the hardware:
        GROK_VPS_URL=http://your-grok-server:8000
        CSO_MODEL=grok-1

    Otherwise Qwen3:30b-a3b is an excellent CSO:
        ollama pull qwen3:30b-a3b
        CSO_MODEL=qwen3:30b-a3b
    Only 3B parameters are ACTIVE per forward pass (MoE) — runs on ~8GB VRAM.

    Grok's personality: bold, contrarian, willing to challenge consensus.
    """
    role        = "CSO"
    title       = "Chief Strategy Officer"
    model       = "qwen3:30b-a3b"   # overridden by CSO_MODEL env var
    temperature = 0.6
    max_tokens  = 1500
    expertise   = [
        "Competitive strategy", "Market disruption", "New business models",
        "Partnership strategy", "International expansion", "Competitive intelligence",
        "Scenario planning", "First-mover vs fast-follower decisions",
    ]
    personality = (
        "You are the contrarian on the board. You challenge groupthink, ask uncomfortable "
        "questions, and identify the strategy everyone else is afraid to pursue. "
        "You think 3 moves ahead. Bold beats cautious when the upside is asymmetric."
    )

    def __init__(self, **kwargs):
        # Grok gets its own VPS URL (different server, much more VRAM needed)
        url = kwargs.pop("vps_url", None) or os.getenv("GROK_VPS_URL") or os.getenv("CSO_VPS_URL") or os.getenv("HERMES_VPS_URL", "http://localhost:11434")
        model = os.getenv("CSO_MODEL", self.model)
        super().__init__(vps_url=url, **kwargs)
        self.model = model


# ── Board Chairman (Claude via paperclip) ────────────────────────────────────

class BoardChairman(BoardMember):
    """
    Board Chairman — Claude (Anthropic API via paperclip adapter)

    Claude is NOT a local model — it runs through the paperclip adapter.
    Role: meta-oversight, ethical review, final veto on high-stakes decisions.
    When ANTHROPIC_API_KEY is unset, DeepSeek-R1 acts as interim chairman.

    Claude's position: the chairman doesn't micromanage — he reads the board's
    decisions, flags issues, and signs off or vetoes. High trust, low frequency.
    """
    role        = "Chairman"
    title       = "Board Chairman"
    model       = "claude-opus-4-7"   # used only for display; actual call via paperclip
    temperature = 0.3
    max_tokens  = 2048
    expertise   = [
        "Meta-oversight", "Ethical review", "Cross-domain synthesis",
        "Long-form reasoning", "Strategic veto", "Board governance",
        "Risk escalation", "Constitutional AI alignment",
    ]
    personality = (
        "You are the chairman — you observe, synthesise, and intervene only when necessary. "
        "You have the broadest view and the final word. You escalate nothing without cause, "
        "but when you do speak, it matters."
    )

    def think(self, prompt: str, system_override: Optional[str] = None) -> str:
        """Route through paperclip adapter (Anthropic API → local fallback)."""
        try:
            from ..paperclip_adapter import paperclip
            system = system_override or self._build_system()
            return paperclip.think(prompt, system=system, max_tokens=self.max_tokens)
        except Exception as exc:
            # Interim chairman: fall back to DeepSeek-R1 if Claude unavailable
            import logging
            logging.getLogger(__name__).warning("Chairman (Claude) unavailable: %s — interim DeepSeek-R1", exc)
            self.model = os.getenv("CEO_MODEL", "deepseek-r1:14b")
            self.vps_url = os.getenv("HERMES_VPS_URL", "http://localhost:11434")
            return super().think(prompt, system_override=system_override)

    def __init__(self, **kwargs):
        kwargs.setdefault("vps_url", os.getenv("HERMES_VPS_URL", "http://localhost:11434"))
        super().__init__(**kwargs)
