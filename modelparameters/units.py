from .sympytools import *


si_unit_map = {"ampere":"A", "becquerel":"Bq", "candela":"cd", "celsius":"gradC",
               "coulomb":"C","dimensionless":"1", "farad":"F", "gram":"g",
               "gray":"Gy", "henry":"H", "hertz":"Hz", "joule":"J", "katal":"kat",
               "kelvin":"K", "kilogram":"kg", "liter":"l", "litre":"l","molar":"M",
               "lumen":"lm", "lux":"lx", "meter":"m", "metre":"m", "mole":"mole",
               "newton":"N", "ohm":"Omega", "pascal":"Pa", "radian":"rad",
               "second":"s", "siemens":"S", "sievert":"Sv", "steradian":"sr",
               "tesla":"T", "volt":"V", "watt":"W", "weber":"Wb", "dimensionless":"1"}

prefix_map = {"deca":"da", "hecto":"h", "kilo":"k", "mega":"M", "giga":"G",
              "tera":"T", "peta":"P", "exa":"E", "zetta":"Z", "yotta":"Y",
              "deci":"d", "centi":"c", "milli":"m", "micro":"u", "nano":"n",
              "pico":"p", "femto":"f", "atto":"a", "zepto":"z", "yocto":"y",
              None:"", "-3":"m"}

si_units = ["kg", "m", "s", "A", "mole", "K", "cd", "1"]


to_si_units = {"V": "kg*m**2*s**-3*A**-1",
               "F": "s**4*A**2*m**-2*kg**-1",
               "S": "kg**-1*m**-2*s**3*A**2",
               "Hz": "s**-1",
               "l":"cm**3",
               "C": "A*s",
               "I": "1",
               "J": "kg*m**2*s**-2",
               "M": "mole*dm**-3"}

for u in si_units:
    to_si_units[u] = u

prefix_factor \
    = {"da":10,
       "h": 100,
       "k": 1000,
       "M": 1000**2,
       "G":1000**3,
       "T":1000**4,
       "P":1000**5,
       "E":1000**6,
       "Z":1000**7,
       "Y":1000**8,
       "d":0.1,
       "c":0.01,
       "m":0.001,
       "u":0.001**2,
       "n":0.001**3,
       "p":0.001**4,
       "f":0.001**5,
       "a":0.001**6,
       "z":0.001**7,
       "y":0.001**8}

prefix_factor_to_key \
    = {1.0000000000000001e-24: 'y',
       1.0000000000000001e-21: 'z',
       1e-18: 'a',
       1e-15: 'f',
       1e-12: 'p',
       1e-09: 'n',
       1e-06: 'u',
       0.001: 'm',
       0.01: 'c',
       0.1: 'd',
       10: 'da',
       100: 'h',
       1000: 'k',
       1000000: 'M',
       1000000000: 'G',
       1000000000000: 'T',
       1000000000000000: 'P',
       1000000000000000000: 'E',
       1000000000000000000000: 'Z',
       1000000000000000000000000: 'Y'}


def _clean_unit(unit):

    # Remove square roots
    if "**1/2" in unit:
        unit = "*".join(["*".join(u.split("*")[:-1]) for \
                         u in unit.split("**1/2")]).strip("*")
        
    return unit


class Unit(object):
    """
    Class for converting units

    Arguments
    ---------
    unit_str : str
        Sting with unit

    """
    def __init__(self, unit_str):

        unit_str = _clean_unit(unit_str)
        self._unit_str=unit_str
        self._factor, self._base_unit, self._prefixes = self._remove_prefixes()


    @property
    def factor(self):
        """
        Return factor to mulitply when removing
        prefixes
        """
        return self._factor

    @property
    def prefix(self):
        """
        Return the unit prefix (if any), e.g 'm'
        if the unit is ms
        """
        if len(self._prefixes) == 1:
            return self._prefixes[0]
        else:
            return self._prefixes

    @property
    def unit(self):
        return self._unit_str

    @property
    def base_unit(self):
        """
        Return unit without prefixes
        """
        return self._base_unit

    @property
    def reciprocal(self):
        """
        Return the reciprocal of the unit
        
        Example
        -------
    
        >>> ...
            >>> unit = Unit("s**-1")
            >>> unit.reciprocal
            "s"
            >>> ...

        """
        # Get the base units and exponents
        if not hasattr(self, "_base_si_exponents"):
            self._process_si_unit()

        # Collect the terms and use the negative exponent
        reciprocals = []
        for b, e, p in zip(self._base_si_units,
                           self._base_si_exponents, self._prefixes):

            
            if e == -1:
                # Do not include any exponents
                reciprocals.append("{}{}".format(p, b))
            else:
                # Include exponent
                reciprocals.append("{}{}**{}".format(p, b, -e))
            
        return "*".join(reciprocals)
    
    
    @property
    def si_unit(self):
        """
        Return the unit converted into SI units
        
        """

        if not hasattr(self, "_si_unit"):
            self._process_si_unit()

        return self._si_unit

    @property
    def si_unit_factor(self):
        """
        Return the factor to multiple when coverting 
        to SI units
        
        """

        if not hasattr(self, "_si_unit_factor"):
            self._process_si_unit()

        return self._si_unit_factor

        

    def _process_si_unit(self):
        factor = self._factor
        subunits = "^".join(self._base_unit.split("**")).split("*")

        si_unit = 1.0
        exprs = []
        units = []
        exponents = []
        for u in subunits:

            # Remove possible exponent
            u_ = u.split("^")

            # Convert to SI
            msg = ("Unit {} if not found in SI-unit map".format(u_[0])+
                   "\nPossible units are {}".format(list(to_si_units.keys())))
            assert u_[0] in list(to_si_units.keys()), msg
            
            u_si_ = to_si_units[u_[0]]
            
            # Remove possible prefixes from SI unit
            factor_, u_si, prefix_ = get_unit_conversion_factor(u_si_, True,
                                                                   excluded_kg=True)
            factor *= factor_
            
            # Convert to SI
            si_unit_ = sp.sympify(u_si)
            units.append(si_unit_)

            # Get exponent
            exponent = 1 if len(u_) == 1 else sp.sympify(u_[1])
            exponents.append(exponent)


        self._base_si_units = units
        self._base_si_exponents = exponents
        
        # Collect all subunits
        f = None
        for q,e in zip(units, exponents):
            
            u_ = q if not e else q**e
            if f:
                f = f*u_
            else:
                f = u_

        self._si_unit = str(f)
        self._si_unit_factor = factor
        
        return self._si_unit

    def get_factor(self, unit):
        """
        Return the factor needed to multiply with 
        the current unit in order to get the argument unit
        
        Arugments
        ---------
        unit : str
            A unit


        Returns
        .......
        factor : float
            Return the factor needed to multiply with 
            the current unit in order to get the argument unit


        Example
        -------
        
            >>> unit = Unit("dm")
            >>> unit.get_factor("m")
            10
            >>> unit.get_factor("mm")
            0.01

        
        """
        factor = Unit(unit).factor
        return factor / float(self.factor)

        
    def _remove_prefixes(self):
        """
        Remove possible prefixes such as
        milli, micro, etc 
        """

        return get_unit_conversion_factor(self._unit_str,
                                          return_new_unit=True)


    def __str__(self):
        return self._unit_str



