# -*- coding: utf-8 -*-
"""
Created on Wed Feb 17 14:59:09 2021

@author: mikva
"""
import numpy as np
import sparse

class Simulator():
    def __init__(self, gates, register, custom, measurements):
        self.gates = gates
        self.register = register
        self.singlegates = {'x' : np.array([[0,1], [1,0]]),
                      'y' : np.array([[0,-1j], [1j,0]]),
                      'z' : np.array([[1,0], [0,-1]]),
                      'h' : np.array([[1,1],[1,-1]])/np.sqrt(2),
                      'p' : np.array([[1,0],[0,1j]]),
                      't' : np.array([[1,0],[0,np.exp(1j*np.pi/4)]]),
                      'i' : np.eye(2)
                      }
        self.customgates = custom
        self.measurements = [measurements, []]

    def bitactive(self, n, bit):
        """
        Checks whether a given integer has a particular bit active

        Parameters
        ----------
        n : int
            Integer to check
        bit : int
            The position of the bit to check

        Returns
        -------
        boolean
            True of bit is active, false if not

        """
        return ((n>>(bit)) & 1) == 1
        
    def toggle(self, n, bit):
        """
        Toggles a specific bit in an integer

        Parameters
        ----------
        n : int
            Integer to toggle
        bit : int
            The position of the bit to toggle

        Returns
        -------
        int
            The new integer created by toggling the bit

        """
        return n ^ (1 << bit)
    
    def cNot(self, gate_info):
        """
        Creates an arbitrary sized controlled not gate between two arbitrary qbits.
        
        Parameters
        ----------
        qbit1 : int
            Position in the circuit of the control qubit
        qbit2 : int
            Position in the circuit of the controlled qubit
    
        Returns
        -------
        SparseMatrix
            The cnot gate entangling the two qubits given.
            """
        qbit1, qbit2 = gate_info
            
        if qbit1>qbit2:
            control_bit = np.abs(qbit2-qbit1)
            controlled_bit = 0
        else:
            control_bit = 0
            controlled_bit = qbit2 - qbit1
            
        elements = [sparse.MatrixElement(0,0,1)]
        dimension = 2**(np.abs(qbit2-qbit1)+1)
        for i in range(1, dimension):
            if self.bitactive(i, control_bit):
                col = self.toggle(i, controlled_bit)
                elements.append(sparse.MatrixElement(i, col, 1))
            else: elements.append(sparse.MatrixElement(i,i,1))
        return sparse.SparseMatrix(dimension, elements)
    
    def ccNot(self, gate_info):
        """
        Creates a sparsematrix representing the controlled-controlled-not (ccnot or Tiffoli) 
        gate for the given qubits. Can be applied to any exisiting qubits.
        
        Parameters
        ----------
        control1 : int
            first qubit controlling the gate
        control2 : int
            second qubit controlling the gate
        qbit3 : int
            The qubit to be controlled by the other two
    
        Returns
        -------
        SparseMatrix
            Matrix representation of the gate
    
        """
        control1, control2, qbit3 = gate_info
        # Reset the values to range from 0 to maxval
        minval = min(control1, control2, qbit3)
        maxval = max(control1, control2, qbit3) - minval
        control1 = control1 - minval
        control2 = control2 - minval
        qbit3 = qbit3 - minval
            
        # Create elements and calculate dimensions
        elements = [sparse.MatrixElement(0,0,1)]
        dimension = 2**(maxval+1)
            
        # For each possible bit check whether the control qubits are active
        for i in range(1, dimension):
            if self.bitactive(i, control1) and self.bitactive(i, control2):
                # if control qubits are active, calculate the new value and insert into matrix
                col = self.toggle(i, qbit3)
                elements.append(sparse.MatrixElement(i, col, 1))
            else: elements.append(sparse.MatrixElement(i,i,1))
        return sparse.SparseMatrix(dimension, elements)
    
    def cZ(self, gate_info):
        """
        Creates a controlled z gate given 2 qubits
    
        Parameters
        ----------
        gate_info : tuple(int, int)
            The two gates to control the z
    
        Returns
        -------
        SparseMatrix
            Representation of the cz gate
        """
        qbit1, qbit2 = gate_info
        shift = min(qbit1, qbit2)
        qbit1 = qbit1 - shift
        qbit2 = qbit2 - shift
            
        elements = [sparse.MatrixElement(0,0,1)]
        dimension = 2**(np.abs(qbit2-qbit1)+1)
        for i in range(1, dimension):
            if self.bitactive(i, qbit1) and self.bitactive(i, qbit2):
                elements.append(sparse.MatrixElement(i, i, -1))
            else: elements.append(sparse.MatrixElement(i,i,1))
        return sparse.SparseMatrix(dimension, elements)
    
    def cP(self, gate_info):
        """
        Creates a controlled phase gate for the given qubits
    
        Parameters
        ----------
        gate_info : tuple(int, int, float)
            The information supplied to the gate. Control qubits as ints, float as the phase.
    
        Returns
        -------
        SparseMatrix
            Representation of the cp gate
    
        """
        qbit1, qbit2, phi = gate_info
        
        elements = [sparse.MatrixElement(0,0,1)]
        dimension = 2**(np.abs(qbit2-qbit1)+1)
        for i in range(1, dimension):
            if self.bitactive(i, qbit1) and self.bitactive(i, qbit2):
                elements.append(sparse.MatrixElement(i, i, np.exp(1j*phi)))
            else: elements.append(sparse.MatrixElement(i,i,1))
        return sparse.SparseMatrix(dimension, elements)
        
    def NCP(self, gate_info):
        """
        Adds a phase gate controlled by an arbitrary number of bits
    
        Parameters
        ----------
        gate_info : tuple(int, int, int..., float)
            Control qubits as ints, phase as a float
    
        Returns
        -------
        SparseMatrix
            Matrix representatin of the gate
        """
        bits = np.array(gate_info[:-1])
        bits = bits - min(bits)
        phi = gate_info[-1]
        
        elements = [sparse.MatrixElement(0,0,1)]
        dimension = 2**(max(bits)-min(bits)+1)
        for i in range(1, dimension):
            active = True
            for bit in bits:
                if not self.bitactive(i, bit):
                    active = False
                    break
            if active: elements.append(sparse.MatrixElement(i, i, np.exp(1j*phi)))
            else: elements.append(sparse.MatrixElement(i, i, 1))
        return sparse.SparseMatrix(dimension, elements)
    
    def NCZ(self, gate_info):
        """
        Adds a z gate controlled by an arbitrary number of bits
    
        Parameters
        ----------
        gate_info : tuple(int, int, int...,)
            Control qubits as ints, arbitrary number
    
        Returns
        -------
        SparseMatrix
            Matrix representatin of the gate
        """
        bits = np.array(gate_info)
        bits = bits - min(bits)
        
        elements = [sparse.MatrixElement(0,0,1)]
        dimension = 2**(max(bits)-min(bits)+1)
        for i in range(1, dimension):
            active = True
            for bit in bits:
                if not self.bitactive(i, bit):
                    active = False
                    break
            if active: elements.append(sparse.MatrixElement(i, i, -1))
            else: elements.append(sparse.MatrixElement(i, i, 1))
        return sparse.SparseMatrix(dimension, elements)
    
    def Swap(self, gate_info):
        """
        Creates the matrix representing the swap operation between two qubits.
    
        Parameters
        ----------
        gate_info : tuple(int, int)
            The two gates to be swapped.
    
        Returns
        -------
        SparseMatrix
            Matrix representation of the swap gate.
    
        """
        qbit1, qbit2 = gate_info
        shift = min(qbit1, qbit2)
        qbit1 = qbit1 - shift
        qbit2 = qbit2 - shift
        elements = []
        dimension = 2**(np.abs(qbit2-qbit1)+1)
        for i in range(0, dimension):
            col = i
            if (self.bitactive(i, qbit1) and not self.bitactive(i, qbit2)) or (not self.bitactive(i, qbit1) and self.bitactive(i, qbit2)):
                col = self.toggle(self.toggle(i, qbit1), qbit2)
            elements.append(sparse.MatrixElement(i, col, 1))
            
        return sparse.SparseMatrix(dimension, elements)
    
    def addLargeGate(self, gate_info):
        """
        Helper function for makeMatrices(). Calls the creators for the larger gates based
        info provided.
    
        Parameters
        ----------
        gate_info : tuple
            information concerning the gate
    
        Returns
        -------
        operation : SparseMatrix
            MAtrix representation of the operation for the gates given.
    
        """
        #print(gate_info)
        if gate_info[0]=='r':
            operation = self.Rt(complex(gate_info[1]))
        elif gate_info[0]=='cn':
            operation = self.cNot(gate_info[1:])
        elif gate_info[0]=='ccn':
            operation = self.ccNot(gate_info[1:])
        elif gate_info[0]=='swap':
            operation = self.Swap(gate_info[1:])
        elif gate_info[0]=='cz':
            operation = self.cZ(gate_info[1:])
        elif gate_info[0]=='cp':
            operation = self.cP(gate_info[1:])
        elif gate_info[0]=='ncp':
            operation = self.NCP(gate_info[1:])
        elif gate_info[0]=='ncz':
            operation = self.NCZ(gate_info[1:])
        elif gate_info[0]=='custom':
            operation = self.customgates[gate_info[-1]]
        
            
        return operation
        
    def makeMatrices(self):
        # We should make sparse matrix representations of single gates from the beginning.
        """
        Creates the matrices that will be applied to the wavevector
    
        Returns
        -------
        bigmats : numpy array
            list of np matrices that will be applied to the statevector
    
        """
        gates = np.array(self.gates, dtype = object).T
        #debug
        #print('Gates are:')
        #print(gates)
            
        bigmats = []
        for i, slot in enumerate(gates):
            bigmat = sparse.SparseMatrix(1, [sparse.MatrixElement(0,0,1)])
            for j in slot:
                if type(j)==tuple:
                    bigmat = self.addLargeGate(j).tensorProduct(bigmat)
                elif j == 's': continue
                else: 
                    bigmat = sparse.makesparse(self.singlegates[j]).tensorProduct(bigmat)
            bigmats.append(bigmat)
            
        return np.array(bigmats)
        
    def Rt(self, theta):
        """
        Creates an r gate with the given phase
    
        Parameters
        ----------
        theta : float
            The angle in radians which the qubit should be rotated by.
    
        Returns
        -------
        SparseMatrix
            Matrix representation of the r gate.
    
        """
        return sparse.makesparse(np.array([[1, 0], [0, np.exp(1j*theta)]], dtype=complex))
    
    def simulate(self, return_full = False):
        """
        Applies the circuit to the initialized statevector
    
        Returns
        -------
        The register
        if return_full:
            the register, operations and any measurements.
            
        """
        operations = self.makeMatrices()
        for i, operation in enumerate(operations):
            #print(i)
            #print(operation)
            self.register.Statevec = operation.apply(self.register.Statevec)
            if i in self.measurements[0]:
                self.measurements[1].append(self.register.Statevec.Elements)
            
        if return_full: return self.register, operations, self.measurements
        return self.register
    
    def simulate2(self):
        """
        Applies the circuit to the initialized statevector without storing the operations
    
        Returns
        -------
        The register and any measurements made
            
        """
        gates = np.array(self.gates, dtype = object).T
        #debug
        #print('Gates are:')
        #print(gates)
        
        for i, slot in enumerate(gates):
            bigmat = sparse.SparseMatrix(1, [sparse.MatrixElement(0,0,1)])
            for j in slot:
                if type(j)==tuple:
                    bigmat = self.addLargeGate(j).tensorProduct(bigmat)
                elif j == 's': continue
                else: 
                    bigmat = sparse.makesparse(self.singlegates[j]).tensorProduct(bigmat)
            self.register.Statevec = bigmat.apply(self.register.Statevec)
            if i in self.measurements[0]:
                self.measurements[1].append(self.register.Statevec.Elements)
        
        return self.register, self.measurements