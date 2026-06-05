import sys
from unittest.mock import MagicMock

# Mock dependencies
sys.modules['sqlalchemy'] = MagicMock()
sys.modules['sqlalchemy.orm'] = MagicMock()

mock_integrations = MagicMock()
mock_integrations.IntegrationFactory = MagicMock()
sys.modules['src.blank_business_builder.integrations'] = mock_integrations
sys.modules['.integrations'] = mock_integrations

mock_db = MagicMock()
sys.modules['src.blank_business_builder.database'] = mock_db
sys.modules['.database'] = mock_db

mock_payments = MagicMock()
sys.modules['src.blank_business_builder.payments'] = mock_payments
sys.modules['.payments'] = mock_payments

mock_gates = MagicMock()
sys.modules['src.blank_business_builder.approval_gates'] = mock_gates
sys.modules['.approval_gates'] = mock_gates

mock_policy = MagicMock()
sys.modules['src.blank_business_builder.enterprise_agent_policy'] = mock_policy
sys.modules['.enterprise_agent_policy'] = mock_policy

from src.blank_business_builder.level6_agent import Level6Agent
import datetime

agent = Level6Agent.__new__(Level6Agent)
user = MagicMock()
user.created_at = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)

# Test new _needs_onboarding signature
assert agent._needs_onboarding(user, 0) == True
assert agent._needs_onboarding(user, 1) == False

business = MagicMock()
business.id = "b1"

# Test new _needs_marketing_campaign signature
assert agent._needs_marketing_campaign(business, {"b1", "b2"}) == False
assert agent._needs_marketing_campaign(business, {"b2"}) == True

print("Tests passed!")
