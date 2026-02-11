"""
Market research agent using web scraping and ECH0 intelligence.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations
from typing import Dict, List

try:
    from scrapingbee import ScrapingBeeClient
    SCRAPINGBEE_AVAILABLE = True
except ImportError:
    ScrapingBeeClient = None
    SCRAPINGBEE_AVAILABLE = False

from ..ech0_service import ECH0Service

class MarketResearch:
    """
    Market research agent that uses web scraping to gather intelligence.
    """

    def __init__(self, api_key: str):
        if SCRAPINGBEE_AVAILABLE:
            self.client = ScrapingBeeClient(api_key=api_key)
        else:
            self.client = None
        self.ech0_service = ECH0Service()

    async def scrape_competitors(self, urls: List[str]) -> Dict[str, str]:
        """
        Scrape content from a list of competitor URLs.
        """
        results = {}
        for url in urls:
            try:
                # Try scraping with ECH0 first
                results[url] = await self.ech0_service.scrape_url(url)
            except Exception:
                # Fallback to ScrapingBee
                if self.client:
                    response = self.client.get(url)
                    if response.ok:
                        results[url] = response.text
                    else:
                        results[url] = f"Error: {response.status_code}"
                else:
                    results[url] = "Error: ScrapingBee not available"
        return results

    async def google_search(self, query: str) -> Dict:
        """
        Perform a Google search and scrape the results.
        """
        try:
            # Try searching with ECH0 first
            return await self.ech0_service.google_search(query)
        except Exception:
            # Fallback to ScrapingBee
            if self.client:
                response = self.client.get(
                    "https://www.google.com/search",
                    params={"q": query}
                )
                if response.ok:
                    return response.json()
                return {"error": response.status_code}
            return {"error": "ScrapingBee not available"}
