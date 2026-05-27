"""
Catalog API — all business templates, agents, and skills in one place.
Paperclip (Claude) powers the Company Composer to mix & match unique companies.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os

router = APIRouter(prefix="/api/catalog", tags=["catalog"])

# ---------------------------------------------------------------------------
# Agent Catalog — 23 agents, every skill listed
# ---------------------------------------------------------------------------
AGENTS = [
    # ── Core Operational Roles ──────────────────────────────────────────────
    {"id": "researcher", "name": "Researcher", "tier": "core", "color": "blue", "icon": "fa-search",
     "description": "Market research, competitive analysis, trend monitoring",
     "skills": ["Market Analysis", "Competitor Tracking", "Trend Monitoring", "Data Synthesis", "Report Generation", "Industry Benchmarking"]},
    {"id": "marketer", "name": "Marketer", "tier": "core", "color": "purple", "icon": "fa-bullhorn",
     "description": "Content creation, SEO, multi-channel advertising",
     "skills": ["Blog Content", "Social Media Posts", "Email Campaigns", "Google Ads", "SEO Optimization", "A/B Testing"]},
    {"id": "sales", "name": "Sales Agent", "tier": "core", "color": "green", "icon": "fa-handshake",
     "description": "Lead generation, cold outreach, and deal closing",
     "skills": ["Lead Generation", "Cold Email", "Sales Calls via Bland AI", "Proposal Writing", "Deal Closing", "CRM Management", "Rebuttal Handling"]},
    {"id": "fulfillment", "name": "Fulfillment Agent", "tier": "core", "color": "orange", "icon": "fa-box",
     "description": "Service and product delivery orchestration",
     "skills": ["Order Processing", "Delivery Coordination", "Quality Control", "Vendor Management", "Inventory Tracking", "SLA Monitoring"]},
    {"id": "support", "name": "Support Agent", "tier": "core", "color": "teal", "icon": "fa-headset",
     "description": "24/7 customer service and retention automation",
     "skills": ["Customer Chat", "Ticket Resolution", "Refund Processing", "Retention Campaigns", "FAQ Automation", "Escalation Routing"]},
    {"id": "finance", "name": "Finance Agent", "tier": "core", "color": "emerald", "icon": "fa-dollar-sign",
     "description": "Revenue tracking, invoicing, financial reporting",
     "skills": ["Revenue Tracking", "Invoicing", "Expense Monitoring", "Financial Reporting", "Stripe Integration", "Cash Flow Forecasting"]},
    {"id": "hr", "name": "HR Agent", "tier": "core", "color": "pink", "icon": "fa-users",
     "description": "Resource allocation and budget management",
     "skills": ["Resource Monitoring", "Budget Allocation", "API Cost Tracking", "Capacity Planning", "Agent Onboarding", "Performance Reviews"]},
    # ── Management Roles ─────────────────────────────────────────────────────
    {"id": "meta_manager", "name": "Meta Manager", "tier": "management", "color": "indigo", "icon": "fa-sitemap",
     "description": "Supervises worker agents, detects and resolves bottlenecks",
     "skills": ["Sub-Agent Supervision", "Bottleneck Detection", "Task Reassignment", "Performance Reporting", "Workflow Optimization", "Priority Queuing"]},
    {"id": "executive", "name": "Executive Agent", "tier": "management", "color": "red", "icon": "fa-chess-king",
     "description": "Top-level strategy, goal-setting, pivot decisions",
     "skills": ["Quarterly Goal Setting", "Strategic Pivots", "Business Health Analysis", "OKR Tracking", "Board Reporting", "Risk Management"]},
    {"id": "orchestrator", "name": "Orchestrator", "tier": "management", "color": "gray", "icon": "fa-network-wired",
     "description": "Coordinates all agents across the business via HiveMind",
     "skills": ["Agent Coordination", "Task Distribution", "Priority Management", "Inter-Agent Messaging", "Consensus Building", "Hive Mind Sync"]},
    # ── Specialist Roles ─────────────────────────────────────────────────────
    {"id": "deep_researcher", "name": "Deep Researcher", "tier": "specialist", "color": "cyan", "icon": "fa-microscope",
     "description": "Academic research, cross-reference verification, synthesis",
     "skills": ["Academic Research", "Cross-Reference Verification", "White Paper Synthesis", "Literature Reviews", "Citation Management", "Patent Analysis"]},
    {"id": "osint_specialist", "name": "OSINT Specialist", "tier": "specialist", "color": "yellow", "icon": "fa-eye",
     "description": "Competitor intelligence and market surveillance",
     "skills": ["Social Media Monitoring", "Public Filings Analysis", "Competitor Intelligence", "Vulnerability ID", "Dark Web Monitoring", "Brand Mention Tracking"]},
    {"id": "creative_director", "name": "Creative Director", "tier": "specialist", "color": "fuchsia", "icon": "fa-palette",
     "description": "Design, A/V production, music, brand consistency",
     "skills": ["Text-to-Image", "Text-to-Video", "Voiceovers", "Music Generation", "Brand Consistency", "Ad Creatives", "Thumbnail Design"]},
    # ── Specialized 2025 Roles ───────────────────────────────────────────────
    {"id": "crypto_miner", "name": "Crypto Miner", "tier": "specialized", "color": "amber", "icon": "fa-coins",
     "description": "Hashrate optimization and coin switching automation",
     "skills": ["Hashrate Optimization", "Coin Switching", "Pool Selection", "Profitability Calculation", "Wallet Management", "Energy Cost Monitoring"]},
    {"id": "nft_trader", "name": "NFT Trader", "tier": "specialized", "color": "violet", "icon": "fa-image",
     "description": "AI art generation, smart contracts, NFT trading",
     "skills": ["AI Art Generation", "Smart Contract Deployment", "Marketplace Listing", "Floor Price Monitoring", "Rarity Analysis", "Collection Drops"]},
    {"id": "saas_builder", "name": "SaaS Builder", "tier": "specialized", "color": "sky", "icon": "fa-code",
     "description": "Identifies market gaps and deploys no-code SaaS tools",
     "skills": ["Gap Analysis", "No-Code Development", "API Integration", "Subscription Setup", "User Onboarding", "Churn Reduction"]},
    {"id": "arbitrage_bot", "name": "Arbitrage Bot", "tier": "specialized", "color": "lime", "icon": "fa-exchange-alt",
     "description": "Retail price scanning and profit-maximizing resale",
     "skills": ["Price Scanning", "Profit Calculation", "Listing Automation", "Inventory Sourcing", "Repricing Logic", "Return Management"]},
    {"id": "content_creator", "name": "Content Creator", "tier": "specialized", "color": "rose", "icon": "fa-video",
     "description": "High-volume viral content generation for any platform",
     "skills": ["Viral Script Writing", "Video Generation", "Thumbnail Creation", "SEO Tagging", "Multi-Platform Distribution", "Trend Hijacking"]},
    {"id": "dropshipper", "name": "Dropshipper", "tier": "specialized", "color": "stone", "icon": "fa-truck",
     "description": "Product research, supplier management, and order fulfillment",
     "skills": ["Product Research", "Supplier Relations", "Order Routing", "Returns Management", "Shopify Integration", "Margin Optimization"]},
    {"id": "tax_preparer", "name": "Tax Preparer", "tier": "specialized", "color": "neutral", "icon": "fa-file-invoice-dollar",
     "description": "Automated tax preparation and e-filing at scale",
     "skills": ["Tax Document Collection", "Deduction Analysis", "Form Preparation", "E-Filing", "Audit Support", "Multi-State Compliance"]},
    {"id": "survey_bot", "name": "Survey Bot", "tier": "specialized", "color": "zinc", "icon": "fa-poll",
     "description": "Mass survey completion for passive income",
     "skills": ["Survey Discovery", "Auto-Completion", "Data Aggregation", "Insight Reports", "Panel Management", "Rewards Optimization"]},
    {"id": "tester_bot", "name": "Tester Bot", "tier": "specialized", "color": "slate", "icon": "fa-vial",
     "description": "Automated usability and A/B testing as a service",
     "skills": ["UI Testing", "A/B Test Setup", "Bug Reporting", "Regression Testing", "Heatmap Analysis", "Performance Benchmarking"]},
    {"id": "quantum_trader", "name": "Quantum Trader", "tier": "specialized", "color": "blue", "icon": "fa-atom",
     "description": "Quantum algorithm-based trading and portfolio optimization",
     "skills": ["Quantum Optimization", "Portfolio Rebalancing", "Risk Assessment", "Algo Trading", "Market Prediction", "Derivatives Analysis"]},
]

# ---------------------------------------------------------------------------
# Business Catalog — tiers 0–3 + legacy
# ---------------------------------------------------------------------------
BUSINESSES = [
    # Special Tier 6
    {"id": "quantum_trading", "name": "Quantum-Enhanced Trading Bot", "tier": 0, "tier_label": "Special Tier 6 — Elite",
     "monthly_revenue": "$110,000", "time_commitment": "1%", "automation_level": "99%",
     "description": "Quantum algorithm-driven trading with real-time portfolio rebalancing and risk management.",
     "agents": ["quantum_trader", "finance", "deep_researcher", "executive", "orchestrator"],
     "skills_needed": ["Quantum Optimization", "Portfolio Rebalancing", "Risk Assessment", "Algo Trading", "Market Prediction"]},
    # Tier 1 — Highest Profit
    {"id": "crypto_mining", "name": "Quantum-Optimized Crypto Mining", "tier": 1, "tier_label": "Tier 1 — Highest Profit",
     "monthly_revenue": "$32,500", "time_commitment": "1%", "automation_level": "99%",
     "description": "Fully automated crypto mining with AI-optimized hashrate and coin switching.",
     "agents": ["crypto_miner", "finance", "researcher", "orchestrator"],
     "skills_needed": ["Hashrate Optimization", "Coin Switching", "Revenue Tracking", "Market Analysis"]},
    {"id": "nft_collection", "name": "NFT Collection Creation & Trading", "tier": 1, "tier_label": "Tier 1 — Highest Profit",
     "monthly_revenue": "$52,500", "time_commitment": "2%", "automation_level": "98%",
     "description": "AI-generated NFT collections with smart contract deployment and automated marketplace trading.",
     "agents": ["nft_trader", "creative_director", "marketer", "finance"],
     "skills_needed": ["AI Art Generation", "Smart Contracts", "Marketplace Listing", "Social Media Posts"]},
    {"id": "saas_empire", "name": "SaaS Micro-Tools Empire", "tier": 1, "tier_label": "Tier 1 — Highest Profit",
     "monthly_revenue": "$30,000", "time_commitment": "3%", "automation_level": "97%",
     "description": "Deploy multiple micro-SaaS tools targeting underserved niches with recurring subscriptions.",
     "agents": ["saas_builder", "marketer", "support", "finance", "researcher"],
     "skills_needed": ["Gap Analysis", "No-Code Development", "Customer Chat", "Subscription Setup"]},
    {"id": "amazon_fba", "name": "Amazon FBA Arbitrage", "tier": 1, "tier_label": "Tier 1 — Highest Profit",
     "monthly_revenue": "$27,500", "time_commitment": "4%", "automation_level": "96%",
     "description": "Automated retail arbitrage buying and selling on Amazon FBA at scale.",
     "agents": ["arbitrage_bot", "fulfillment", "finance", "researcher"],
     "skills_needed": ["Price Scanning", "Order Routing", "Inventory Tracking", "Profitability Calculation"]},
    {"id": "print_on_demand", "name": "Print-on-Demand Empire", "tier": 1, "tier_label": "Tier 1 — Highest Profit",
     "monthly_revenue": "$16,500", "time_commitment": "2%", "automation_level": "98%",
     "description": "AI-designed products across Merch, Redbubble, and Printful with zero inventory required.",
     "agents": ["creative_director", "marketer", "fulfillment", "finance"],
     "skills_needed": ["Text-to-Image", "Marketplace Listing", "Order Processing", "Revenue Tracking"]},
    # Tier 2 — High Profit
    {"id": "tax_battalion", "name": "Automated Tax Preparation Battalion", "tier": 2, "tier_label": "Tier 2 — High Profit",
     "monthly_revenue": "$20,000", "time_commitment": "5%", "automation_level": "95%",
     "description": "AI-powered tax prep service scaled with bot fleet for high-volume seasonal and year-round filing.",
     "agents": ["tax_preparer", "sales", "support", "finance"],
     "skills_needed": ["Tax Document Collection", "E-Filing", "Lead Generation", "Deduction Analysis"]},
    {"id": "survey_battalion", "name": "Survey Taking Battalion", "tier": 2, "tier_label": "Tier 2 — High Profit",
     "monthly_revenue": "$5,500", "time_commitment": "0%", "automation_level": "100%",
     "description": "Fully automated survey completion across all major research platforms.",
     "agents": ["survey_bot", "finance", "orchestrator"],
     "skills_needed": ["Survey Discovery", "Auto-Completion", "Panel Management", "Rewards Optimization"]},
    {"id": "website_testing", "name": "Website Testing Agency", "tier": 2, "tier_label": "Tier 2 — High Profit",
     "monthly_revenue": "$10,500", "time_commitment": "5%", "automation_level": "95%",
     "description": "Sell automated QA and A/B testing services to SaaS companies and agencies.",
     "agents": ["tester_bot", "sales", "support", "marketer"],
     "skills_needed": ["UI Testing", "Bug Reporting", "A/B Test Setup", "Lead Generation"]},
    {"id": "stock_photography", "name": "Stock Photography Empire", "tier": 2, "tier_label": "Tier 2 — High Profit",
     "monthly_revenue": "$8,000", "time_commitment": "2%", "automation_level": "98%",
     "description": "Generate and license AI stock images across Shutterstock, Getty, and Adobe Stock.",
     "agents": ["creative_director", "marketer", "finance"],
     "skills_needed": ["Text-to-Image", "SEO Tagging", "Multi-Platform Distribution", "Revenue Tracking"]},
    {"id": "youtube_automation", "name": "YouTube Automation Channels", "tier": 2, "tier_label": "Tier 2 — High Profit",
     "monthly_revenue": "$12,500", "time_commitment": "3%", "automation_level": "97%",
     "description": "Faceless YouTube channels running on AI-scripted, voiced, and edited content.",
     "agents": ["content_creator", "researcher", "marketer", "finance"],
     "skills_needed": ["Viral Script Writing", "Video Generation", "SEO Tagging", "Trend Monitoring"]},
    # Tier 3 — Medium Profit
    {"id": "lead_gen", "name": "Lead Generation & Sales", "tier": 3, "tier_label": "Tier 3 — Medium Profit",
     "monthly_revenue": "$10,000", "time_commitment": "10%", "automation_level": "90%",
     "description": "Automated B2B lead generation and sales outreach using Apollo and Bland AI voice calls.",
     "agents": ["sales", "researcher", "marketer", "support"],
     "skills_needed": ["Lead Generation", "Cold Email", "Sales Calls via Bland AI", "CRM Management"]},
    {"id": "tiktok_channels", "name": "Faceless TikTok Channels", "tier": 3, "tier_label": "Tier 3 — Medium Profit",
     "monthly_revenue": "$6,500", "time_commitment": "5%", "automation_level": "95%",
     "description": "AI-scripted and generated TikTok content for multiple faceless brand channels.",
     "agents": ["content_creator", "marketer", "researcher"],
     "skills_needed": ["Viral Script Writing", "Video Generation", "Trend Monitoring", "Multi-Platform Distribution"]},
    {"id": "etsy_digital", "name": "Etsy Digital Products Store", "tier": 3, "tier_label": "Tier 3 — Medium Profit",
     "monthly_revenue": "$8,000", "time_commitment": "3%", "automation_level": "97%",
     "description": "Sell AI-generated digital templates, printables, and art on Etsy at scale.",
     "agents": ["creative_director", "marketer", "fulfillment", "finance"],
     "skills_needed": ["Text-to-Image", "Marketplace Listing", "Order Processing", "SEO Optimization"]},
    {"id": "dropshipping", "name": "Dropshipping (AI-Optimized)", "tier": 3, "tier_label": "Tier 3 — Medium Profit",
     "monthly_revenue": "$14,000", "time_commitment": "5%", "automation_level": "95%",
     "description": "AI-powered product research and supplier management for high-margin dropshipping.",
     "agents": ["dropshipper", "marketer", "support", "finance"],
     "skills_needed": ["Product Research", "Supplier Relations", "Order Routing", "Social Media Posts"]},
    {"id": "kindle_publishing", "name": "Kindle Publishing Empire", "tier": 3, "tier_label": "Tier 3 — Medium Profit",
     "monthly_revenue": "$5,500", "time_commitment": "3%", "automation_level": "97%",
     "description": "AI-authored Kindle books across multiple pen names and genres for passive royalties.",
     "agents": ["content_creator", "researcher", "marketer", "finance"],
     "skills_needed": ["Viral Script Writing", "SEO Tagging", "Market Analysis", "Multi-Platform Distribution"]},
    # Legacy / Professional Service Models
    {"id": "seo_agency", "name": "SEO & Content Agency", "tier": 3, "tier_label": "Professional Services",
     "monthly_revenue": "$15,000", "time_commitment": "10%", "automation_level": "90%",
     "description": "Full-service SEO and content agency powered by AI writers, researchers, and outreach bots.",
     "agents": ["marketer", "researcher", "sales", "support"],
     "skills_needed": ["SEO Optimization", "Blog Content", "Lead Generation", "Market Analysis"]},
    {"id": "ai_chatbots", "name": "AI Chatbot Agency", "tier": 3, "tier_label": "Professional Services",
     "monthly_revenue": "$18,000", "time_commitment": "8%", "automation_level": "92%",
     "description": "Build and deploy custom AI chatbots for SMBs on a monthly retainer.",
     "agents": ["saas_builder", "sales", "support", "marketer"],
     "skills_needed": ["No-Code Development", "Lead Generation", "Customer Chat", "Social Media Posts"]},
    {"id": "nocode_agency", "name": "No-Code App Agency", "tier": 3, "tier_label": "Professional Services",
     "monthly_revenue": "$20,000", "time_commitment": "10%", "automation_level": "90%",
     "description": "Build web and mobile apps for clients using no-code platforms with AI-generated code.",
     "agents": ["saas_builder", "creative_director", "sales", "support", "finance"],
     "skills_needed": ["No-Code Development", "Text-to-Image", "Proposal Writing", "Customer Chat"]},
    {"id": "ugc_network", "name": "UGC Content Network", "tier": 3, "tier_label": "Professional Services",
     "monthly_revenue": "$12,000", "time_commitment": "8%", "automation_level": "92%",
     "description": "User-generated content creation and distribution network for brand partnerships.",
     "agents": ["content_creator", "marketer", "sales", "creative_director"],
     "skills_needed": ["Viral Script Writing", "Video Generation", "Lead Generation", "Brand Consistency"]},
]

AGENT_MAP = {a["id"]: a for a in AGENTS}
BIZ_MAP = {b["id"]: b for b in BUSINESSES}


class ComposeRequest(BaseModel):
    business_ids: List[str]
    agent_ids: List[str]
    custom_note: Optional[str] = None


@router.get("/intelligence/status")
async def intelligence_status():
    """Return paperclip adapter provider health — which brain is active."""
    try:
        from .paperclip_adapter import paperclip
        return paperclip.status()
    except Exception as e:
        return {"active": "unknown", "error": str(e)}


@router.get("/businesses")
async def get_businesses():
    return {"businesses": BUSINESSES, "total": len(BUSINESSES)}


@router.get("/agents")
async def get_agents():
    return {"agents": AGENTS, "total": len(AGENTS)}


@router.post("/compose")
async def compose_company(req: ComposeRequest):
    selected_businesses = [BIZ_MAP[b] for b in req.business_ids if b in BIZ_MAP]
    selected_agents = [AGENT_MAP[a] for a in req.agent_ids if a in AGENT_MAP]

    if not selected_businesses and not selected_agents:
        raise HTTPException(status_code=400, detail="Select at least one business template or agent.")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return _compose_offline(selected_businesses, selected_agents, req.custom_note)

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        biz_block = "\n".join(
            f"- {b['name']} ({b['monthly_revenue']}/mo): {b['description']}"
            for b in selected_businesses
        ) or "None specified"
        agent_block = "\n".join(
            f"- {a['name']}: {', '.join(a['skills'][:4])}"
            for a in selected_agents
        ) or "None specified"

        prompt = f"""You are a business architect for the Better Business Builder autonomous AI platform.

