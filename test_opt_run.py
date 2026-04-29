import sys
from unittest.mock import MagicMock

# Mock dependencies
sys.modules['fastapi'] = MagicMock()
sys.modules['sqlalchemy'] = MagicMock()
sys.modules['sqlalchemy.ext.asyncio'] = MagicMock()
sys.modules['sqlalchemy.orm'] = MagicMock()
sys.modules['pydantic'] = MagicMock()
sys.modules['celery'] = MagicMock()
sys.modules['redis'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['openai'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['httpx'] = MagicMock()
sys.modules['stripe'] = MagicMock()
sys.modules['sendgrid'] = MagicMock()
sys.modules['twilio'] = MagicMock()
sys.modules['tweepy'] = MagicMock()

from src.blank_business_builder.expert_integration import ExpertEnhancedOrchestrator
from src.blank_business_builder.autonomous_business import AutonomousTask
from src.blank_business_builder.expert_system import ExpertDomain

orchestrator = ExpertEnhancedOrchestrator()
task1 = AutonomousTask(task_id="t1", business_id="b1", description="analyze chemical properties", task_type="test")
domain1 = orchestrator._map_task_to_domain(task1)
print(f"Task 1 domain: {domain1}")

task2 = AutonomousTask(task_id="t2", business_id="b2", description="do some marketing stuff", task_type="test")
domain2 = orchestrator._map_task_to_domain(task2)
print(f"Task 2 domain: {domain2}")

from src.blank_business_builder.quantum_stack_optimizer import QuantumStackOptimizer
from src.blank_business_builder.quantum_features_master import QuantumFeature

optimizer = QuantumStackOptimizer()
f1 = QuantumFeature(id="f1", name="AI Prediction Tool", description="test", category="test", quantum_priority=10)
f2 = QuantumFeature(id="f2", name="UI Dashboard", description="test", category="test", quantum_priority=5)

alloc = optimizer._calculate_quantum_resource_allocation([f1, f2])
print(f"Allocation: {alloc}")
