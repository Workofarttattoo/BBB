"""
Materials Prediction & Legal Tech Business (TheGavl Integration)
================================================================

A unified business interface for:
1. Materials Science Predictions (for Students/Enterprises)
2. Legal Predictions (TheGavl)
3. Software Licensing
4. MCP Server Integration

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

import asyncio
import logging
import json
import random
from datetime import datetime
from typing import Dict, Any, Optional, List

# Adjust path for direct execution if needed
import sys
import os

# Add src to path if running directly
if __name__ == "__main__":
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

try:
    from blank_business_builder.expert_system import (
        MultiDomainExpertSystem,
        ExpertQuery,
        ExpertDomain,
        KnowledgeDocument,
        CHROMADB_AVAILABLE
    )
except ImportError:
    # Fallback for when running from different contexts
    from src.blank_business_builder.expert_system import (
        MultiDomainExpertSystem,
        ExpertQuery,
        ExpertDomain,
        KnowledgeDocument,
        CHROMADB_AVAILABLE
    )

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("MaterialsBusiness")


class MaterialsBusiness:
    """
    Main business logic for Materials Data & Legal Predictions.
    """

    def __init__(self):
        logger.info("Initializing Materials & Legal Business System...")
        self.expert_system = MultiDomainExpertSystem(use_chromadb=CHROMADB_AVAILABLE)
        self.active_licenses: Dict[str, Dict] = {}
        self.mcp_server_running = False

        # Pre-load some knowledge for demo purposes
        self._load_initial_knowledge()

    def _load_initial_knowledge(self):
        """Load initial knowledge into the expert system."""
        docs = [
            # Materials Science Data
            KnowledgeDocument(
                doc_id="mat_001",
                content="Graphene is a single layer of carbon atoms arranged in a 2D honeycomb lattice. It has high thermal conductivity and mechanical strength.",
                domain=ExpertDomain.MATERIALS_SCIENCE,
                metadata={"source": "research_paper_001", "type": "material_property"}
            ),
            KnowledgeDocument(
                doc_id="mat_002",
                content="Perovskite solar cells have shown rapid increase in power conversion efficiency, reaching over 25%. Stability remains a challenge.",
                domain=ExpertDomain.MATERIALS_SCIENCE,
                metadata={"source": "energy_journal_2024", "type": "energy_material"}
            ),
            # Legal Data (TheGavl)
            KnowledgeDocument(
                doc_id="legal_001",
                content="In 'Smith v. Jones', the court ruled that digital assets are considered personal property for the purpose of inheritance.",
                domain=ExpertDomain.LEGAL,
                metadata={"case": "Smith v. Jones", "year": 2023, "jurisdiction": "Federal"}
            ),
            KnowledgeDocument(
                doc_id="legal_002",
                content="Smart contracts are legally binding if they meet the standard requirements of offer, acceptance, and consideration.",
                domain=ExpertDomain.LEGAL,
                metadata={"topic": "smart_contracts", "status": "emerging_precedent"}
            )
        ]
        self.expert_system.add_knowledge(docs)
        logger.info(f"Loaded {len(docs)} initial knowledge documents.")

    async def predict_materials(self, query_text: str, client_type: str = "student") -> Dict[str, Any]:
        """
        Generate materials science predictions.

        Args:
            query_text: The question or prediction request.
            client_type: 'student' or 'enterprise' (affects detail/pricing).
        """
        logger.info(f"Processing materials prediction for {client_type}: {query_text}")

        query = ExpertQuery(
            query=query_text,
            domain=ExpertDomain.MATERIALS_SCIENCE,
            context={"client_type": client_type}
        )

        response = await self.expert_system.query(query)

        # Enterprise clients get more detailed reasoning
        if client_type == "enterprise":
            detailed_analysis = f"ENTERPRISE ANALYSIS:\n{response.reasoning}\nConfidence Interval: {response.confidence:.3f}"
        else:
            detailed_analysis = "Upgrade to Enterprise for deep analysis."

        return {
            "prediction": response.answer,
            "confidence": float(response.confidence),
            "analysis": detailed_analysis,
            "sources": [s['content'][:50] + "..." for s in response.sources],
            "timestamp": datetime.now().isoformat()
        }

    async def predict_legal(self, query_text: str) -> Dict[str, Any]:
        """
        Generate legal predictions via TheGavl integration.
        """
        logger.info(f"Processing legal prediction (TheGavl): {query_text}")

        query = ExpertQuery(
            query=query_text,
            domain=ExpertDomain.LEGAL
        )

        response = await self.expert_system.query(query)

        return {
            "legal_opinion": response.answer,
            "confidence_score": float(response.confidence),
            "precedents_cited": len(response.sources),
            "disclaimer": "Not legal advice. For informational purposes only.",
            "timestamp": datetime.now().isoformat()
        }

    def license_software(self, client_name: str, license_type: str = "enterprise") -> Dict[str, Any]:
        """
        Issue a license for the software.
        """
        logger.info(f"Issuing {license_type} license to {client_name}")

        license_key = f"LIC-{license_type.upper()}-{random.randint(1000, 9999)}-{datetime.now().strftime('%Y%m%d')}"

        license_data = {
            "client_name": client_name,
            "license_type": license_type,
            "key": license_key,
            "issued_at": datetime.now().isoformat(),
            "status": "active"
        }

        self.active_licenses[client_name] = license_data

        return {
            "status": "success",
            "message": f"License issued to {client_name}",
            "license_details": license_data
        }

    async def start_mcp_server(self, port: int = 8080):
        """
        Start the MCP (Model Context Protocol) Server.
        """
        if self.mcp_server_running:
            logger.warning("MCP Server is already running.")
            return

        logger.info(f"Starting MCP Server on port {port}...")
        self.mcp_server_running = True

        # Simulate server startup
        await asyncio.sleep(1)
        logger.info("MCP Server is LISTENING. Ready to serve context to LLMs.")

        return {
            "status": "running",
            "port": port,
            "protocol": "MCP v1.0",
            "endpoints": ["/context", "/resources", "/prompts"]
        }


async def run_demo():
    """Run a full demonstration of the business capabilities."""
    business = MaterialsBusiness()

    print("\n" + "="*60)
    print("🧪 MATERIALS DATA & LEGAL PREDICTIONS BUSINESS DEMO")
    print("="*60)

    # 1. Materials Prediction (Student)
    print("\n--- 1. Materials Prediction (Student Tier) ---")
    student_res = await business.predict_materials("What are the properties of Graphene?", client_type="student")
    print(json.dumps(student_res, indent=2))

    # 2. Materials Prediction (Enterprise)
    print("\n--- 2. Materials Prediction (Enterprise Tier) ---")
    enterprise_res = await business.predict_materials("Analyze stability of Perovskite cells.", client_type="enterprise")
    print(json.dumps(enterprise_res, indent=2))

    # 3. Legal Prediction (TheGavl)
    print("\n--- 3. Legal Prediction (TheGavl Integration) ---")
    legal_res = await business.predict_legal("Are smart contracts legally binding?")
    print(json.dumps(legal_res, indent=2))

    # 4. Licensing
    print("\n--- 4. Software Licensing ---")
    license_res = business.license_software("Acme Corp", "enterprise")
    print(json.dumps(license_res, indent=2))

    # 5. MCP Server
    print("\n--- 5. MCP Server Integration ---")
    mcp_res = await business.start_mcp_server()
    print(json.dumps(mcp_res, indent=2))

    print("\n" + "="*60)
    print("✅ DEMO COMPLETE")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(run_demo())
