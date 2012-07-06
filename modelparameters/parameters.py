__author__ = "Johan Hake <hake.dev@gmail.com>"
__date__ = "2008-06-22 -- 2012-07-06"
__copyright__ = "Copyright (C) 2008-2012 " + __author__
__license__  = "GNU LGPL Version 3.0 or later"

__all__ = ["Param", "ScalarParam", "OptionParam", "ConstParam", "ArrayParam"]

# System imports
# Conditional sympy import
try:
    from sympytools import sp
except:
    sp = None

import types
import operator

# local imports
from config import *
from logger import *
from utils import check_arg, scalars, value_formater, _np

# Collect all parameters
_all_parameters = {}

option_types = scalars + (str,)

def symbol_to_params(sym):
    """
    Take a symbol or expression of symbols and returns the corresponding Parameters
    """
    check_arg(sym, SymbolParam, context=symbol_to_param)
    param = _all_parameters.get(sym)
        
    if param is None:
        error("No parameter with name '{0}' registered".format(sym.abbrev))
    return param

class Param(object):
    _combined_count = 0
    """
    A simple type checking class for a single value
    """
    def __init__(self, value, name=""):
        """
        Initialize the Param
        
        Arguments
        ---------
        value : any
            The initial value of this parameter. The type of value is stored
            for future type checks
        name : str (optional)
            The name of the parameter. Used in pretty printing
        """
        check_kwarg(name, "name", str)
        self._value = value
        self.value_type = type(value)
        self._repr_str = "Param(%s)"
        self._not_in_str = None
        self._in_str = None
        self._in_range = None
        self._name = name

    def _get_name(self):
        return self._name
    
    def _set_name(self, name):
        check_arg(name, str)
        if self._name:
            error("Cannot set name attribute of Parameter, "\
                  "it is already set to '%s'" % self._name)
        self._name = name
        
    name = property(_get_name, _set_name)
    
    def setvalue(self, value):
        """
        Try to set the value using the check
        """
        self._value = self.check(value)
        
    def getvalue(self):
        """
        Return the value
        """
        return self._value
    
    def check(self, value):
        """
        Check the value using the type and any range check
        """
        # Fist check if the value is an int or float.
        # (Treat these independently)
        name_str = "" if self.name is None else \
                   " for the parameter '%s'"%self.name
        if self.value_type in scalars and \
               isinstance(value, scalars):
            if isinstance(value, float) and self.value_type == int:
                info("Converting %s to %d%s", str(value), int(value), \
                     name_str)
            value = self.value_type(value)
        if self.value_type in [bool] and isinstance(value, int) and \
               not isinstance(value, bool):
            info("Converting %s to '%s'%s", str(value), \
                 "True" if value else "False", name_str)
            value = self.value_type(value)
            
        if not isinstance(value, self.value_type):
            type_error("Please provide a '%s'%s"%\
                       (self.value_type.__name__, name_str))
        if self._in_range is not None:
            if not self._in_range(value):
                value_error("Illegal value%s: %s"%\
                            (name_str, self.format_data(value, True)))
        return value
    
    def format_data(self, value=None, not_in=False, str_length=0):
        """
        Print a nice formated version of the value and its range

        Arguments
        ---------
        value : same as Param.value_type (optional)
            A value to be used in the formating. If not passed stored
            value is used.
        not_in : bool (optional)
            If True return a not in version of the value
        str_length : int (optional)
            Used to pad the str with blanks
        """
        if value is None:
            value = self._value

        # If no '_in_str' is defined
        if self._in_str is None:
            return value_formatter(self._value, str_length)
        
        if not_in:
            return self._not_in_str%(value_formatter(value, str_length))
        else:
            return self._in_str % value_formatter(value, str_length)

    def format_width(self):
        """
        Return the width of the formated str of value
        """
        return len(value_formatter(self._value))

    def __repr__(self):
        """
        Returns an executable version of the Param
        """
        return self._repr_str % value_formatter(self._value)
    
    def __str__(self):
        """
        Returns a nice representation of the Param
        """
        return self.format_data()