The user is composing a unique company by combining:

BUSINESS MODELS:
{biz_block}

AI AGENT STACK:
{agent_block}

{f'User note: {req.custom_note}' if req.custom_note else ''}

Design a UNIQUE combined company concept. Include:
1. A creative company name
2. One-paragraph pitch (what makes this combination powerful)
3. Revenue streams with estimated monthly totals
4. The full autonomous workflow: client acquisition → onboarding → delivery → support → billing
5. Unfair competitive advantages of this specific combination
6. Recommended next step to launch

Be bold, specific, and exciting. Format cleanly with headers."""

        message = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}]
        )
        concept = message.content[0].text
        powered_by = "paperclip"
    except Exception:
        return _compose_offline(selected_businesses, selected_agents, req.custom_note)

    return {
        "concept": concept,
        "selected_businesses": selected_businesses,
        "selected_agents": selected_agents,
        "powered_by": powered_by,
    }


def _compose_offline(businesses, agents, note):
    biz_names = [b["name"] for b in businesses] or ["Custom"]
    agent_names = [a["name"] for a in agents] or ["Custom"]
    revenues = [b["monthly_revenue"] for b in businesses]
    all_skills = list(dict.fromkeys(s for a in agents for s in a["skills"]))

    concept = f"""## Custom Company Concept (Offline Mode)

