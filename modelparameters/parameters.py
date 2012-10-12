# Copyright (C) 2008-2012 Johan Hake
#
# This file is part of ModelParameters.
#
# ModelParameters is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ModelParameters is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with ModelParameters. If not, see <http://www.gnu.org/licenses/>.

__all__ = ["Param", "ScalarParam", "OptionParam", "ConstParam", "ArrayParam"\
           "SlaveParam", "eval_param_expr", "dummy_sym"]

# System imports
# Conditional sympy import
try:
    from sympytools import sp, ModelSymbol, store_symbol_parameter, \
         symbol_param_value_namespace
    dummy_sym = ModelSymbol("", "")
except ImportError, e:
    sp = None
    ModelSymbol = None
    dummy_sym = None

import types
import operator

# local imports
from config import *
from logger import *
from utils import check_arg,  check_kwarg, scalars, value_formatter,\
     Range, tuplewrap, integers, nptypes
from utils import _np as np

option_types = scalars + (str,)

class Param(object):
    """
    A simple type checking class for a single value
    """
    def __init__(self, value, name="", helptext=""):
        """
        Initialize the Param
        
        Arguments
        ---------
        value : any
            The initial value of this parameter. The type of value is stored
            for future type checks
        name : str (optional)
            The name of the parameter. Used in pretty printing
        helptext : str (optional)
            A help text associated with the Parameter
        """
        check_kwarg(name, "name", str)
        self._value = value
        self.value_type = type(value)
        self._not_in_str = None
        self._in_str = None
        self._in_range = None
        self._name = name
        self._helptext = helptext

    @property
    def helptext(self):
        return self._helptext
    
    def _get_name(self):
        return self._name
    
    def _set_name(self, name):
        check_arg(name, str)
        if self._name:
            value_error("Cannot set name attribute of %s, it is already set "\
                  "to '%s'" % (self.__class__.__name__, self._name))
        self._name = name
        
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
    
    name = property(_get_name, _set_name)
    value = property(getvalue, setvalue)
    
    def check(self, value):
        """
        Check the value using the type and any range check
        """
        # Fist check if the value is an int or float.
        # (Treat these independently)

        name_str = " '%s'" % self.name if self.name else ""
        if self.value_type in scalars and \
               isinstance(value, scalars):
            if isinstance(value, float) and self.value_type == int:
                info("Converting %s to %d%s", value, int(value), \
                     name_str)
            value = self.value_type(value)
            
        if self.value_type in [bool] and isinstance(value, int) and \
               not isinstance(value, bool):
            info("Converting %s to '%s' while setting parameter%s", \
                 value, bool(value), name_str)
            value = self.value_type(value)
            
        if not isinstance(value, self.value_type):
            if self.value_type == nptypes:
                type_name = "scalar or np.ndarray"
            else:
                type_name = self.value_type.__name__
            type_error("expected '%s' while setting parameter%s"%\
                       (type_name, name_str))
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
        return "%s(%s%s%s)" % (self.__class__.__name__, \
                               value_formatter(self._value), self._check_arg(),\
                               self._name_arg())

    def _name_arg(self):
        return ", name='%s'" % self._name if self._name else ""
    
    def _check_arg(self):
        return ""
    
    def __str__(self):
        """
        Returns a nice representation of the Param
        """
        return self.format_data()

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
               (self._name == other._name, self._value == other._value, \
                self.__class__ == other.__class__)

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
        check_arg(options, list)
        if len(options) < 2:
            value_error("expected the options argument to be at least of length 2")
            
        super(OptionParam, self).__init__(value, name)
        
        # Check valid types for an 'option check'
        for option in options:
            if not isinstance(option, option_types):
                type_error("options can only be 'str' and scalars got: '%s'" % \
                           type(option).__name__)
        
        # Define a 'check function'
        self._in_range = lambda value : value in options
        
        # Define some string used for pretty print
        self._in_str = "%%s \xe2\x88\x88 %s" % repr(options)
        
        self._not_in_str = "%%s \xe2\x88\x89 %s" % repr(options)
        
        # Define a 'repr string'
        #self._repr_str = "OptionParam(%%s, %s)" % repr(options)
        
        # Set the value using the check functionality
        self.setvalue(value)

        # Check that all values in options has the same type
        for val in options:
            if not isinstance(val, self.value_type):
                type_error("All values of the 'option check' " +\
                           "need to be of type: '%s'" % type(self._value).__name__)
        
        # Store options
        self._options = options
        
    def _check_arg(self):
        return ", %s" % repr(self._options)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
               (self._name == other._name, self._value == other._value, \
                self.__class__ == other.__class__, \
                self._options == other._options)

