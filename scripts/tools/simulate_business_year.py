#!/usr/bin/env python3
"""
BBB Annual Business Simulator
Fast-forwards through a year of autonomous operations to verify system behavior.
"""

import asyncio
import logging
import random
from datetime import datetime, timedelta
from startup_compiler import StartupCompiler
from src.blank_business_builder.autonomous_business import TaskStatus, AgentRole
from src.blank_business_builder.semantic_framework import semantic, send

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("YearSimulator")

class YearSimulator:
    def __init__(self, insight: str):
        self.insight = insight
        self.compiler = StartupCompiler()
        self.start_date = datetime.now()
        self.current_date = self.start_date
        self.logs = []

    async def run(self):
        logger.info(f"📅 Starting 1-Year Fast-Forward for: {self.insight}")
        
        # 1. Compile the startup
        await self.compiler.compile(self.insight)
        orch = self.compiler.orchestrator
        
        # 2. Simulate 365 days in chunks
        for day in range(1, 366):
            self.current_date += timedelta(days=1)
            
            # Simulate random business events
            num_clients = random.randint(0, 5)
            for _ in range(num_clients):
                client_id = f"client_{day}_{random.randint(1000, 9999)}"
                send(semantic.Client.onboarded, {"client_id": client_id, "date": self.current_date.isoformat()})
                orch.metrics.customer_count += 1
            
            # Simulate autonomous agent activity for the day
            # In a real run, the agents would pick up tasks from the queue.
            # Here we simulate the OODA loops and outputs.
            
            if day % 7 == 0: # Weekly marketing push
                logger.info(f"Day {day}: Autonomous Marketing Blast executed.")
                orch.metrics.leads_generated += random.randint(10, 50)
                
            if day % 30 == 0: # Monthly financial review
                revenue_gain = orch.metrics.customer_count * random.uniform(50, 200)
                orch.metrics.total_revenue += revenue_gain
                logger.info(f"Day {day}: Monthly Revenue Update: +${revenue_gain:.2f} (Total: ${orch.metrics.total_revenue:.2f})")

            # Simulate agent task completions
            for task in orch.task_queue:
                if task.status == TaskStatus.PENDING and random.random() > 0.3:
                    task.status = TaskStatus.COMPLETED
                    task.completed_at = self.current_date
                    orch.metrics.tasks_completed += 1
                    
            # Log periodic status
            if day % 90 == 0:
                logger.info(f"--- Quarter {day//90} Report ---")
                logger.info(f"Revenue: ${orch.metrics.total_revenue:.2f} | Clients: {orch.metrics.customer_count} | Tasks: {orch.metrics.tasks_completed}")

        logger.info("🏁 1-Year Simulation Complete.")
        self.generate_report(orch)

    def generate_report(self, orch):
        report = f"""
# Annual Autonomy Report
**Insight**: {self.insight}
**Duration**: 365 Days (Simulated)

## Key Metrics
- **Total Revenue**: ${orch.metrics.total_revenue:,.2f}
- **Client Base**: {orch.metrics.customer_count}
- **Tasks Autonomously Executed**: {orch.metrics.tasks_completed}
- **Lead Generation**: {orch.metrics.leads_generated}

## Activity Summary
- **Calls/Outreach**: {orch.metrics.leads_generated * 1.5:.0f} simulated interactions
- **Email Campaigns**: {int(365/7)} autonomous blasts
- **Financial Reviews**: 12 semantic audits
"""
        with open("simulation_report.md", "w") as f:
            f.write(report)
        logger.info("📄 Simulation report generated: simulation_report.md")

if __name__ == "__main__":
    sim = YearSimulator("AI-Powered Subscription Box for Artisanal Woodworking Tools")
    asyncio.run(sim.run())
