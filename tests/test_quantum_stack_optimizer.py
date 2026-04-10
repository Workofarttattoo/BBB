import pytest
import numpy as np
from src.blank_business_builder.quantum_stack_optimizer import QuantumStateEngine

def test_quantum_state_engine_cnot():
    """Test the CNOT gate in QuantumStateEngine."""
    # Initialize a 2-qubit system
    # States are: |00> (0), |01> (1), |10> (2), |11> (3)
    # The bitwise logic in cnot uses: (i >> control) & 1
    # So qubit 0 is the least significant bit
    qse = QuantumStateEngine(num_qubits=2)

    # State is initially |00> (index 0 is 1.0)
    assert qse.state[0] == 1.0

    # 1. Test when control is 0: target should not change
    # Apply CNOT with control=0, target=1
    # State is |00> (control is 0), so target stays 0 -> state stays |00>
    qse.cnot(0, 1)
    assert qse.state[0] == 1.0
    assert qse.state[1] == 0.0
    assert qse.state[2] == 0.0
    assert qse.state[3] == 0.0

    # 2. Test when control is 1: target should flip
    # Set the state to |01> (qubit 0 is 1, qubit 1 is 0)
    qse.state = np.zeros(4, dtype=complex)
    qse.state[1] = 1.0  # |01>

    # Apply CNOT with control=0, target=1
    # Since control is 1, target (qubit 1) should flip from 0 to 1
    # Result should be |11> (index 3)
    qse.cnot(0, 1)

    assert qse.state[0] == 0.0
    assert qse.state[1] == 0.0
    assert qse.state[2] == 0.0
    assert qse.state[3] == 1.0

    # 3. Test flipping from 1 back to 0
    # Set the state to |11> (qubit 0 is 1, qubit 1 is 1)
    qse.state = np.zeros(4, dtype=complex)
    qse.state[3] = 1.0  # |11>

    # Apply CNOT with control=0, target=1
    # Control is 1, target flips from 1 to 0
    # Result should be |01> (index 1)
    qse.cnot(0, 1)

    assert qse.state[0] == 0.0
    assert qse.state[1] == 1.0
    assert qse.state[2] == 0.0
    assert qse.state[3] == 0.0

    # 4. Test with superposition (entanglement creation)
    # State = 1/sqrt(2) * (|00> + |01>)
    qse.state = np.zeros(4, dtype=complex)
    qse.state[0] = 1/np.sqrt(2) # |00>
    qse.state[1] = 1/np.sqrt(2) # |01>

    # Apply CNOT with control=0, target=1
    # |00> stays |00>
    # |01> becomes |11>
    # So state becomes 1/sqrt(2) * (|00> + |11>) - a Bell state
    qse.cnot(0, 1)

    assert np.isclose(qse.state[0], 1/np.sqrt(2))
    assert qse.state[1] == 0.0
    assert qse.state[2] == 0.0
    assert np.isclose(qse.state[3], 1/np.sqrt(2))

def test_quantum_state_engine_cnot_reverse_control():
    """Test CNOT with control and target swapped."""
    qse = QuantumStateEngine(num_qubits=2)

    # Set state to |10> (index 2: qubit 0 is 0, qubit 1 is 1)
    qse.state = np.zeros(4, dtype=complex)
    qse.state[2] = 1.0

    # Apply CNOT with control=1, target=0
    # Control is 1, target flips from 0 to 1
    # Result should be |11> (index 3)
    qse.cnot(1, 0)

    assert qse.state[0] == 0.0
    assert qse.state[1] == 0.0
    assert qse.state[2] == 0.0
    assert qse.state[3] == 1.0

def test_quantum_state_engine_cnot_preserves_norm():
    """Test that CNOT preserves the norm of the state vector."""
    qse = QuantumStateEngine(num_qubits=3)

    # Create an arbitrary normalized state
    qse.state = np.array([0.1+0.1j, 0.2+0.2j, 0.3+0.3j, 0.4+0.4j,
                          0.1+0.0j, 0.0+0.1j, -0.2+0.1j, 0.1-0.2j], dtype=complex)
    # Normalize it
    norm = np.linalg.norm(qse.state)
    qse.state = qse.state / norm

    initial_norm = np.linalg.norm(qse.state)
    assert np.isclose(initial_norm, 1.0)

    qse.cnot(1, 2)

    final_norm = np.linalg.norm(qse.state)
    assert np.isclose(final_norm, 1.0)
