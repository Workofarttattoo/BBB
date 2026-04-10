"""
Tests for QuantumStateEngine in quantum_stack_optimizer.py
"""
import pytest
import numpy as np
from src.blank_business_builder.quantum_stack_optimizer import QuantumStateEngine

def test_phase_gate_zero_angle():
    """Test that a phase rotation of 0 does not change the state."""
    engine = QuantumStateEngine(1)
    # Put into superposition to see relative phase
    engine.hadamard(0)
    expected_state = np.copy(engine.state)

    engine.phase(0, 0.0)

    np.testing.assert_array_almost_equal(engine.state, expected_state)

def test_phase_gate_pi():
    """Test that a phase rotation of pi flips the sign of the |1> state."""
    engine = QuantumStateEngine(1)
    engine.hadamard(0)  # State is (|0> + |1>)/sqrt(2)

    engine.phase(0, np.pi)

    # Expected state: (|0> - |1>)/sqrt(2)
    expected_state = np.array([1/np.sqrt(2), -1/np.sqrt(2)])
    np.testing.assert_array_almost_equal(engine.state, expected_state)

def test_phase_gate_pi_half():
    """Test that a phase rotation of pi/2 adds an imaginary phase (S gate)."""
    engine = QuantumStateEngine(1)
    engine.hadamard(0)  # State is (|0> + |1>)/sqrt(2)

    engine.phase(0, np.pi / 2)

    # Expected state: (|0> + i|1>)/sqrt(2)
    expected_state = np.array([1/np.sqrt(2), 1j/np.sqrt(2)])
    np.testing.assert_array_almost_equal(engine.state, expected_state)

def test_phase_gate_multiple_qubits():
    """Test applying phase rotation to specific qubits in a multi-qubit system."""
    engine = QuantumStateEngine(2)

    # Apply Hadamard to both qubits to create equal superposition
    # State: |00> + |01> + |10> + |11> / 2
    engine.hadamard(0)
    engine.hadamard(1)

    # Apply pi phase to qubit 1 (the higher order bit in the state vector)
    engine.phase(1, np.pi)

    # Qubit 1 is the most significant bit.
    # States where qubit 1 is |1> should be negated: |10> and |11>
    # States where qubit 1 is |0> remain the same: |00> and |01>
    # Indices: 0 (|00>), 1 (|01>), 2 (|10>), 3 (|11>)
    expected_state = np.array([0.5, 0.5, -0.5, -0.5])
    np.testing.assert_array_almost_equal(engine.state, expected_state)

def test_phase_gate_no_superposition():
    """Test applying phase to a computational basis state (global phase effect)."""
    engine = QuantumStateEngine(1)
    # State is |0>, phase applied to |1> has no effect since |1> amplitude is 0
    expected_state = np.array([1.0, 0.0])
    engine.phase(0, np.pi)
    np.testing.assert_array_almost_equal(engine.state, expected_state)
