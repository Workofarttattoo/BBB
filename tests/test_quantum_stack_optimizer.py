import pytest
import numpy as np
from unittest.mock import patch, ANY

from src.blank_business_builder.quantum_stack_optimizer import QuantumStateEngine

def test_hadamard_gate():
    """Test that the hadamard method constructs the correct matrix and applies it."""
    engine = QuantumStateEngine(num_qubits=1)
    target_qubit = 0

    expected_h_matrix = np.array([[1, 1], [1, -1]]) / np.sqrt(2)

    with patch.object(engine, '_apply_single_qubit_gate') as mock_apply:
        engine.hadamard(target_qubit)

        mock_apply.assert_called_once()
        args, kwargs = mock_apply.call_args

        # Verify matrix
        passed_matrix = args[0]
        np.testing.assert_array_almost_equal(passed_matrix, expected_h_matrix)

        # Verify qubit index
        passed_qubit = args[1]
        assert passed_qubit == target_qubit

def test_hadamard_gate_state_effect():
    """Test the actual effect of the Hadamard gate on the quantum state."""
    engine = QuantumStateEngine(num_qubits=1)

    # Initial state is |0>
    assert engine.state[0] == 1.0
    assert engine.state[1] == 0.0

    # Apply Hadamard
    engine.hadamard(0)

    # Expected state is |+> = (|0> + |1>) / sqrt(2)
    expected_amplitude = 1 / np.sqrt(2)
    assert np.isclose(engine.state[0], expected_amplitude)
    assert np.isclose(engine.state[1], expected_amplitude)

def test_hadamard_gate_state_effect_multi_qubit():
    """Test the actual effect of the Hadamard gate on a specific qubit in a multi-qubit system."""
    engine = QuantumStateEngine(num_qubits=2)

    # Initial state is |00>
    assert engine.state[0] == 1.0

    # Apply Hadamard to second qubit (qubit 1)
    # The state should become |00> + |10> / sqrt(2)
    # Because state index is essentially an integer representation of binary state.
    # We need to verify how _apply_single_qubit_gate works.
    engine.hadamard(1)

    expected_amplitude = 1 / np.sqrt(2)
    # Binary: |00> -> index 0
    # Binary: |10> -> index 2 (if qubit 1 is the most significant bit, 2^1 = 2)
    assert np.isclose(engine.state[0], expected_amplitude)
    assert np.isclose(engine.state[2], expected_amplitude)
