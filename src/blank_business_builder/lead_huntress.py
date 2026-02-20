"""
Lead Huntress Agent
===================
Autonomous lead generation agent that scrapes the web for real contacts.
"""

import json
import time
from typing import List, Dict
from .autonomous_tools import AutonomousTools
# from .crm_automation import CRMAutomation  # Removed: CRM is injected via core_system

class LeadHuntress:
    def __init__(self, core_system):
        self.core = core_system
        self.tools = AutonomousTools()

    def find_leads(self, criteria: str, count: int = 5) -> List[Dict]:
        """
        Find leads matching the criteria using web search.
        Step 1: Search for companies/people.
        Step 2: Extract contact info (simulated extraction from search snippets for now).
        Step 3: Verify (simple heuristic).
        """
        print(f"🔎 HUNTRESS: Searching for '{criteria}'...")
        
        # Search query optimization
        query = f"{criteria} contact email site:linkedin.com OR site:crunchbase.com OR site:company_website"
        results = self.tools.web_search(query, max_results=count * 3)
        
        leads = []
        for r in results:
            if len(leads) >= count:
                break
                
            title = r.get('title', '')
            body = r.get('body', '')
            href = r.get('href', '')
            
            # Simple extraction heuristic (improved with LLM later)
            if "contact" in body.lower() or "email" in body.lower():
                lead = {
                    "source_title": title,
                    "url": href,
                    "snippet": body,
                    "status": "raw"
                }
                leads.append(lead)
                
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