**Business Models:** {', '.join(biz_names)}
**Agent Stack:** {', '.join(agent_names)}
**Revenue Streams:** {', '.join(revenues) if revenues else 'TBD'}
**Combined Skills:** {', '.join(all_skills[:12]) if all_skills else 'TBD'}

{f'Notes: {note}' if note else ''}

Set ANTHROPIC_API_KEY in your environment to unlock AI-generated company concepts powered by Paperclip (Claude)."""

    return {
        "concept": concept,
        "selected_businesses": businesses,
        "selected_agents": agents,
        "powered_by": "offline",
    }


# ---------------------------------------------------------------------------
# Board of Directors API endpoints
# ---------------------------------------------------------------------------

class BoardConsultRequest(BaseModel):
    topic: str
    context: Optional[str] = None
    include_chairman: bool = True

class BoardExpertRequest(BaseModel):
    role: str   # ceo | coo | cfo | cto | cmo | cso | chairman
    question: str

class EchoOperatorRequest(BaseModel):
    task: str
    start_url: Optional[str] = None
    extract: Optional[str] = None
    max_steps: int = 15


@router.get("/board/status")
async def board_status():
    """Return online/offline status for each C-suite AI board member."""
    try:
        from .board.board_room import get_board
        return get_board().status()
    except Exception as e:
        return {"error": str(e)}


@router.get("/board/members")
async def board_members():
    """Return the full C-suite roster: roles, models, and expertise."""
    return {
        "members": [
            {"role": "chairman", "title": "Board Chairman",          "model": "claude-opus-4-7 (via paperclip)", "expertise": ["Meta-oversight", "Ethical review", "Final veto"], "vps": "Anthropic API"},
            {"role": "ceo",      "title": "Chief Executive Officer", "model": "deepseek-r1:14b",                  "expertise": ["Strategic vision", "Risk assessment", "Capital allocation"], "install": "ollama pull deepseek-r1:14b"},
            {"role": "coo",      "title": "Chief Operating Officer", "model": "hermes3:8b",                       "expertise": ["Agent orchestration", "Workflow design", "KPI tracking"],       "install": "ollama pull hermes3:8b"},
            {"role": "cfo",      "title": "Chief Financial Officer", "model": "qwen2.5:7b",                       "expertise": ["P&L management", "Cash flow", "Budget approval"],              "install": "ollama pull qwen2.5:7b"},
            {"role": "cto",      "title": "Chief Technology Officer","model": "deepseek-coder-v2:16b",            "expertise": ["System architecture", "Security review", "Scalability"],       "install": "ollama pull deepseek-coder-v2:16b"},
            {"role": "cmo",      "title": "Chief Marketing Officer", "model": "llama3.2:3b",                      "expertise": ["Brand strategy", "Content marketing", "Growth tactics"],       "install": "ollama pull llama3.2:3b"},
            {"role": "cso",      "title": "Chief Strategy Officer",  "model": "qwen3:30b-a3b (or Grok-1)",       "expertise": ["Competitive strategy", "Market disruption", "Scenario planning"], "install": "ollama pull qwen3:30b-a3b  # or set GROK_VPS_URL"},
        ]
    }


@router.post("/board/consult")
async def board_consult(req: BoardConsultRequest):
    """
    Call a full board meeting on any topic.
    All C-suite members deliberate in parallel; Chairman reviews.
    """
    try:
        from .board.board_room import get_board
        board = get_board()
        minutes = board.deliberate(req.topic, context=req.context, include_chairman=req.include_chairman)
        return {
            "topic":            minutes.topic,
            "majority":         minutes.majority,
            "vote_tally":       minutes.vote_tally,
            "consensus":        minutes.consensus,
            "chairman_verdict": minutes.chairman_verdict,
            "decisions":        [
                {
                    "member":         d.member,
                    "role":           d.role,
                    "model":          d.model,
                    "opinion":        d.opinion,
                    "recommendation": d.recommendation,
                    "confidence":     d.confidence,
                    "reasoning":      d.reasoning,
                    "conditions":     d.conditions,
                }
                for d in minutes.decisions
            ],
            "available_members":   minutes.available_members,
            "unavailable_members": minutes.unavailable_members,
            "duration_seconds":    minutes.duration_seconds,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/board/ask")
async def board_ask_expert(req: BoardExpertRequest):
    """Route a question to a specific C-suite board member for domain advice."""
    try:
        from .board.board_room import get_board
        answer = get_board().ask_expert(req.role, req.question)
        return {"role": req.role, "question": req.question, "answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/echo/operate")
async def echo_operate(req: EchoOperatorRequest):
    """
    Run Echo Operator on a browser task.
    Vision model sees the screen; Hermes decides actions.
    Requires: playwright + qwen2.5-vl:3b on VPS.
    """
    try:
        from .computer_use.echo_operator import EchoOperator
        async with EchoOperator() as echo:
            result = await echo.browse(
                task=req.task,
                start_url=req.start_url,
                extract=req.extract,
                max_steps=req.max_steps,
            )
        return {
            "task":           result.task,
            "success":        result.success,
            "steps":          result.steps,
            "extracted_data": result.extracted_data,
            "error":          result.error,
            "duration":       result.duration_seconds,
            "screenshots":    result.screenshots_taken,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