class ConstParam(Param):
    """
    A Constant parameter which prevent any change of values
    """
    def __init__(self, value, name=""):
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
        
        # Define a 'check function'
        self._in_range = lambda x : x == self._value
        
        # Define some string used for pretty print
        self._in_str = "%s - Constant"
        self._not_in_str = "%%s != %s" % self._value
        self.setvalue(value)

class ScalarParam(Param):
    """
    A simple type and range checking class for a scalar value
    """
    def __init__(self, value, ge=None, le=None, gt=None, lt=None, \
                 unit="1", name="", symname=""):
        """
        Creating a ScalarParam
        
        Arguments
        ---------
        value : scalar
            The initial value of this parameter
        gt : scalar (optional)
            Greater than, range control of argument
        ge : scalar (optional)
            Greater than or equal, range control of argument
        lt : scalar (optional)
            Lesser than, range control of argument
        le : scalar (optional)
            Lesser than or equal, range control of argument
        unit : str (optional, if sympy is available)
            The unit of the scalar parameter
        name : str (optional)
            The name of the parameter. Used in pretty printing
        symname : str (optional, if sympy is available)
            The name of the symbol which will be associated with this
            parameter. Can only be set if name is also set.
        """
        check_arg(value, scalars, 0, ScalarParam)
        super(ScalarParam, self).__init__(value, name)
        
        self._range = Range(ge, le, gt, lt)
        self._in_range = self._range._in_range

        # Define some string used for pretty print
        self._in_str = self._range._in_str
        self._not_in_str = self._range._not_in_str

        # Create symbol
        if name == "":
            if symname != "":
                type_error("expected no symname when name is not set")
            self._sym = dummy_sym
        elif sp is None:
            self._sym = None
        else:
            self._sym = ModelSymbol(name, name if symname == "" else symname)

            # Store parameter 
            store_symbol_parameter(self)

        # Set the value using the check functionality
        # (Only if not called from derived class)
        if type(self) == ScalarParam:
            self.setvalue(value)

    def _get_name(self):
        return self._name
    
    def _set_name(self, name):
        """
        Set the name. Can only be done if not set during instantiation
        """
        name = tuplewrap(name)
        check_kwarg(name, "name", tuple, itemtypes=str)

        if len(name) == 1:
            name = name[0]
            symname = name
        elif len(name) == 2:
            if sp is None:
                error("sympy is not installed so setting symname is not "\
                      "supported")
            name, symname = name
        else:
            value_error("expected 1 or 2 name arguments")
        
        super(ScalarParam, self)._set_name(name)

        if sp is None:
            return
        
        # Create a new symbol with the updated name
        self._sym = ModelSymbol(name, symname)

        # Store parameter 
        store_symbol_parameter(self)

    def get_sym(self):
        return self._sym
    
    name = property(_get_name, _set_name)
    sym = property(get_sym)
    
    def _name_arg(self):
        """
        Return a repr of the name arguments for a ScalarParam
        """
        name_arg = super(ScalarParam, self)._name_arg()
        if sp is None:
            return name_arg
        return name_arg + (", symname='%s'" % (self._sym.abbrev) \
               if self._sym.abbrev and self._sym.abbrev != self._name else "")

    def _check_arg(self):
        """
        Return a repr of the check arguments
        """
        if self._range.arg_repr_str:
            return ", " + self._range.arg_repr_str
        return ""

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
               (self._name == other._name, self._value == other._value, \
                self.__class__ == other.__class__, \
                self._range == other._range)

