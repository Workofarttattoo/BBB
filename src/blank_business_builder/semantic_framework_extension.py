@dataclass
class VerifiedProspect(SemanticObject):
    """A verified prospect ready for resale."""
    type: str = "VerifiedProspect"
    lead: Optional[Lead] = None
    verification_date: str = ""
    resale_price: float = 0.0
    status: str = "Available" # Available, Sold, Reserved
