"""
Lightweight arXiv fetch for proactive ingest jobs.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations

import logging
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List

logger = logging.getLogger(__name__)

ARXIV_API = "http://export.arxiv.org/api/query"
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


@dataclass
class ArxivPaper:
    arxiv_id: str
    title: str
    summary: str
    published: str
    categories: List[str]


def fetch_recent_papers(
    *,
    categories: str = "cat:cs.AI OR cat:cs.LG OR cat:cs.SE",
    max_results: int = 15,
    days_back_hint: str = "submittedDate:[202401010000 TO 209912312359]",
) -> List[ArxivPaper]:
    """
    Fetch recent arXiv papers matching categories.
    Uses arXiv Atom API (no API key required).
    """
    query = f"({categories}) AND {days_back_hint}"
    params = urllib.parse.urlencode(
        {
            "search_query": query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
    )
    url = f"{ARXIV_API}?{params}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            raw = resp.read()
    except Exception as exc:
        logger.warning("arXiv fetch failed: %s", exc)
        return []

    root = ET.fromstring(raw)
    papers: List[ArxivPaper] = []
    for entry in root.findall("atom:entry", ATOM_NS):
        aid = (entry.find("atom:id", ATOM_NS).text or "").split("/abs/")[-1]
        title = (entry.find("atom:title", ATOM_NS).text or "").strip().replace("\n", " ")
        summary = (entry.find("atom:summary", ATOM_NS).text or "").strip().replace("\n", " ")[:400]
        published = (entry.find("atom:published", ATOM_NS).text or "")[:10]
        cats = [c.get("term", "") for c in entry.findall("atom:category", ATOM_NS)]
        papers.append(
            ArxivPaper(
                arxiv_id=aid,
                title=title,
                summary=summary,
                published=published,
                categories=cats,
            )
        )
    return papers


def format_papers_for_prompt(papers: List[ArxivPaper]) -> str:
    if not papers:
        return "(No arXiv papers fetched — proceed with patent queue review only.)"
    lines = [f"Fetched {len(papers)} recent arXiv papers:"]
    for p in papers[:12]:
        lines.append(f"- [{p.arxiv_id}] {p.title} ({p.published}) — {p.summary[:120]}...")
    return "\n".join(lines)