class OptionParam(Param):
    """
    A simple type and options checking class for a single value
    """
    def __init__(self, value, options, name=""):
        """
        Initialize the OptionParam
        
        Arguments
        ---------
        value : scalars or str
            The initial value of this parameter. The type of value is stored
            for future type checks
        options : list
            A list of acceptable values for the parameter
        name : str (optional)
            The name of the parameter. Used in pretty printing
        """
        super(OptionParam, self).__init__(value, name)
        check_arg(options, list)
        
        # Check valid types for an 'option check'
        for option in options:
            if not isinstance(option, option_types):
                type_error("options can only be 'str' and scalars got '%s'" % \
                           type(option).__name__)
        
        # Define a 'check function'
        self._in_range = lambda value : value in options
        
        # Define some string used for pretty print
        self._in_str = "%%s \xe2\x88\x88 %s" % repr(options)
        
        self._not_in_str = "%%s \xe2\x88\x89 %s" % repr(options)
        
        # Define a 'repr string'
        self._repr_str = "OptionParam(%%s, %s)" % repr(options)
        
        # Set the value using the check functionality
        self.setvalue(value)

        # Check that all values in options has the same type
        for val in options:
            if not isinstance(val, self.value_type):
                type_error("All values of the 'option check' " +\
                           "need to be of type: '%s'" % type(self.value).__name__)
        
class ConstParam(Param):
    """
    A Constant parameter which prevent any change of values
    """
    def __init__(self, value, name=None):
        """
        Initialize the ConstParam
        
        Arguments
        ---------
        value : scalars or str
            The initial value of this parameter. The type of value is stored
            for future type checks
        name : str (optional)
            The name of the parameter. Used in pretty printing
        """
        Param.__init__(self, value, name)
        self._repr_str = "ConstParam(%s)"
        
        # Define a 'check function'
        self._in_range = lambda x : x == self._value
        
        # Define some string used for pretty print
        self._in_str = "%s - Constant"
        self._not_in_str = "%%s != %s" % self._value
        self.setvalue(value)

class ScalarParam(Param):
    """
    A simple type and range checking class for a single value

    Example:
    ========
    
    >>> sigma = ScalarParam(5, ge=0, le=10)

    @type value : scalar
    @param value : The initial value of the ScalarParam parameter
    @type ge : scalar
    @param ge : Defines the lower closed limit of the check (greater or
    equal than).
    @type gt : scalar
    @param gt : Defines the lower open limit of the check (greater than).
    @type le : scalar
    @param le : Defines the upper closed limit of the check (lesser or
    equal than).
    @type lt : scalar
    @param lt : Defines the upper open limit of the check (lesser than).

    If none of C{gt} or C{ge} are set, are -\inf set as the lower
    limit. Likewise, if none of C{lt} or C{le} are set, are \inf
    set as the upper limit.

    """
    def __init__(self, value, ge=None, le=None, gt=None, lt=None, \
                 name=None, symname=None):
        Param.__init__(self, value, name)
        
        self._range = Range(ge, le, gt, lt)
        self._in_range = self._range._in_range

        # Define some string used for pretty print
        self._in_str = self._range._in_str
        self._not_in_str = self._range._not_in_str

        # Define a 'repr string'
        self._repr_str = "ScalarParam(%%s, %s%%s)" % self._range.arg_repr_str
        
        # Set the value using the check functionality
        self.setvalue(value)

    def _get_name(self):
        return self._name
    
    def _set_name(self, name):
        "Set name"
        symname=None
        if isinstance(name, tuple):
            assert(len(name)==2)
            assert(all(isinstance(n, str) for n in name))
            name, symname = name
            
        if not isinstance(name, str):
            error("expected a str for the name argument")

        if self._name:
            error("Cannot set name attribute of Parameter, "\
                  "it is already set to '%s'"%self._name)
        self._name = name
        
        # Set name of symbol
        self.sym.abbre = sympy.Symbol(symname)
    
    name = property(_get_name, _set_name)
    
class ArrayParam(Param):
    """
    A numpy Array based parameter
    """
    def __init__(self, value, size=None, name=None, symname=None):
        if size is not None:
            # If a size is provided a scalar is expected for the value
            if not isinstance(value, scalars):
                error("expected a scalar as the first argument")
            if not isinstance(size, int) and size<=0:
                error("expected a positive int as the second argument")
            value = _np.array([value]*size, dtype="d" \
                             if isinstance(value, float) \
                             else "i")
        
        # Checking Array argument
        if isinstance(value, _np.ndarray):
            if value.dtype.char == "f":
                value = value.astype("d")
            elif value.dtype.char in ["I", "u", "b"]:
                value = value.astype("i")
            elif value.dtype.char not in ["i", "d"]:
                error("expected dtype of passed NumPy array to "\
                      "be a scalar")
        elif isinstance(value, scalars):
            value = _np.array([value])
        else:
            error("expected a scalar or NumPy array as the first "\
                  "argument")
        
        Param.__init__(self, value, name, symname)

        # Define a 'repr string'
        self._repr_str = "ArrayParam(%s)"

    def setvalue(self, value):
        """
        Set value of ArrayParameter
        """
        if isinstance(value, _np.ndarray):
            if len(value) != len(self._value):
                raise TypeError, "expected the passed array to be of "\
                      "size: '%d'"%len(self._value)
            self._value[:] = value
        
        # Set the whole array to value
        elif isinstance(value, scalars):
            self._value[:] = value
        elif isinstance(value, tuple) and len(value)==2:
            if not(isinstance(value[0], int) and \
                   isinstance(value[1], scalars)):
                error("expected a size 2 tuple of an int and"\
                                " a scalar")
            self._value[value[0]] = value[1]
        else:
            error("expected a scalar, numpy array or a size "\
                  "2 tuple of an int and a scalar")
        
    def resize(self, newsize):
        """
        Change the size of the Array
        """
        if not isinstance(newsize, int):
            error("expected newsize argument to be an int")
        if len(self._value) != newsize:
            self._value = _np.resize(self._value, newsize)
    
