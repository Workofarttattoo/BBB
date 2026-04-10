import pytest
import numpy as np
from src.blank_business_builder.quantum_stack_optimizer import QuantumStateEngine

def test_expectation_initial_state():
    """Test expectation value for the initial |0...0> state."""
    qse = QuantumStateEngine(num_qubits=2)
    # State is |00>, so probability is 1.0 for state 0 (bits 00).
    # For Z0 (qubit 0), bit is 0 -> sign is +1. Expectation = 1.0
    # For Z1 (qubit 1), bit is 0 -> sign is +1. Expectation = 1.0
    assert qse.expectation('Z0') == pytest.approx(1.0)
    assert qse.expectation('Z1') == pytest.approx(1.0)

def test_expectation_invalid_observable():
    """Test expectation with an observable not starting with 'Z'."""
    qse = QuantumStateEngine(num_qubits=1)
    # Should return 0.0 for unknown observables
    assert qse.expectation('X0') == 0.0
    assert qse.expectation('Y') == 0.0
    assert qse.expectation('invalid') == 0.0

def test_expectation_default_qubit():
    """Test expectation when observable is just 'Z' (defaults to qubit 0)."""
    qse = QuantumStateEngine(num_qubits=1)
    assert qse.expectation('Z') == pytest.approx(1.0)

def test_expectation_superposition():
    """Test expectation value for a superposition state."""
    qse = QuantumStateEngine(num_qubits=1)
    qse.hadamard(0)
    # State is (|0> + |1>) / sqrt(2)
    # Probabilities: P(0) = 0.5, P(1) = 0.5
    # Expectation of Z0 = (+1)*0.5 + (-1)*0.5 = 0.0
    assert qse.expectation('Z0') == pytest.approx(0.0, abs=1e-9)

def test_expectation_entangled_state():
    """Test expectation value after CNOT (entanglement)."""
    qse = QuantumStateEngine(num_qubits=2)
    qse.hadamard(0)
    qse.cnot(0, 1)
    # State is (|00> + |11>) / sqrt(2)
    # State 0 (00): P=0.5. Z0 sign=+1, Z1 sign=+1
    # State 3 (11): P=0.5. Z0 sign=-1, Z1 sign=-1
    # Z0 exp = 0.5*(+1) + 0.5*(-1) = 0.0
    # Z1 exp = 0.5*(+1) + 0.5*(-1) = 0.0
    assert qse.expectation('Z0') == pytest.approx(0.0, abs=1e-9)
    assert qse.expectation('Z1') == pytest.approx(0.0, abs=1e-9)

def test_expectation_specific_state():
    """Test expectation by manually setting the state to test specific outcomes."""
    qse = QuantumStateEngine(num_qubits=2)
    # Set state to |01> (qubit 0 is 1, qubit 1 is 0)
    # State index 1 (binary 01): P=1.0
    qse.state = np.zeros(4, dtype=complex)
    qse.state[1] = 1.0

    # Qubit 0 is bit 0 -> 1 -> sign -1
    # Qubit 1 is bit 1 -> 0 -> sign +1
    assert qse.expectation('Z0') == pytest.approx(-1.0)
    assert qse.expectation('Z1') == pytest.approx(1.0)

    # Set state to |10> (qubit 0 is 0, qubit 1 is 1)
    # State index 2 (binary 10): P=1.0
    qse.state = np.zeros(4, dtype=complex)
    qse.state[2] = 1.0

    # Qubit 0 is bit 0 -> 0 -> sign +1
    # Qubit 1 is bit 1 -> 1 -> sign -1
    assert qse.expectation('Z0') == pytest.approx(1.0)
    assert qse.expectation('Z1') == pytest.approx(-1.0)
