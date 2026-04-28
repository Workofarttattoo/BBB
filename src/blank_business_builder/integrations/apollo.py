"""
Apollo lead search/enrichment integration.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests


class ApolloService:
    """Thin API client for Apollo people search and enrichment."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout_seconds: int = 20,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.api_key = api_key or os.getenv("APOLLO_API_KEY", "")
        self.base_url = (base_url or os.getenv("APOLLO_BASE_URL", "https://api.apollo.io")).rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.session = session or requests.Session()

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError("APOLLO_API_KEY is required")
        response = self.session.post(
            url=f"{self.base_url}{path}",
            json=payload,
            headers={
                "X-Api-Key": self.api_key,
                "Content-Type": "application/json",
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        return response.json() if response.content else {}

    def search_people(
        self,
        *,
        q_organization_name: Optional[str] = None,
        q_keywords: Optional[str] = None,
        page: int = 1,
        per_page: int = 25,
    ) -> Dict[str, Any]:
        """Search prospects; call enrich_person for complete contact details."""
        payload: Dict[str, Any] = {"page": page, "per_page": max(1, min(per_page, 100))}
        if q_organization_name:
            payload["q_organization_name"] = q_organization_name
        if q_keywords:
            payload["q_keywords"] = q_keywords
        return self._post("/v1/mixed_people/search", payload)

    def enrich_person(
        self,
        *,
        email: Optional[str] = None,
        linkedin_url: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        company_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Enrich a specific person using available identifiers."""
        payload: Dict[str, Any] = {}
        if email:
            payload["email"] = email
        if linkedin_url:
            payload["linkedin_url"] = linkedin_url
        if first_name:
            payload["first_name"] = first_name
        if last_name:
            payload["last_name"] = last_name
        if company_name:
            payload["company_name"] = company_name
        return self._post("/v1/people/match", payload)
