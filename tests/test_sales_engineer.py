import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from blank_business_builder.sales_engineer import SalesEngineer
from blank_business_builder.semantic_framework import Lead, Person, Organization, db

class MockCoreSystem:
    def __init__(self):
        self.llm_engine = None

    def log_activity(self, *args, **kwargs):
        pass

class TestSalesEngineerQualify:
    def setup_method(self):
        # Clear the in-memory db before each test to prevent cross-test pollution
        db._store = {}
        self.core = MockCoreSystem()
        self.se = SalesEngineer(self.core)

    def test_missing_organization(self):
        lead = Lead(person=Person(name="John", role="CTO"))
        self.se.qualify(lead)
        assert lead.status == "Disqualified"
        assert lead.score == 0

    def test_missing_person(self):
        lead = Lead(organization=Organization(name="Acme", industry="AI"))
        self.se.qualify(lead)
        assert lead.status == "Disqualified"
        assert lead.score == 0

    def test_no_matches(self):
        lead = Lead(
            person=Person(name="John", role="Developer"),
            organization=Organization(name="Acme", industry="E-commerce")
        )
        self.se.qualify(lead)
        assert lead.score == 50
        assert lead.status == "Low Priority"
        # Verify it was saved to DB
        assert lead.id in db._store

    def test_industry_match_only(self):
        lead = Lead(
            person=Person(name="John", role="Developer"),
            organization=Organization(name="Acme", industry="B2B Services")
        )
        self.se.qualify(lead)
        assert lead.score == 70
        assert lead.status == "Qualified"

    def test_role_match_only(self):
        lead = Lead(
            person=Person(name="John", role="VP of Engineering"),
            organization=Organization(name="Acme", industry="E-commerce")
        )
        self.se.qualify(lead)
        assert lead.score == 70
        assert lead.status == "Qualified"

    def test_both_matches(self):
        lead = Lead(
            person=Person(name="John", role="Founder & CEO"),
            organization=Organization(name="Acme", industry="AI / ML")
        )
        self.se.qualify(lead)
        assert lead.score == 90
        assert lead.status == "Qualified"

    def test_case_insensitivity(self):
        lead = Lead(
            person=Person(name="John", role="ceo"),
            organization=Organization(name="Acme", industry="saas platform")
        )
        self.se.qualify(lead)
        assert lead.score == 90
        assert lead.status == "Qualified"
