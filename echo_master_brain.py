"""
ECH0 Master Brain - Autonomous Business Reasoning Engine
========================================================
Integrates Hive Mind, Tool Use, and Specialized Agents into a continuous cognitive loop.
"""

import time
import threading
import sys
import os
from typing import Dict, List

# Add src to path to allow importing business libraries
# Use insert(0) to prioritize local 'src' over interpreted/environment paths
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
sys.path.insert(0, src_path)

print(f"DEBUG: sys.path[0] = {sys.path[0]}")

# Imports
try:
    from blank_business_builder.hive_mind_coordinator import HiveMindCoordinator, AgentType, HiveMessage, DecisionPriority
    from blank_business_builder.autonomous_tools import AutonomousTools
    from blank_business_builder.lead_huntress import LeadHuntress
    from blank_business_builder.autonomous_developer import AutonomousDeveloper
    from blank_business_builder.sales_engineer import SalesEngineer
    from blank_business_builder.data_broker import DataBroker
    from ech0_llm_engine import ECH0LLMEngine
    # Mock CRM removed from imports, defined locally below
except ImportError as e:
    print(f"CRITICAL IMPORT ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

class EchoMasterBrain:
    def __init__(self):
        print("🧠 ECH0 MASTER BRAIN INITIALIZING...")
        
        # 1. Initialize Components
        self.llm_engine = ECH0LLMEngine()
        self.hive = HiveMindCoordinator()
        self.tools = AutonomousTools()
        
        # 2. Initialize Agents
        self.huntress = LeadHuntress(self)
        self.developer = AutonomousDeveloper(self)
        self.sales = SalesEngineer(self)
        self.broker = DataBroker(self)
        
        # Mock CRM module structure for now if not fully integrated
        self.modules = {
            'crm': MockCRM() 
        }
        
        self.running = False
        
    def start(self):
        """Start the continuous reasoning loop."""
        self.running = True
        print("\n🚀 ECH0 RUNNING - 24/7 AUTONOMY ENGAGED")
        
        # Start the loop in a thread
        thread = threading.Thread(target=self._reasoning_loop)
        thread.start()
        
    def stop(self):
        self.running = False
        print("🛑 ECH0 STOPPING...")

    def _reasoning_loop(self):
        """
        The Core Cognitive Loop:
        1. Perceive (Check messages, emails, system state)
        2. Plan (Hive Mind Strategy)
        3. Act (Dispatch tasks to agents)
        4. Learn (Update knowledge base)
        """
        while self.running:
            try:
                print("\n--- 🧠 ECH0 THINKING CYCLE ---")
                
                # 1. Check Hive Mind Status
                status = self.hive.get_hive_status()
                print(f"Status: {status['active_agents']} agents active.")
                
                # 2. Decide on next action (Simulated high-level reasoning)
                # In a real system, the LLM would analyze the state and choose.
                # Here we cycle through key priorities.
                
                # Priority 1: Data Brokerage (Hunt & Verify for Resale)
                print("🧠 Brain: Hunting for high-value leads to package...")
                raw_leads = self.huntress.find_leads("Generative AI B2B clients", count=2)
                semantic_leads = self._process_raw_leads(raw_leads)
                
                if semantic_leads:
                    # Pipeline A: Resale
                    self.broker.verify_and_package(semantic_leads)
                    self.broker.generate_manifest()
                    
                    # Pipeline B: Direct Sales (TheGAVL / ChatterTech)
                    # We can reuse the same leads if they fit, or hunt specifically
                    print("🧠 Brain: Checking TheGAVL specific targets...")
                    # self.sales.process_leads(semantic_leads) # Optional: Sell to them directly too
                
                # Priority 2: Business Specific Tasks
                # The GAVL (Legal Tech)
                # self.run_gavl_tasks()
                
                # ChatterTech (AI Support)
                # self.run_chattertech_tasks()

                # Priority 3: Maintenance
                print("💤 Brain Loop: Sleeping for 60s to respect API rate limits...")
                time.sleep(60) # Thinking time
                
            except Exception as e:
                print(f"[CRITICAL ERROR] Brain Loop Exception: {e}")
                time.sleep(30)
    
    def _process_raw_leads(self, raw_leads):
        from blank_business_builder.semantic_framework import Lead, Person, Organization
        semantic_leads = []
        for raw in raw_leads:
            lead = Lead()
            lead.source = raw.get('url', 'Search')
            lead.organization = Organization(name=raw.get('source_title', 'Unknown Corp'), industry="Tech")
            lead.person = Person(name="Contact", role="Decision Maker", email="contact@example.com") # Mock email for demo
            semantic_leads.append(lead)
        return semantic_leads

class MockCRM:
    def add_lead(self, data):
        print(f"   [CRM] Added lead: {data}")

if __name__ == "__main__":
    brain = EchoMasterBrain()
    brain.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        brain.stop()
