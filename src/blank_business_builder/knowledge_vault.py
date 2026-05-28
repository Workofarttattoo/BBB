"""
Knowledge Vault — Centralized Business Memory for Autonomous Agents

Provides instant access to:
- Company Identity (Who we are)
- Services & Pricing (What we sell)
- Policies & Rules (How we operate)
- Skills Library (How we execute)

Architecture:
- Hot Cache: JSON/Dict for instant retrieval of core facts
- Semantic Layer: SQLite + Embeddings for deep search (optional/lazy)
- Sync: File-based (watchers) or Firebase (optional)
"""

import json
import os
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

# Try to import optional semantic search deps
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False

class KnowledgeVault:
    def __init__(self, company_path: str = "companies/saas-micro-tools"):
        self.company_path = Path(company_path)
        self.cache: Dict[str, Any] = {}
        self.index: Dict[str, Dict] = {}  # filename -> metadata
        self.semantic_model = None
        
        # Initialize
        self._load_core_files()
        if SEMANTIC_AVAILABLE:
            self._init_semantic()

    def _load_core_files(self):
        """Load all core business files into hot cache."""
        files_to_load = [
            ("company", "COMPANY.md"),
            ("policy", "policy.json"),
            ("services", "services.json"),  # Optional
            ("pricing", "pricing.json"),    # Optional
        ]
        
        for key, filename in files_to_load:
            filepath = self.company_path / filename
            if filepath.exists():
                content = filepath.read_text()
                if filename.endswith(".json"):
                    self.cache[key] = json.loads(content)
                else:
                    self.cache[key] = content
                self.index[filename] = {
                    "key": key,
                    "path": str(filepath),
                    "size": len(content),
                    "updated": datetime.fromtimestamp(filepath.stat().st_mtime).isoformat()
                }
        
        # Load skills directory
        skills_dir = self.company_path / "skills"
        if skills_dir.exists():
            self.cache["skills"] = {}
            for skill_file in skills_dir.glob("*.md"):
                self.cache["skills"][skill_file.stem] = skill_file.read_text()
                self.index[f"skills/{skill_file.name}"] = {
                    "key": f"skills.{skill_file.stem}",
                    "path": str(skill_file),
                    "size": len(skill_file.read_text()),
                    "updated": datetime.fromtimestamp(skill_file.stat().st_mtime).isoformat()
                }

    def _init_semantic(self):
        """Initialize semantic search model (lazy load)."""
        try:
            # Use a small, fast model for local embedding
            self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
            print("[KnowledgeVault] Semantic search enabled (all-MiniLM-L6-v2)")
        except Exception as e:
            print(f"[KnowledgeVault] Semantic search disabled: {e}")
            self.semantic_model = None

    def get(self, key: str, default: Any = None) -> Any:
        """Instant retrieval from hot cache."""
        # Support dot notation: "skills.sales_outreach"
        parts = key.split(".")
        data = self.cache
        for part in parts:
            if isinstance(data, dict):
                data = data.get(part, None)
            else:
                return default
            if data is None:
                return default
        return data

    def search(self, query: str, limit: int = 5) -> List[Dict]:
        """Search across all knowledge base content."""
        results = []
        
        # 1. Simple keyword match (always available)
        query_lower = query.lower()
        for filename, meta in self.index.items():
            key = meta["key"]
            content = self.get(key, "")
            if isinstance(content, str) and query_lower in content.lower():
                # Extract snippet
                idx = content.lower().find(query_lower)
                start = max(0, idx - 50)
                end = min(len(content), idx + 100)
                snippet = content[start:end].replace("\n", " ")
                results.append({
                    "source": filename,
                    "key": key,
                    "snippet": f"...{snippet}...",
                    "score": 1.0  # Keyword match score
                })
        
        # 2. Semantic search (if available)
        if SEMANTIC_AVAILABLE and self.semantic_model and len(results) < limit:
            try:
                # Encode query
                query_embedding = self.semantic_model.encode([query])[0]
                
                # Encode all text chunks (simplified: should be chunked properly in prod)
                texts = []
                keys = []
                for filename, meta in self.index.items():
                    content = self.get(meta["key"], "")
                    if isinstance(content, str):
                        # Chunk by paragraphs
                        chunks = content.split("\n\n")
                        for chunk in chunks:
                            if len(chunk) > 20:  # Ignore tiny chunks
                                texts.append(chunk)
                                keys.append((filename, meta["key"]))
                
                if texts:
                    text_embeddings = self.semantic_model.encode(texts)
                    # Cosine similarity
                    similarities = np.dot(text_embeddings, query_embedding) / (
                        np.linalg.norm(text_embeddings, axis=1) * np.linalg.norm(query_embedding)
                    )
                    
                    # Top K
                    top_indices = np.argsort(similarities)[::-1][:limit]
                    for idx in top_indices:
                        if similarities[idx] > 0.5:  # Threshold
                            filename, key = keys[idx]
                            snippet = texts[idx][:150].replace("\n", " ")
                            # Avoid duplicates with keyword search
                            if not any(r["source"] == filename and r["snippet"][:50] == snippet[:50] for r in results):
                                results.append({
                                    "source": filename,
                                    "key": key,
                                    "snippet": f"...{snippet}...",
                                    "score": float(similarities[idx])
                                })
            except Exception as e:
                print(f"[KnowledgeVault] Semantic search error: {e}")
        
        # Sort by score
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    def get_system_prompt_context(self) -> str:
        """Generate a compact context block for agent system prompts."""
        company = self.get("company", "")
        policy = self.get("policy", {})
        services = self.get("services", {})
        pricing = self.get("pricing", {})
        
        context = [
            "### COMPANY IDENTITY ###",
            company if isinstance(company, str) else json.dumps(company),
            "",
            "### POLICIES & RULES ###",
            json.dumps(policy, indent=2) if isinstance(policy, dict) else str(policy),
            "",
            "### SERVICES & PRICING ###",
            json.dumps(services, indent=2) if isinstance(services, dict) else str(services),
            json.dumps(pricing, indent=2) if isinstance(pricing, dict) else str(pricing),
        ]
        
        return "\n".join(context)

    def reload(self):
        """Force reload from disk (for GUI updates)."""
        self.cache.clear()
        self.index.clear()
        self._load_core_files()
        return {"status": "reloaded", "files": len(self.index)}

# Singleton instance
_vault_instance: Optional[KnowledgeVault] = None

def get_vault(company_path: str = "companies/saas-micro-tools") -> KnowledgeVault:
    global _vault_instance
    if _vault_instance is None:
        _vault_instance = KnowledgeVault(company_path)
    return _vault_instance
