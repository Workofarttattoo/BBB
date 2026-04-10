import pytest
import numpy as np
from src.blank_business_builder.quantum_stack_optimizer import QuantumStateEngine

def test_measure_initial_state():
    """Test measurement of the initial |0...0> state."""
    # 2 qubits -> 4 states (0, 1, 2, 3)
    engine = QuantumStateEngine(2)

    # Initial state is |00>, so probability of 0 is 1.0
    for _ in range(10):
        assert engine.measure() == 0

def test_measure_deterministic_state():
    """Test measurement of a specific deterministic state."""
    engine = QuantumStateEngine(3)

    # Manually set state to |011> (state 3)
    engine.state = np.zeros(engine.num_states, dtype=complex)
    engine.state[3] = 1.0

    for _ in range(10):
        assert engine.measure() == 3

def test_measure_superposition():
    """Test measurement of a superposition state."""
    # Use 1 qubit -> 2 states (0, 1)
    engine = QuantumStateEngine(1)

    # Apply Hadamard gate to create |+> state: (|0> + |1>) / sqrt(2)
    engine.hadamard(0)

    # Measure multiple times
    num_measurements = 1000
    results = [engine.measure() for _ in range(num_measurements)]

    # We expect roughly 50% 0s and 50% 1s
    count_0 = results.count(0)
    count_1 = results.count(1)

    assert count_0 + count_1 == num_measurements
    # Use a generous tolerance for the random distribution (e.g., +/- 10%)
    assert 400 < count_0 < 600
    assert 400 < count_1 < 600

def test_measure_return_type_and_bounds():
    """Test that measurement returns an integer within expected bounds."""
    num_qubits = 4
    engine = QuantumStateEngine(num_qubits)

    # Apply some gates to mix things up
    engine.hadamard(0)
    engine.hadamard(1)
    engine.cnot(0, 2)

    for _ in range(50):
        result = engine.measure()
        assert isinstance(result, (int, np.integer))
        assert 0 <= result < engine.num_states
