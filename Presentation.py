# -*- coding: utf-8 -*-
"""
Created on Fri Feb 19 13:47:29 2021

@author: mikva
"""
import QuantumCircuit
import numpy as np
import matplotlib.pyplot as plt
import QuantumRegister
import sparse
import math
import array_to_latex as a2l

def diffuser(circuit):
    """
    Creates the diffuser for a given circuit for a Grover's algorithm.

    Parameters
    ----------
    circuit : QuantumCircuit
        The quantum circuit that Grover's algorithm should be applied to.

    Returns
    -------
    None.

    """
    n_qubits = len(circuit.register.Qbits)
    
    # Apply h gates to all qubits
    for qbit in range(n_qubits):
        circuit.addGate('h', [qbit])
    # Apply x gates to all qubits
    for qbit in range(n_qubits):
        circuit.addGate('x', [qbit])
    
    circuit.ncz([i for i in range(n_qubits)])
    
    # Apply x gates to all qubits
    for qbit in range(n_qubits):
        circuit.addGate('x', [qbit])
    
    # Apply h gates to all qubits
    for qbit in range(n_qubits):
        circuit.addGate('h', [qbit])
    

def Grover_Circuit(n_qubits, measured_bits):
    """
    Constructs a circuit representing Grover's algorithm for a given number of qubits and
    bits that we are interested in. Plots measurements after each iteration of the algorithm.

    Parameters
    ----------
    n_qubits : int
        Number of qubits in the circuit.
    measured_bits : list
        list of bits that we are interested in and want to increase the amplitude of.

    Returns
    -------
    None.
    """
    grover_circuit = QuantumCircuit.QuantumCircuit(n_qubits)
    grover_circuit.addGate('h', [i for i in range(n_qubits)])
    repetitions = round(np.sqrt(n_qubits/len(measured_bits))) - 1
    
    grover_circuit.addmeasure()
    # calculate oracle
    elements = []
    for i in range(2**n_qubits):
        if i in measured_bits:
            elements.append(sparse.MatrixElement(i,i,-1))
        else: elements.append(sparse.MatrixElement(i,i,1))
    oracle_gate = sparse.SparseMatrix(2**n_qubits, elements) # Creates a sparseMatrix representation of the oracle
    #print(oracle_gate.makedense())
    
    #Add Oracle
    grover_circuit.addCustom(0, n_qubits-1, oracle_gate, 'oracle')
    
    #grover_circuit.addmeasure()
    #Add diffuser
    diffuser(grover_circuit)

    grover_circuit.addmeasure()
    # Repeat if necessary
    for i in range(repetitions):
        # Add Oracle
        grover_circuit.addCustom(0, n_qubits-1, oracle_gate, 'oracle')
        #Add diffuser
        diffuser(grover_circuit)
        grover_circuit.addmeasure()

    #a2l.to_ltx(np.array(grover_circuit.gates, dtype=object))
    print(np.array(grover_circuit.gates, dtype=object)[:,:6])

    #show results
    final_statevec, measurements = grover_circuit.simulate2()
    #for m in measurements[1]:
    #   print(m)
    
    # plots the results in a snazzy way
    figure, axis = plt.subplots(1, len(measurements[1]))
    for j, measurement in enumerate(measurements[1]):
        axis[j].bar([i for i in range(measurement.size)], measurement*np.conj(measurement))
        axis[j].set_ylim([0,1])
        axis[j].set_xlabel("State |N>", fontsize = '13')
        if j>0:
            axis[j].set_yticklabels("")
        #print((results[2][1][j]*np.conj(results[2][1][j])).sum())
    axis[0].set_ylabel("Probability", fontsize = '13')
    
    #figure.set_ylabel("Probability of Measuring State")
    figure.suptitle("Probability of measuring state N",fontweight='bold', fontsize='15')
    plt.show()
    
    