def get_single_unit_conversion_factor(unit, excluded_kg=False):
    """
    Convert unit to unit without prefixes and return
    the new unit and the factor to multiply

    Arguments
    ---------
    unit : str
        A string containing a single unit with possible prefix

    Returns
    -------
    new_unit : str
        The unit without prefixes
    factor : float
        The factor to multiply to get the correct unit
    prefix : str:
        The prefi
    
    """

    if unit in list(si_unit_map.values()):
        # There are no prefix
        new_unit = unit
        factor = 1.0
        prefix = ""
        
    else:
        
        prefix = unit[0]
        new_unit = unit[1:]

        # print prefix
        # print new_unit
        msg="Invalid unit {}".format(new_unit)
        assert new_unit in list(si_unit_map.values()), msg
        
        if excluded_kg and new_unit == "g":
            return unit, 1.0
     
      
        msg="Prefix {} if not standardized".format(prefix)
        assert prefix in list(prefix_factor.keys()), msg
    
      
        factor = prefix_factor[prefix]

        
    return new_unit, factor, prefix

def get_unit_conversion_factor(unit, return_new_unit=False, excluded_kg=False):
    """
    Convert sting of composed units to sting of 
    composed units without prefixes and return
    the new unit and the factor to multiply

    Arguments
    ---------
    unit : str
        A string containing a multiple unit separated by "*"
        with possible prefix and exponents, with exponents
        being defined as the number post "**"
    return_new_unit : str
        If True, return a string with the new unit without 
        prefixes (Default:False)

    Returns
    -------
    new_unit : str
        The unit without prefixes
    factor : float
        The factor to multiply to get the correct unit
    exclude_kg : bool
        If True, do not remove prefix from 'kg'
    
    """


    # Split total unit in different unit
    u1 = "^".join(unit.split("**")).split("*")


    factor = 1
    new_units = []
    prefixes = []

    for u in u1:
    
        # For each unit extract the exponent
        u0 = u.split("^")
        new_unit , factor_, prefix_ = get_single_unit_conversion_factor(u0[0],
                                                               excluded_kg)
      
        prefixes.append(prefix_)
        if len(u0) == 1:
            # There are no exponent
            new_units.append(new_unit)
            factor *= factor_
            
        else:
            msg="Invalid exponent in unit {}".format(u)
            assert len(u0) == 2, msg 
            # Get exponent
            new_units.append(new_unit + "**" + u0[1])
            factor /= factor_

    if return_new_unit:
        return factor, "*".join(new_units), prefixes
    
    return factor


def _test1():
    from modelparameters.parameters import ScalarParam

    Cai1=ScalarParam(0.2049, unit='uM', name ="Cai1")
    Cai2 = ScalarParam(0.000153, unit="mM", name ="Cai2")

    # unit="l*pF**-1*ns**-1"


    Cai2.update(Cai1)
    print(Cai2)
    exit()
            
            
            
        
        
    from IPython import embed; embed()
    exit()
    
    
    from modelparameters.parameters import ScalarParam
    
    p1 = ScalarParam(1.0, unit = "mM")
    p2 = ScalarParam(0.01, unit = "uM")

    p1.update(p2)


    
if __name__ == "__main__":

    unit = 'mV*mS*uF**-1'
    new_unit = Unit(unit)
    si_unit = new_unit.si_unit

    l_unit = Unit("l")
    si_unit = l_unit.si_unit
    from IPython import embed; embed()
    exit()
