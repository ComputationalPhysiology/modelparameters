from __future__ import print_function, division

from ...core.sympify import _sympify
from ...core import S, Basic

from .matexpr import ShapeError
from .matpow import MatPow


class Inverse(MatPow):
    """
    The multiplicative inverse of a matrix expression

    This is a symbolic object that simply stores its argument without
    evaluating it. To actually compute the inverse, use the ``.inverse()``
    method of matrices.

    Examples
    ========

    >>> from ... import MatrixSymbol, Inverse
    >>> A = MatrixSymbol('A', 3, 3)
    >>> B = MatrixSymbol('B', 3, 3)
    >>> Inverse(A)
    A^-1
    >>> A.inverse() == Inverse(A)
    True
    >>> (A*B).inverse()
    B^-1*A^-1
    >>> Inverse(A*B)
    (A*B)^-1

    """
    is_Inverse = True
    exp = S(-1)

    def __new__(cls, mat):
        mat = _sympify(mat)
        if not mat.is_Matrix:
            raise TypeError("mat should be a matrix")
        if not mat.is_square:
            raise ShapeError("Inverse of non-square matrix %s" % mat)
        return Basic.__new__(cls, mat)

    @property
    def arg(self):
        return self.args[0]

    @property
    def shape(self):
        return self.arg.shape

    def _eval_inverse(self):
        return self.arg

    def _eval_determinant(self):
        from .determinant import det
        return 1/det(self.arg)

    def doit(self, **hints):
        if hints.get('deep', True):
            return self.arg.doit(**hints).inverse()
        else:
            return self.arg.inverse()


from ...assumptions.ask import ask, Q
from ...assumptions.refine import handlers_dict


def refine_Inverse(expr, assumptions):
    """
    >>> from ... import MatrixSymbol, Q, assuming, refine
    >>> X = MatrixSymbol('X', 2, 2)
    >>> X.I
    X^-1
    >>> with assuming(Q.orthogonal(X)):
    ...     print(refine(X.I))
    X.T
    """
    if ask(Q.orthogonal(expr), assumptions):
        return expr.arg.T
    elif ask(Q.unitary(expr), assumptions):
        return expr.arg.conjugate()
    elif ask(Q.singular(expr), assumptions):
        raise ValueError("Inverse of singular matrix %s" % expr.arg)

    return expr

handlers_dict['Inverse'] = refine_Inverse
