"""
Enterprise agent automation policy — capability matrix per role and integration.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class AutomationMode(str, Enum):
    """How an agent may use a capability."""

    AUTO = "auto"
    DRAFT = "draft"
    MANUAL = "manual"
    APPROVAL_REQUIRED = "approval_required"


class Capability(str, Enum):
    """Cross-cutting capabilities agents may invoke."""

    APOLLO_SEARCH = "apollo_search"
    APOLLO_BULK = "apollo_bulk"
    LEAD_INGEST = "lead_ingest"
    EMAIL_SEND = "email_send"
    EMAIL_CAMPAIGN = "email_campaign"
    PAYMENT_CHARGE = "payment_charge"
    SOCIAL_POST = "social_post"
    MARKET_RESEARCH = "market_research"
    CONTENT_GENERATE = "content_generate"
    STRATEGY_ECHO = "strategy_echo"


# Default enterprise matrix: irreversible / outbound actions need approval or manual run.
DEFAULT_CAPABILITY_MATRIX: Dict[str, Dict[str, str]] = {
    "researcher": {
        Capability.MARKET_RESEARCH.value: AutomationMode.AUTO.value,
        Capability.APOLLO_SEARCH.value: AutomationMode.MANUAL.value,
        Capability.APOLLO_BULK.value: AutomationMode.APPROVAL_REQUIRED.value,
        Capability.STRATEGY_ECHO.value: AutomationMode.DRAFT.value,
    },
    "deep_researcher": {
        Capability.MARKET_RESEARCH.value: AutomationMode.AUTO.value,
        Capability.APOLLO_SEARCH.value: AutomationMode.MANUAL.value,
        Capability.STRATEGY_ECHO.value: AutomationMode.DRAFT.value,
    },
    "osint_specialist": {
        Capability.MARKET_RESEARCH.value: AutomationMode.AUTO.value,
        Capability.APOLLO_SEARCH.value: AutomationMode.MANUAL.value,
        Capability.APOLLO_BULK.value: AutomationMode.APPROVAL_REQUIRED.value,
    },
    "marketer": {
        Capability.CONTENT_GENERATE.value: AutomationMode.AUTO.value,
        Capability.EMAIL_SEND.value: AutomationMode.DRAFT.value,
        Capability.EMAIL_CAMPAIGN.value: AutomationMode.APPROVAL_REQUIRED.value,
        Capability.SOCIAL_POST.value: AutomationMode.DRAFT.value,
        Capability.APOLLO_SEARCH.value: AutomationMode.MANUAL.value,
    },
    "sales": {
        Capability.CONTENT_GENERATE.value: AutomationMode.DRAFT.value,
        Capability.EMAIL_SEND.value: AutomationMode.DRAFT.value,
        Capability.EMAIL_CAMPAIGN.value: AutomationMode.APPROVAL_REQUIRED.value,
        Capability.APOLLO_SEARCH.value: AutomationMode.MANUAL.value,
        Capability.LEAD_INGEST.value: AutomationMode.APPROVAL_REQUIRED.value,
        Capability.APOLLO_BULK.value: AutomationMode.APPROVAL_REQUIRED.value,
    },
    "fulfillment": {
        Capability.CONTENT_GENERATE.value: AutomationMode.AUTO.value,
    },
    "support": {
        Capability.CONTENT_GENERATE.value: AutomationMode.DRAFT.value,
        Capability.EMAIL_SEND.value: AutomationMode.DRAFT.value,
    },
    "finance": {
        Capability.PAYMENT_CHARGE.value: AutomationMode.APPROVAL_REQUIRED.value,
        Capability.MARKET_RESEARCH.value: AutomationMode.AUTO.value,
    },
    "hr": {
        Capability.STRATEGY_ECHO.value: AutomationMode.DRAFT.value,
    },
    "meta_manager": {
        Capability.STRATEGY_ECHO.value: AutomationMode.DRAFT.value,
        Capability.LEAD_INGEST.value: AutomationMode.APPROVAL_REQUIRED.value,
    },
    "executive": {
        Capability.STRATEGY_ECHO.value: AutomationMode.DRAFT.value,
        Capability.APOLLO_SEARCH.value: AutomationMode.MANUAL.value,
        Capability.PAYMENT_CHARGE.value: AutomationMode.APPROVAL_REQUIRED.value,
    },
    "creative_director": {
        Capability.CONTENT_GENERATE.value: AutomationMode.AUTO.value,
        Capability.SOCIAL_POST.value: AutomationMode.DRAFT.value,
    },
    "saas_builder": {
        Capability.CONTENT_GENERATE.value: AutomationMode.AUTO.value,
        Capability.STRATEGY_ECHO.value: AutomationMode.DRAFT.value,
    },
    "content_creator": {
        Capability.CONTENT_GENERATE.value: AutomationMode.AUTO.value,
        Capability.SOCIAL_POST.value: AutomationMode.DRAFT.value,
    },
    "community_manager": {
        Capability.SOCIAL_POST.value: AutomationMode.DRAFT.value,
        Capability.CONTENT_GENERATE.value: AutomationMode.AUTO.value,
    },
    "crypto_miner": {Capability.MARKET_RESEARCH.value: AutomationMode.AUTO.value},
    "nft_trader": {Capability.MARKET_RESEARCH.value: AutomationMode.AUTO.value},
    "arbitrage_bot": {Capability.MARKET_RESEARCH.value: AutomationMode.AUTO.value},
    "dropshipper": {Capability.CONTENT_GENERATE.value: AutomationMode.AUTO.value},
    "quantum_trader": {Capability.PAYMENT_CHARGE.value: AutomationMode.APPROVAL_REQUIRED.value},
    "tax_preparer": {Capability.CONTENT_GENERATE.value: AutomationMode.DRAFT.value},
    "survey_bot": {Capability.MARKET_RESEARCH.value: AutomationMode.AUTO.value},
    "tester_bot": {Capability.CONTENT_GENERATE.value: AutomationMode.AUTO.value},
}

GOVERNANCE_ROLES = ("executive", "hr", "meta_manager")


@dataclass
class RoleCapabilityPolicy:
    """Resolved policy for one agent role."""

    role: str
    capabilities: Dict[str, AutomationMode] = field(default_factory=dict)

    def mode_for(self, capability: Capability | str) -> AutomationMode:
        key = capability.value if isinstance(capability, Capability) else str(capability)
        raw = self.capabilities.get(key, AutomationMode.MANUAL.value)
        try:
            return AutomationMode(raw)
        except ValueError:
            return AutomationMode.MANUAL

    def allows_agent_execution(self, capability: Capability | str) -> bool:
        return self.mode_for(capability) in (
            AutomationMode.AUTO,
            AutomationMode.DRAFT,
            AutomationMode.APPROVAL_REQUIRED,
        )

    def requires_approval_before_side_effect(self, capability: Capability | str) -> bool:
        return self.mode_for(capability) == AutomationMode.APPROVAL_REQUIRED

    def is_manual_only(self, capability: Capability | str) -> bool:
        return self.mode_for(capability) == AutomationMode.MANUAL


@dataclass
class BusinessAutomationPolicy:
    """Policy bundle for a staffed business."""

    business_name: str
    roles: List[str]
    role_policies: Dict[str, RoleCapabilityPolicy] = field(default_factory=dict)
    capability_overrides: Dict[str, Dict[str, str]] = field(default_factory=dict)

    @classmethod
    def for_business(
        cls,
        business_name: str,
        required_roles: List[str],
        capability_overrides: Optional[Dict[str, Dict[str, str]]] = None,
    ) -> "BusinessAutomationPolicy":
        roles = list(dict.fromkeys(required_roles))
        for gov in GOVERNANCE_ROLES:
            if gov not in roles:
                roles.append(gov)

        overrides = capability_overrides or {}
        role_policies: Dict[str, RoleCapabilityPolicy] = {}
        for role in roles:
            base = dict(DEFAULT_CAPABILITY_MATRIX.get(role, {}))
            base.update(overrides.get(role, {}))
            caps = {}
            for k, v in base.items():
                try:
                    caps[k] = AutomationMode(v)
                except ValueError:
                    caps[k] = AutomationMode.MANUAL
            role_policies[role] = RoleCapabilityPolicy(role=role, capabilities=caps)

        return cls(
            business_name=business_name,
            roles=roles,
            role_policies=role_policies,
            capability_overrides=overrides,
        )

    def policy_for_role(self, role: str) -> RoleCapabilityPolicy:
        return self.role_policies.get(
            role,
            RoleCapabilityPolicy(role=role, capabilities={}),
        )

    def to_dict(self) -> Dict:
        return {
            "business_name": self.business_name,
            "roles": self.roles,
            "role_policies": {
                r: {k: v.value for k, v in p.capabilities.items()}
                for r, p in self.role_policies.items()
            },
        }


def resolve_business_policy(business_name: str) -> BusinessAutomationPolicy:
    """Build policy from business_models_2025 template when available."""
    from .business_data import default_ideas

    matching = next((i for i in default_ideas() if i.name == business_name), None)
    if matching and getattr(matching, "required_roles", None):
        overrides = getattr(matching, "capability_overrides", None)
        return BusinessAutomationPolicy.for_business(
            business_name,
            list(matching.required_roles),
            capability_overrides=overrides,
        )
    return BusinessAutomationPolicy.for_business(
        business_name,
        ["marketer", "sales", "support", "finance", "executive"],
    )
