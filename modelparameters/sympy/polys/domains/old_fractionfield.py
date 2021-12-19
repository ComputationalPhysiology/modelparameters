"""Implementation of :class:`FractionField` class. """

from __future__ import print_function, division

from .field import Field
from .compositedomain import CompositeDomain
from .characteristiczero import CharacteristicZero

from ..polyclasses import DMF
from ..polyerrors import GeneratorsNeeded
from ..polyutils import dict_from_basic, basic_from_dict, _dict_reorder

from ...utilities import public

@public
class FractionField(Field, CharacteristicZero, CompositeDomain):
    """A class for representing rational function fields. """

    dtype = DMF
    is_FractionField = is_Frac = True

    has_assoc_Ring = True
    has_assoc_Field = True

    def __init__(self, dom, *gens):
        if not gens:
            raise GeneratorsNeeded("generators not specified")

        lev = len(gens) - 1
        self.ngens = len(gens)

        self.zero = self.dtype.zero(lev, dom, ring=self)
        self.one = self.dtype.one(lev, dom, ring=self)

        self.domain = self.dom = dom
        self.symbols = self.gens = gens

    def new(self, element):
        return self.dtype(element, self.dom, len(self.gens) - 1, ring=self)

    def __str__(self):
        return str(self.dom) + '(' + ','.join(map(str, self.gens)) + ')'

    def __hash__(self):
        return hash((self.__class__.__name__, self.dtype, self.dom, self.gens))

    def __eq__(self, other):
        """Returns ``True`` if two domains are equivalent. """
        return isinstance(other, FractionField) and \
            self.dtype == other.dtype and self.dom == other.dom and self.gens == other.gens

    def to_sympy(self, a):
        """Convert ``a`` to a SymPy object. """
        return (basic_from_dict(a.numer().to_sympy_dict(), *self.gens) /
                basic_from_dict(a.denom().to_sympy_dict(), *self.gens))

    def from_sympy(self, a):
        """Convert SymPy's expression to ``dtype``. """
        p, q = a.as_numer_denom()

        num, _ = dict_from_basic(p, gens=self.gens)
        den, _ = dict_from_basic(q, gens=self.gens)

        for k, v in num.items():
            num[k] = self.dom.from_sympy(v)

        for k, v in den.items():
            den[k] = self.dom.from_sympy(v)

        return self((num, den)).cancel()

    def from_ZZ_python(K1, a, K0):
        """Convert a Python ``int`` object to ``dtype``. """
        return K1(K1.dom.convert(a, K0))

    def from_QQ_python(K1, a, K0):
        """Convert a Python ``Fraction`` object to ``dtype``. """
        return K1(K1.dom.convert(a, K0))

    def from_ZZ_gmpy(K1, a, K0):
        """Convert a GMPY ``mpz`` object to ``dtype``. """
        return K1(K1.dom.convert(a, K0))

    def from_QQ_gmpy(K1, a, K0):
        """Convert a GMPY ``mpq`` object to ``dtype``. """
        return K1(K1.dom.convert(a, K0))

    def from_RealField(K1, a, K0):
        """Convert a mpmath ``mpf`` object to ``dtype``. """
        return K1(K1.dom.convert(a, K0))

    def from_GlobalPolynomialRing(K1, a, K0):
        """Convert a ``DMF`` object to ``dtype``. """
        if K1.gens == K0.gens:
            if K1.dom == K0.dom:
                return K1(a.rep)
            else:
                return K1(a.convert(K1.dom).rep)
        else:
            monoms, coeffs = _dict_reorder(a.to_dict(), K0.gens, K1.gens)

            if K1.dom != K0.dom:
                coeffs = [ K1.dom.convert(c, K0.dom) for c in coeffs ]

            return K1(dict(zip(monoms, coeffs)))

    def from_FractionField(K1, a, K0):
        """
        Convert a fraction field element to another fraction field.

        Examples
        ========

        >>> from ..polyclasses import DMF
        >>> from ..domains import ZZ, QQ
        >>> from ...abc import x

        >>> f = DMF(([ZZ(1), ZZ(2)], [ZZ(1), ZZ(1)]), ZZ)

        >>> QQx = QQ.old_frac_field(x)
        >>> ZZx = ZZ.old_frac_field(x)

        >>> QQx.from_FractionField(f, ZZx)
        (x + 2)/(x + 1)

        """
        if K1.gens == K0.gens:
            if K1.dom == K0.dom:
                return a
            else:
                return K1((a.numer().convert(K1.dom).rep,
                           a.denom().convert(K1.dom).rep))
        elif set(K0.gens).issubset(K1.gens):
            nmonoms, ncoeffs = _dict_reorder(
                a.numer().to_dict(), K0.gens, K1.gens)
            dmonoms, dcoeffs = _dict_reorder(
                a.denom().to_dict(), K0.gens, K1.gens)

            if K1.dom != K0.dom:
                ncoeffs = [ K1.dom.convert(c, K0.dom) for c in ncoeffs ]
                dcoeffs = [ K1.dom.convert(c, K0.dom) for c in dcoeffs ]

            return K1((dict(zip(nmonoms, ncoeffs)), dict(zip(dmonoms, dcoeffs))))

    def get_ring(self):
        """Returns a ring associated with ``self``. """
        from ..domains import PolynomialRing
        return PolynomialRing(self.dom, *self.gens)

    def poly_ring(self, *gens):
        """Returns a polynomial ring, i.e. `K[X]`. """
        raise NotImplementedError('nested domains not allowed')

    def frac_field(self, *gens):
        """Returns a fraction field, i.e. `K(X)`. """
        raise NotImplementedError('nested domains not allowed')

    def is_positive(self, a):
        """Returns True if ``a`` is positive. """
        return self.dom.is_positive(a.numer().LC())

    def is_negative(self, a):
        """Returns True if ``a`` is negative. """
        return self.dom.is_negative(a.numer().LC())

    def is_nonpositive(self, a):
        """Returns True if ``a`` is non-positive. """
        return self.dom.is_nonpositive(a.numer().LC())

    def is_nonnegative(self, a):
        """Returns True if ``a`` is non-negative. """
        return self.dom.is_nonnegative(a.numer().LC())

    def numer(self, a):
        """Returns numerator of ``a``. """
        return a.numer()

    def denom(self, a):
        """Returns denominator of ``a``. """
        return a.denom()

    def factorial(self, a):
        """Returns factorial of ``a``. """
        return self.dtype(self.dom.factorial(a))