class SlaveParam(Param):
    """
    A slave parameter defined by other parameters
    """
    _all_objects = {}
    def __init__(self, value, name=None):
        if not isinstance(value, (Param, sympy.Basic)):
            error("expected a scalar, or expression of "\
                  "other parameters")
        if isinstance(value, Param):
            value = value.sym

        if not all(isinstance(atom, (sympy.Number, ParSymbol))\
                   for atom in value.atoms()):
            error("expected expression of other parameters")
        Param.__init__(self, value, name, symname=name)

        # Store the original expression used to evaluate the value of
        # the SlaveParam
        self.symbols = value
        self.is_array = any(isinstance(atom.param, ArrayParam) for atom in \
                            self.iter_par_symbols())
        
        # If the parameter is not array it is scalar
        self.is_scalar = not self.is_array
        self._repr_str = "SlaveParam(%s)"

        # Store object
        SlaveParam._all_objects[str(self)] = self
        
    def check(self, value):
        "A check function which always fails"
        error("Cannot assign a value to a 'SlaveParam'")

    def _str_repr(self, op="repr"):
        assert(op in ["name", "repr", "symb"])
        return str(self.sym.subs(dict(eval("atom.%s_subs()"%op)\
                                      for atom in self.sym.atoms()\
                                      if isinstance(atom, ParSymbol))))
    def __str__(self):
        return self._str_repr("name")
    
    def __repr__(self):
        return self._str_repr("name")

    def iter_par_symbols(self):
        """
        Return an iterator over all original parameter symbols of the
        expression
        """
        for atom in self.symbols.atoms():
            if not isinstance(atom, ParSymbol):
                continue
            if isinstance(atom.param, SlaveParam):
                for atom in atom.param.iter_par_symbols():
                    yield atom
            yield atom
                
    def get(self):
        """
        Return a computed value of the Parameters
        """
        par_symbols = [atom for atom in self.iter_par_symbols()]
        
        # Create name space which the expression will be evaluated in
        ns = dict((str(sym), sym.value()) for sym in par_symbols)
        ns.update(_np.__dict__)
        all_length = [len(sym.param.get()) for sym in par_symbols if \
                      sym.param.is_array]
        same_length = all(all_length[0] == l for l in all_length)
        if not same_length:
            error("expected all ArrayParams in an expression "\
                  "to be of equal size.")

        return eval(str(self.symbols), globals(), ns)
    
    def format_data(self, value=None, not_in=False, str_length=0):
        "Print a nice formated version of the value and its range"

        # If no '_in_str' is defined
        return "%s - SlaveParam(%s)"%(value_formatter(self.get(), str_length), \
                                    self._str_repr("symb"))

# Test code
if __name__ == "__main__":
    x = Param(3)
    print x
    print repr(x)
    x.setvalue(5)
    print x
    
    v = ScalarParam(5, 0, 10)
    print v
    print repr(v)
    
    u = OptionParam("a", ["a", "b", "c", "d"])
    print u
    print repr(u)

    a = ArrayParam(5.,10)
    print a
    print repr(a)
    a.setvalue((0, 6.))
    print a
    a.setvalue(7.)
    print a
    a.setvalue(_np.arange(10))
    print a
    a.resize(20)
    print repr(a)
    for atom in (v*x+v*a).atoms():
        print atom.param
    print v*x+v*a
    p = SlaveParam(v*x+v*a)
    print p.get()
    print p
    print repr(p)
    a1 = ArrayParam(5.,20)
    print SlaveParam(a1*p).get()

    x = ArrayParam(1.)
    y = ArrayParam(1.)
    z = ArrayParam(1.)
    n = ArrayParam(1.)
    
    p = SlaveParam(sympy.exp(-z))
    print p
    
    print p.get()
    z.resize(11)
    z.setvalue(_np.linspace(0,1,11))
    print p.get()
