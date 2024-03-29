"""
**Contains**

* Medium
"""

from __future__ import division
from ..units import second, meter, kilogram, ampere

__all__ = ['Medium']

from ... import Symbol, sympify, sqrt
from ..units import speed_of_light, u0, e0


c = speed_of_light.convert_to(meter/second)
_e0mksa = e0.convert_to(ampere**2*second**4/(kilogram*meter**3))
_u0mksa = u0.convert_to(meter*kilogram/(ampere**2*second**2))


class Medium(Symbol):

    """
    This class represents an optical medium. The prime reason to implement this is
    to facilitate refraction, Fermat's priciple, etc.

    An optical medium is a material through which electromagnetic waves propagate.
    The permittivity and permeability of the medium define how electromagnetic
    waves propagate in it.


    Parameters
    ==========

    name: string
        The display name of the Medium.

    permittivity: Sympifyable
        Electric permittivity of the space.

    permeability: Sympifyable
        Magnetic permeability of the space.

    n: Sympifyable
        Index of refraction of the medium.


    Examples
    ========

    >>> from ...abc import epsilon, mu
    >>> from ..optics import Medium
    >>> m1 = Medium('m1')
    >>> m2 = Medium('m2', epsilon, mu)
    >>> m1.intrinsic_impedance
    149896229*pi*kilogram*meter**2/(1250000*ampere**2*second**3)
    >>> m2.refractive_index
    299792458*meter*sqrt(epsilon*mu)/second


    References
    ==========

    .. [1] http://en.wikipedia.org/wiki/Optical_medium

    """

    def __new__(cls, name, permittivity=None, permeability=None, n=None):
        obj = super(Medium, cls).__new__(cls, name)
        obj._permittivity = sympify(permittivity)
        obj._permeability = sympify(permeability)
        obj._n = sympify(n)
        if n is not None:
            if permittivity != None and permeability == None:
                obj._permeability = n**2/(c**2*obj._permittivity)
            if permeability != None and permittivity == None:
                obj._permittivity = n**2/(c**2*obj._permeability)
            if permittivity != None and permittivity != None:
                if abs(n - c*sqrt(obj._permittivity*obj._permeability)) > 1e-6:
                   raise ValueError("Values are not consistent.")
        elif permittivity is not None and permeability is not None:
            obj._n = c*sqrt(permittivity*permeability)
        elif permittivity is None and permeability is None:
            obj._permittivity = _e0mksa
            obj._permeability = _u0mksa
        return obj

    @property
    def intrinsic_impedance(self):
        """
        Returns intrinsic impedance of the medium.

        The intrinsic impedance of a medium is the ratio of the
        transverse components of the electric and magnetic fields
        of the electromagnetic wave travelling in the medium.
        In a region with no electrical conductivity it simplifies
        to the square root of ratio of magnetic permeability to
        electric permittivity.

        Examples
        ========

        >>> from ..optics import Medium
        >>> m = Medium('m')
        >>> m.intrinsic_impedance
        149896229*pi*kilogram*meter**2/(1250000*ampere**2*second**3)

        """
        return sqrt(self._permeability/self._permittivity)

    @property
    def speed(self):
        """
        Returns speed of the electromagnetic wave travelling in the medium.

        Examples
        ========

        >>> from ..optics import Medium
        >>> m = Medium('m')
        >>> m.speed
        299792458*meter/second

        """
        return 1/sqrt(self._permittivity*self._permeability)

    @property
    def refractive_index(self):
        """
        Returns refractive index of the medium.

        Examples
        ========

        >>> from ..optics import Medium
        >>> m = Medium('m')
        >>> m.refractive_index
        1

        """
        return (c/self.speed)

    @property
    def permittivity(self):
        """
        Returns electric permittivity of the medium.

        Examples
        ========

        >>> from ..optics import Medium
        >>> m = Medium('m')
        >>> m.permittivity
        625000*ampere**2*second**4/(22468879468420441*pi*kilogram*meter**3)

        """
        return self._permittivity

    @property
    def permeability(self):
        """
        Returns magnetic permeability of the medium.

        Examples
        ========

        >>> from ..optics import Medium
        >>> m = Medium('m')
        >>> m.permeability
        pi*kilogram*meter/(2500000*ampere**2*second**2)

        """
        return self._permeability

    def __str__(self):
        from ...printing import sstr
        return type(self).__name__ + sstr(self.args)

    def __lt__(self, other):
        """
        Compares based on refractive index of the medium.
        """
        return self.refractive_index < other.refractive_index

    def __gt__(self, other):
        return not self.__lt__(other)

    def __eq__(self, other):
        return self.refractive_index == other.refractive_index

    def __ne__(self, other):
        return not self.__eq__(other)
