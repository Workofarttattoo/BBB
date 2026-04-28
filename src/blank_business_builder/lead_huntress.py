"""
Lead Huntress Agent
===================
Autonomous lead generation agent that scrapes the web for real contacts.
"""

import json
import time
from typing import List, Dict
from .autonomous_tools import AutonomousTools
from .integrations import IntegrationFactory
# from .crm_automation import CRMAutomation  # Removed: CRM is injected via core_system

class LeadHuntress:
    def __init__(self, core_system):
        self.core = core_system
        self.tools = AutonomousTools()
        self.apollo = IntegrationFactory.get_apollo_service()

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

    def find_leads(self, criteria: str, count: int = 5) -> List[Dict]:
        """
        Find leads matching criteria with Apollo-first flow.
        Step 1: Apollo search.
        Step 2: Apollo enrich.
        Step 3: Fallback to scrape if provider is unavailable.
        """
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
                    # Search succeeds even when enrichment fails for specific records.
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
                # Parse JSON (basic cleanup)
                json_str = response.strip()
                if "{" in json_str:
                    json_str = json_str[json_str.find("{"):json_str.rfind("}")+1]
                    data = json.loads(json_str)
                    
                    if data.get('relevance_score', 0) > 6:
                        self.core.modules['crm'].add_lead(data)
                        print(f"✅ HUNTRESS: Added lead {data.get('name', 'Unknown')} from {data.get('company', 'Unknown')}")
            except Exception as e:
                print(f"[ERROR] Lead parsing failed: {e}")

