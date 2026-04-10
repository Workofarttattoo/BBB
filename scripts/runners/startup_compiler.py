#!/usr/bin/env python3
"""
BBB Startup Compiler
Implements the 'Elegant Swarm' vision: High-leverage insight -> Autonomous Startup.
"""

import asyncio
import logging
import argparse
from src.blank_business_builder.semantic_framework import semantic, on, send, ai
from src.blank_business_builder.autonomous_business import AutonomousBusinessOrchestrator, AgentRole

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("StartupCompiler")

class StartupCompiler:
    def __init__(self):
        self.orchestrator = None

    async def compile(self, insight: str):
        logger.info(f"🚀 Compiling startup from insight: {insight}")
        
        # 1. Analyze insight using semantic framework
        analysis_prompt = f"Analyze this business insight and derive the core semantic mission: {insight}"
        mission = await ai.generate(analysis_prompt, schema=semantic.Business.mission)
        logger.info(f"✨ Semantic Mission: {mission}")

        # 2. Deploy Orchestrator
        self.orchestrator = AutonomousBusinessOrchestrator(
            business_concept=mission,
            founder_name="Echo Creator"
        )
        
        await self.orchestrator.deploy_agents()
        
        # 3. Trigger initial strategy generation via semantic bus
        send(semantic.Startup.compile, {"insight": insight, "mission": mission})
        
        logger.info("✅ Startup compiled and agents deployed. Swarm is active.")

async def main():
    parser = argparse.ArgumentParser(description="BBB Startup Compiler")
    parser.add_argument("--insight", type=str, required=True, help="The high-leverage business insight")
    args = parser.parse_args()

    compiler = StartupCompiler()
    await compiler.compile(args.insight)

if __name__ == "__main__":
    asyncio.run(main())
