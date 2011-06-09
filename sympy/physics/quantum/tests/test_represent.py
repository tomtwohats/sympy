from sympy import Matrix, I, Float, Integer, symbols

from sympy.physics.quantum.dagger import Dagger
from sympy.physics.quantum.represent import represent, rep_innerproduct, rep_expectation
from sympy.physics.quantum.state import Bra, Ket
from sympy.physics.quantum.operator import Operator, OuterProduct
from sympy.physics.quantum.tensorproduct import TensorProduct
from sympy.physics.quantum.tensorproduct import matrix_tensor_product
from sympy.physics.quantum.commutator import Commutator
from sympy.physics.quantum.anticommutator import AntiCommutator
from sympy.physics.quantum.innerproduct import InnerProduct
from sympy.physics.quantum.matrixutils import (
    to_sympy, to_numpy, to_scipy_sparse, numpy_ndarray, scipy_sparse_matrix
)
from sympy.physics.quantum.cartesian import XKet, XOp, XBra
from sympy.physics.quantum.qapply import qapply

from sympy.external import import_module
from sympy.utilities.pytest import skip

Amat = Matrix([[1,I],[-I,1]])
Bmat = Matrix([[1,2],[3,4]])
Avec = Matrix([[1],[I]])

class AKet(Ket):

    @property
    def dual_class(self):
        return ABra

    def _represent_default_basis(self, **options):
        return self._represent_AOp(None, **options)

    def _represent_AOp(self, basis, **options):
        return Avec


class ABra(Bra):

    @property
    def dual_class(self):
        return AKet


class AOp(Operator):

    def _represent_default_basis(self, **options):
        return self._represent_AOp(None, **options)

    def _represent_AOp(self, basis, **options):
        return Amat


class BOp(Operator):

    def _represent_default_basis(self, **options):
        return self._represent_AOp(None, **options)

    def _represent_AOp(self, basis, **options):
        return Bmat


k = AKet('a')
b = ABra('a')
A = AOp('A')
B = BOp('B')

_tests = [
    # Bra
    (b, Dagger(Avec)),
    (Dagger(b), Avec),
    # Ket
    (k, Avec),
    (Dagger(k), Dagger(Avec)),
    # Operator
    (A, Amat),
    (Dagger(A), Dagger(Amat)),
    # OuterProduct
    (OuterProduct(k,b), Avec*Avec.H),
    # TensorProduct
    (TensorProduct(A,B), matrix_tensor_product(Amat,Bmat)),
    # Pow
    (A**2, Amat**2),
    # Add/Mul
    (A*B + 2*A, Amat*Bmat + 2*Amat),
    # Commutator
    (Commutator(A,B), Amat*Bmat - Bmat*Amat),
    # AntiCommutator
    (AntiCommutator(A,B), Amat*Bmat + Bmat*Amat),
    # InnerProduct
    (InnerProduct(b,k), (Avec.H*Avec)[0])
]


def test_format_sympy():
    for test in _tests:
        lhs = represent(test[0], basis=A, format='sympy')
        rhs = to_sympy(test[1])
        assert lhs == rhs

def test_scalar_sympy():
    assert represent(Integer(1)) == Integer(1)
    assert represent(Float(1.0)) == Float(1.0)
    assert represent(1.0+I) == 1.0+I


np = import_module('numpy', min_python_version=(2, 6))

def test_format_numpy():
    if not np:
        skip("numpy not installed or Python too old.")

    for test in _tests:
        lhs = represent(test[0], basis=A, format='numpy')
        rhs = to_numpy(test[1])
        if isinstance(lhs, numpy_ndarray):
            assert (lhs == rhs).all()
        else:
            assert lhs == rhs

def test_scalar_numpy():
    if not np:
        skip("numpy not installed or Python too old.")

    assert represent(Integer(1), format='numpy') == 1
    assert represent(Float(1.0), format='numpy') == 1.0
    assert represent(1.0+I, format='numpy') == 1.0+1.0j


scipy = import_module('scipy', __import__kwargs={'fromlist':['sparse']})

def test_format_scipy_sparse():
    if not np:
        skip("numpy not installed or Python too old.")
    if not scipy:
        skip("scipy not installed.")

    for test in _tests:
        lhs = represent(test[0], basis=A, format='scipy.sparse')
        rhs = to_scipy_sparse(test[1])
        if isinstance(lhs, scipy_sparse_matrix):
            assert np.linalg.norm((lhs-rhs).todense()) == 0.0
        else:
            assert lhs == rhs

def test_scalar_scipy_sparse():
    if not np:
        skip("numpy not installed or Python too old.")
    if not scipy:
        skip("scipy not installed.")

    assert represent(Integer(1), format='scipy.sparse') == 1
    assert represent(Float(1.0), format='scipy.sparse') == 1.0
    assert represent(1.0+I, format='scipy.sparse') == 1.0+1.0j

x_ket = XKet('x')
x_bra = XBra('x')
x_op = XOp('X')

def test_innerprod_represent():
    assert rep_innerproduct(x_ket) == InnerProduct(XBra(), x_ket).doit()
    assert rep_innerproduct(x_bra) == InnerProduct(x_bra, XKet()).doit()

    try:
        test = rep_innerproduct(x_op)
    except TypeError:
        return True

def test_operator_represent():
    basis_kets = x_op._get_basis_kets(2)
    assert rep_expectation(x_op) == qapply(basis_kets[1].dual*x_op*basis_kets[0])
