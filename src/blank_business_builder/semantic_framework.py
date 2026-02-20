"""
Semantic Business Framework
===========================
A lightweight Python implementation of the "Business-as-Code" semantic philosophy.
Inspired by sdk.do and Schema.org.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Any
import json
import uuid

@dataclass
class SemanticObject:
    """Base class for all semantic business objects."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = "Thing"
    
    def to_json(self):
        return json.dumps(asdict(self), indent=2)

@dataclass
class Organization(SemanticObject):
    """Represents a company or organization."""
    type: str = "Organization"
    name: str = ""
    email: Optional[str] = None
    description: str = ""
    industry: str = ""
    domain: str = ""

@dataclass
class Person(SemanticObject):
    """Represents a human contact."""
    type: str = "Person"
    name: str = ""
    email: Optional[str] = None
    role: str = ""
    organization_id: Optional[str] = None

@dataclass
class Lead(SemanticObject):
    """A potential sales opportunity."""
    type: str = "Lead"
    person: Optional[Person] = None
    organization: Optional[Organization] = None
    source: str = ""
    status: str = "New"  # New, Qualified, Contacted, Negotiating, Won, Lost
    score: int = 0
    notes: List[str] = field(default_factory=list)

@dataclass
class Sale(SemanticObject):
    """A completed or in-progress transaction."""
    type: str = "Sale"
    lead_id: str = ""
    amount: float = 0.0
    currency: str = "USD"
    stage: str = "Proposal"
    probability: float = 0.0

class SemanticDB:
    """A simple in-memory semantic database."""
    def __init__(self):
        self._store = {}
    
    def save(self, obj: SemanticObject):
        self._store[obj.id] = obj
        return obj
        
    def query(self, type_filter: str = None, **kwargs):
        """Query objects by type and attributes."""
        results = []
        for obj in self._store.values():
            if type_filter and obj.type != type_filter:
                continue
            
            match = True
            for k, v in kwargs.items():
                if getattr(obj, k, None) != v:
                    match = False
                    break
            if match:
                results.append(obj)
        return results

# Global DB instance for the brain
db = SemanticDB()
@dataclass
class VerifiedProspect(SemanticObject):
    """A verified prospect ready for resale."""
    type: str = "VerifiedProspect"
    lead: Optional[Lead] = None
    verification_date: str = ""
    resale_price: float = 0.0
    status: str = "Available" # Available, Sold, Reserved