class ArrayParam(ScalarParam):
    """
    A numpy Array based parameter
    """
    def __init__(self, value, size=None, ge=None, le=None, gt=None, lt=None, \
                 unit="1", name="", symname=""):
        """
        Creating an ArrayParam
        
        Arguments
        ---------
        value : scalar, np.ndarray
            The initial value of this parameter
        size : integer (optional)
            Set the size of the ns.array. If set value must be a scalar
        gt : scalar (optional)
            Greater than, range control of argument
        ge : scalar (optional)
            Greater than or equal, range control of argument
        lt : scalar (optional)
            Lesser than, range control of argument
        le : scalar (optional)
            Lesser than or equal, range control of argument
        unit : str (optional, if sympy is available)
            The unit of the scalar parameter
        name : str (optional)
            The name of the parameter. Used in pretty printing
        symname : str (optional, if sympy is available)
            The name of the symbol which will be associated with this
            parameter. Can only be set if name is also set.
        """
        
        if np is None:
            error("numpy is not installed so ArrayParam is not available")

        # If setting value using size
        if size is not None:
            # If a size is provided a scalar is expected for the value
            check_kwarg(size, "size", integers, ArrayParam, ge=1)
            check_arg(value, scalars, 0, ArrayParam)

            # Create numpy array based on the passed value
            # Use intc and float_ to be compatible with c code.
            value = np.array([value]*size, dtype=np.intc \
                             if isinstance(value, integers) \
                             else np.float_)

        # If setting value using only value argument
        else:
            check_arg(value, nptypes, 0, ArrayParam)

            # Fist check any scalars passed
            if isinstance(value, integers):
                value = np.array([value], dtype=np.intc)
            elif isinstance(value, scalars):
                value = np.array([value], dtype=np.float_)

            # Then check passed NumPy arrays
            elif value.dtype in integers:
                value = value.astype(np.intc)
            elif value.dtype in scalars:
                value = value.astype(np.float_)
            else:
                type_error("expected a scalar or a scalar valued np.ndarray "
                           "as value argument.")

        # Init super class with dummy value
        super(ArrayParam, self).__init__(value[0], ge, le, gt, lt, unit, \
                                         name, symname)

        # Assign value
        self._value = value
        self.value_type = nptypes

        # Use setvalue to set value using the range
        self.setvalue(value)
        
    def setvalue(self, value):
        """
        Set value of ArrayParameter
        """

        # An initial slive for the whole array
        index = slice(0,len(self._value)+1)

        # Tuple means index assignment
        # FIXME: Add support for slices
        if isinstance(value, tuple):
            if len(value) != 2:
                value_error("expected a tuple of length 2 when assigning "\
                            "single items")
            if not isinstance(value[0], integers):
                value_error("expected first value in index assignment to be"\
                            " an integer")
            if not isinstance(value[1], scalars):
                value_error("expected second value in index assignment to be"\
                            " an scalar")
            index = value[0]
            value = value[1]
        
        check_arg(value, nptypes, context=ArrayParam.setvalue)

        if isinstance(value, np.ndarray):
            if len(value) != len(self._value):
                value_error("expected the passed array to be of "\
                            "size: '%d'"%len(self._value))

        # Assign value
        self._value[index] = self.check(value)
        
    value = property(Param.getvalue, setvalue)

    def resize(self, newsize):
        """
        Change the size of the Array
        """
        if not isinstance(newsize, integers):
            error("expected newsize argument to be an int")
            
        newsize = int(newsize)

        # Resize array if size is changed
        if len(self._value) != newsize:
            self._value = np.resize(self._value, newsize)
    
class SlaveParam(ScalarParam):
    """
    A slave parameter defined by other parameters
    """
    def __init__(self, expr, name=None):

        if sp is None:
            error("sympy is not installed so SlaveParam is not available")
            
        if not isinstance(expr, (ScalarParam, sp.Basic)):
            type_error("expected an expression of symbols from "\
                       "other ScalarParams")
        
        if isinstance(expr, ScalarParam):
            expr = expr.sym

        if not all(isinstance(atom, (sp.Number, ModelSymbol))\
                   for atom in expr.atoms()):
            type_error("expected expression of other ScalarParams")
        
        ScalarParam.__init__(self, 0.0, name=name, symname=name)

        # Store the original expression used to evaluate the value of
        # the SlaveParam
        self._expr = expr
        
    def setvalue(self, value):
        """
        A setvalue method which always fails
        """
        type_error("cannot assign to a SlaveParam")
                
    def getvalue(self):
        """
        Return a computed value of the Parameters
        """
        
        return eval_param_expr(self._expr)
    
    value = property(getvalue, setvalue)

    def format_data(self, value=None, not_in=False, str_length=0):
        "Print a nice formated version of the value and its range"

        # If no '_in_str' is defined
        return "%s - SlaveParam(%s)"%(value_formatter(self.getvalue(), str_length), \
                                      str(self._expr))

def eval_param_expr(expr, ns=None):
    """
    Eval an expression of symbols of ScalarParam

    Arguments
    ---------
    expr : expression of ParamSymbols
        The expression to be evaulated
    ns : dict (optional)
        A namespace in which the expression will be evaluated in
    """

    if sp is None:
        error("sympy is not installed so evaluation of expressions"\
              " is not available")
    
    # Create name space which the expression will be evaluated in
    ns = symbol_param_value_namespace(expr)
    
    # First check if we have numpy arrays
    if np and any(isinstance(value, np.ndarray) for value in ns.values()):

        # Second check if they have the same length
        all_length = [len(value) for value in ns.values() \
                      if isinstance(value, np.ndarray)]
        same_length = all(all_length[0] == l for l in all_length)
        if not same_length:
            value_error("expected all ArrayParams in an expression "\
                        "to be of equal size.")
        
        # Update name space with numpy name space
        ns.update(np.__dict__)
        
    else:
        import math
        ns.update(math.__dict__)
    
    return eval(str(expr), {}, ns)
    

__all__ = [_name for _name in globals().keys() if _name[0] != "_"]

