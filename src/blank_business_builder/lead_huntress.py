"""
Lead Huntress Agent
===================
Autonomous lead generation agent that scrapes the web for real contacts.

Supports manual (GUI) and agent-driven Apollo paths per enterprise policy.
"""

import json
import time
from typing import Dict, List, Optional

from .autonomous_tools import AutonomousTools
from .integrations import IntegrationFactory
from .enterprise_agent_policy import Capability, resolve_business_policy
from .approval_gates import ApprovalGateError, GateAction, gate_from_policy

# from .crm_automation import CRMAutomation  # Removed: CRM is injected via core_system

class LeadHuntress:
    def __init__(self, core_system, business_name: Optional[str] = None):
        self.core = core_system
        self.tools = AutonomousTools()
        self.apollo = IntegrationFactory.get_apollo_service()
        self.business_name = business_name or getattr(
            core_system, "business_concept", "default"
        )

    def _role_policy(self, role: str = "sales"):
        return resolve_business_policy(self.business_name).policy_for_role(role)

    def find_leads_manual(
        self,
        criteria: str,
        count: int = 5,
        *,
        approval_id: Optional[str] = None,
    ) -> List[Dict]:
        """
        Manual / GUI path: founder-triggered Apollo search (exploratory).
        Respects manual-only policy; bulk still requires approval.
        """
        policy = self._role_policy("sales")
        if policy.is_manual_only(Capability.APOLLO_SEARCH) or count > 25:
            if count > 25:
                gate_from_policy(
                    mode_requires_approval=True,
                    action=GateAction.APOLLO_BULK,
                    business_name=self.business_name,
                    role="sales",
                    approval_id=approval_id,
                    metadata={"criteria": criteria, "count": count},
                )
        return self._apollo_search(criteria, count)

    def find_leads_agent(
        self,
        criteria: str,
        count: int = 5,
        *,
        role: str = "sales",
        approval_id: Optional[str] = None,
    ) -> List[Dict]:
        """
        Agent path: only when policy allows agent execution for Apollo.
        """
        policy = self._role_policy(role)
        if policy.is_manual_only(Capability.APOLLO_SEARCH):
            raise ApprovalGateError(
                f"Apollo search is manual-only for {self.business_name} ({role}). "
                "Use find_leads_manual or the BBB Headhunter GUI."
            )
        if policy.requires_approval_before_side_effect(Capability.APOLLO_BULK):
            gate_from_policy(
                mode_requires_approval=True,
                action=GateAction.APOLLO_BULK,
                business_name=self.business_name,
                role=role,
                approval_id=approval_id,
                metadata={"criteria": criteria, "count": count},
            )
        return self._apollo_search(criteria, count)

    def find_leads(
        self,
        criteria: str,
        count: int = 5,
        *,
        mode: str = "manual",
        approval_id: Optional[str] = None,
    ) -> List[Dict]:
        """
        Find leads matching criteria with Apollo-first flow.

        mode: 'manual' (default, GUI/founder) or 'agent' (autonomous loop).
        """
        if mode == "agent":
            return self.find_leads_agent(
                criteria, count, approval_id=approval_id
            )
        return self.find_leads_manual(criteria, count, approval_id=approval_id)

    def _apollo_search(self, criteria: str, count: int) -> List[Dict]:
        print(f"🔎 HUNTRESS: Searching for '{criteria}'...")
        leads = []
        try:
            search = self.apollo.search_people(q_keywords=criteria, per_page=count)
            people = search.get("people") or search.get("contacts") or []

            for person in people[:count]:
                enrich = {}
                try:
                    enrich = self.apollo.enrich_person(
                        email=person.get("email"),
                        linkedin_url=person.get("linkedin_url"),
                        first_name=person.get("first_name"),
                        last_name=person.get("last_name"),
                        company_name=(person.get("organization") or {}).get("name")
                        if isinstance(person.get("organization"), dict)
                        else person.get("organization_name"),
                    )
                except Exception:
                    enrich = {}

                enriched_person = enrich.get("person") if isinstance(enrich, dict) else None
                base = enriched_person if isinstance(enriched_person, dict) else person

                leads.append(
                    {
                        "source_title": f"{base.get('first_name', '')} {base.get('last_name', '')}".strip()
                        or base.get("name")
                        or "Unknown Contact",
                        "url": base.get("linkedin_url") or "",
                        "snippet": base.get("headline")
                        or base.get("title")
                        or f"{base.get('organization_name') or ''}".strip(),
                        "status": "raw",
                        "source": "apollo",
                        "email": base.get("email"),
                        "phone": base.get("phone") or base.get("phone_number"),
                        "company": base.get("organization_name")
                        or (base.get("organization") or {}).get("name")
                        if isinstance(base.get("organization"), dict)
                        else base.get("company"),
                        "first_name": base.get("first_name"),
                        "last_name": base.get("last_name"),
                    }
                )
        except Exception as exc:
            print(f"[WARN] HUNTRESS: Apollo unavailable, falling back to scrape flow ({exc}).")
            leads = self._find_leads_via_scrape(criteria, count)

        print(f"✅ HUNTRESS: Found {len(leads)} raw leads.")
        return leads

    def _find_leads_via_scrape(self, criteria: str, count: int = 5) -> List[Dict]:
        """Fallback search path when Apollo is unavailable."""
        query = (
            f"{criteria} contact email site:linkedin.com "
            "OR site:crunchbase.com OR site:company_website"
        )
        results = self.tools.web_search(query, max_results=count * 3)

        leads = []
        for r in results:
            if len(leads) >= count:
                break

            title = r.get("title", "")
            body = r.get("body", "")
            href = r.get("href", "")

            if "contact" in body.lower() or "email" in body.lower():
                lead = {
                    "source_title": title,
                    "url": href,
                    "snippet": body,
                    "status": "raw",
                    "source": "scrape",
                }
                leads.append(lead)
        return leads

    def ingest_leads_to_crm(
        self,
        leads: List[Dict],
        *,
        role: str = "sales",
        approval_id: Optional[str] = None,
    ) -> int:
        """CRM ingest gated by lead_ingest approval policy."""
        policy = self._role_policy(role)
        gate_from_policy(
            mode_requires_approval=policy.requires_approval_before_side_effect(
                Capability.LEAD_INGEST
            ),
            action=GateAction.LEAD_INGEST,
            business_name=self.business_name,
            role=role,
            approval_id=approval_id,
            metadata={"lead_count": len(leads)},
            force_manual=policy.is_manual_only(Capability.LEAD_INGEST),
        )
        self.verify_and_add_to_crm(leads)
        return len(leads)

    def verify_and_add_to_crm(self, leads: List[Dict]):
        """
        Pass raw leads to the CRM/LLM for processing and adding to database.
        """
        if not self.core.llm_engine:
            print("[WARN] HUNTRESS: No LLM engine to parse leads.")
            return

        for lead in leads:
            prompt = f"""
            Extract structured lead info from this search result:
            Title: {lead['source_title']}
            URL: {lead['url']}
            Snippet: {lead['snippet']}
            
            Return JSON with fields: name, company, role, email (if found, else null), relevance_score (0-10).
            If not relevant, return {{ "relevance_score": 0 }}.
            """
            
            try:
                response = self.core.llm_engine.generate_response(prompt)
                json_str = response.strip()
                if "{" in json_str:
                    json_str = json_str[json_str.find("{"):json_str.rfind("}")+1]
                    data = json.loads(json_str)
                    
                    if data.get('relevance_score', 0) > 6:
                        self.core.modules['crm'].add_lead(data)
                        print(f"✅ HUNTRESS: Added lead {data.get('name', 'Unknown')} from {data.get('company', 'Unknown')}")
            except Exception as e:
                print(f"[ERROR] Lead parsing failed: {e}")