def QFT(circuit):
    """
    Applies quantum fourier transform to a circuit.

    Parameters
    ----------
    circuit : QuantumCircuit
        The quantum circuit to apply the QFT to.

    Returns
    -------
    circuit : QuantumCircuit
        The same quantum circuit with the QFT applied to it.

    """
    n = len(circuit.register.Qbits)
    
    def qft_rotations(circuit, n):
        """
        Calculates the roatation gates and hadamards that must be added to the circuit.

        Parameters
        ----------
        circuit : QuantumCircuit
            The circuit that the gft will be applied to.
        n : int
            Number of qubits in the circuit.

        Returns
        -------
        None.

        """
        if n==0: return circuit
        n -= 1
        circuit.addGate('h', [n])
        for qbit in range(n):
            circuit.addBigGate(('cp', qbit, n, np.pi/2**(n-qbit)))
        qft_rotations(circuit, n)
    
    def swap_registers(circuit, n):
        for qbit in range(n//2):
            circuit.addBigGate(('swap', qbit, n-qbit-1))
        return circuit
    
    def qft(circuit, n):
        qft_rotations(circuit, n)
        swap_registers(circuit, n)
        return circuit
    
    qft(circuit, n)
    
def qft_dagger(circuit):
    """
    Applies an inverse quantum fourier transform to a given circuit.

    Parameters
    ----------
    circuit : QuantumCircuit
        A quantum circuit that the inverse qft should be applied to.

    Returns
    -------
    circuit : QuantumCircuit
        The same circuit, but with an inverse qft applied to it.

    """
    n = len(circuit.register.Qbits)
    
    #swap qbits
    for qbit in range(n//2):
        circuit.swap(qbit, n-qbit-1)
    for j in range(n):
        for m in range(j):
            circuit.cp(m, j, -np.pi/float(2**(j-m)))
        circuit.addGate('h', [j])
    return circuit

def Ber_Vaz(s):
    """
    Creates an example of the Bernstein-Vazirani algorithm.

    Parameters
    ----------
    s : string
        String representation of the state that the algorithm should work for.

    Returns
    -------
    None.

    """
    n=len(s)
    bv_circ = QuantumCircuit.QuantumCircuit(n+1)
    
    # Put ancilla in state |->
    bv_circ.addGate('h', [n])
    bv_circ.addGate('z', [n])
    
    # Apply hadamard gates before querying the oracle
    bv_circ.addGate('h', [i for i in range(n)])
    
    #Apply the inner product oracle
    s = s[::-1] # reverse s to match qubit ordering
    for q in range(n):
        if s[q] == '1': bv_circ.addBigGate(('cn', q, n))
        
    # Apply Hadamard after the oracle
    bv_circ.addGate('h', [i for i in range(n)])
    
    bv_circ.show()
    #bv_circ.register.measure()
    
    short_register = QuantumRegister.QuantumRegister(n)
    short_register.setStateVec(bv_circ.register.Statevec.Elements[:2**n])
    short_register.measure()
    
    
    print('Qubits of the Bernstein-Vazirani circuit:')
    for i, qbit in enumerate(bv_circ.register.Qbits):
        print(f'Qubit {i}')
        print(qbit)
    
    print('Shortened register represented by:')
    print(short_register)
    print('Qubits of the shortened registered')
    for i, qbit in enumerate(short_register.Qbits):
        print(f'Qubit {i}')
        print(qbit)
    
    
def qft_example():
    """
    Create an example demonstrating quantum fourier transform.

    Returns
    -------
    None.

    """
    circuit = QuantumCircuit.QuantumCircuit(3) # Create circuit
    circuit.addGate('x', [2,1]) # Set the state vector to a specific superposition
    circuit.addGate('h', [0,2])
    circuit.addBigGate(('cn', 0, 2))
    circuit.addmeasure()
    QFT(circuit)
    circuit.addmeasure()
    qft_dagger(circuit)
    circuit.addmeasure()
    results = circuit.simulate(return_full=True)
    
    print(np.array(circuit.gates)[:, :12])
    
    for i, measurement in enumerate(results[2][1]):
        print(f'Measurement {i}')
        print(measurement)
        
    figure, axis = plt.subplots(1, len(results[2][1]))
    for j in range(len(results[2][1])):
        axis[j].bar([i for i in range(results[2][1][j].size)], results[2][1][j])
        axis[j].set_ylim([-1,1])
        print((results[2][1][j]*np.conj(results[2][1][j])).sum())
    
    circuit = QuantumCircuit.QuantumCircuit(4)
    circuit.addGate('x', [2,1])
    circuit.addmeasure()
    QFT(circuit)
    circuit.addmeasure()
    qft_dagger(circuit)
    circuit.addmeasure()
    results = circuit.simulate(return_full=True)
    
    for i, measurement in enumerate(results[2][1]):
        print(f'Measurement {i}')
        print(measurement)
        
    figure, axis = plt.subplots(1, len(results[2][1]))
    for j in range(len(results[2][1])):
        axis[j].bar([i for i in range(results[2][1][j].size)], results[2][1][j])
        axis[j].set_ylim([-1,1])
        print((results[2][1][j]*np.conj(results[2][1][j])).sum())