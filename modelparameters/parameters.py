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

__all__ = [
    "Param",
    "ScalarParam",
    "OptionParam",
    "ConstParam",
    "ArrayParam" "SlaveParam",
    "eval_param_expr",
    "dummy_sym",
]
import os

# System imports
# Conditional sympy import
try:
    from .sympytools import (
        sp,
        store_symbol_parameter,
        value_namespace,
        symbols_from_expr,
        symbol_to_param,
    )
    from .codegeneration import pythoncode, sympycode

    dummy_sym = sp.Dummy("")
except ImportError:
    sp = None
    dummy_sym = None

import copy

# local imports
from .logger import value_error, error, type_error, info, warning, debug
from .utils import (
    check_arg,
    check_kwarg,
    scalars,
    value_formatter,
    Range,
    integers,
    nptypes,
    Timer,
)
from .utils import _np as np

import pint

try:
    ureg = pint.UnitRegistry(fmt_locale=os.getenv("LC_ALL", "en_US.UTF-8"))
except Exception:
    ureg = pint.UnitRegistry()

option_types = scalars + (str,)


def _process_other(other):
    """Helper function for magic methods
    in ScalarParam.

    Arguments
    ---------
    other : scalar or Param
        Either a scalar (int , float, ...) of a parameter
        (Param, ScalarParam, ...) that also holds info about
        `name`, and `unit`.

    Returns
    -------
    value : float
        The value of other
    name : str
        The name of other (if not available name = "")
    unit : str
        The unit of other (if not available unit = "1")
    """

    def from_param(other_):
        value = other_.value
        name = other_.name
        unit = getattr(other_, "unit", "1")
        return (value, name, unit)

    if isinstance(other, scalars):
        return (other, "", "1")

    elif isinstance(other, Param):
        return from_param(other)

    else:
        # Check it other has an attribute called param
        # which is the case for gotran.Paramerter
        if hasattr(other, "param"):
            return from_param(other.param)

        # I don't know how to handle this
        raise ValueError(f"Unknown type {type(other)}")


def _eq(eq):
    if len(eq) <= 1:
        return eq
    else:
        return all(np.hstack(eq))


class Param(object):
    """
    A simple type checking class for a single value
    """

    def __init__(self, value, name="", description="", **kwargs):
        """
        Initialize the Param

        Arguments
        ---------
        value : any
            The initial value of this parameter. The type of value is stored
            for future type checks
        name : str (optional)
            The name of the parameter. Used in pretty printing
        description : str (optional)
            A description associated with the Parameter
        """
        check_kwarg(name, "name", str)
        self._value = value
        self.value_type = type(value)
        self._not_in_str = None
        self._in_str = None
        self._in_range = None
        self._name = name
        self._description = description

    def copy(self, include_checkarg=True, include_name=True, include_description=True):
        """
        Return a copy of the parameter

        Arguments
        ---------
        include_checkarg : bool
            If include checkargs in new Param
        include_name : bool
            If include name in new Param
        include_description : bool
            If include description in new Param
        """
        repr_str = "%s(value%s%s%s)" % (
            self.__class__.__name__,
            self._check_arg() if include_checkarg else "",
            self._name_arg() if include_name else "",
            self._description_arg() if include_description else "",
        )

        # FIXME: Over load copy in SlaveParam instead?
        if isinstance(self, SlaveParam):
            value = copy.copy(self._expr)
        else:
            value = copy.copy(self._value)

        # Evaluate the repr str with a copy of the value
        return eval(repr_str, globals(), dict(value=value))

    @property
    def description(self):
        return self._description

    def _get_name(self):
        return self._name

    def _set_name(self, name):
        check_arg(name, str)
        if self._name:
            value_error(
                "Cannot set name attribute of %s, it is already set "
                "to '%s'" % (self.__class__.__name__, self._name),
            )
        self._name = name

    def update(self, value):
        self.setvalue(value, False)

    def setvalue(self, value, check=True):
        """
        Try to set the value using the check
        """
        if check:
            self._value = self.check(value)
        else:
            self._value = value

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

        name_str = f" '{self.name}'" if self.name else ""
        if self.value_type in scalars and isinstance(value, scalars):
            if isinstance(value, float) and self.value_type == int:
                info("Converting %s to %d%s", value, int(value), name_str)
            value = self.value_type(value)

        if (
            self.value_type in [bool]
            and isinstance(value, int)
            and not isinstance(value, bool)
        ):
            info(
                "Converting %s to '%s' while setting parameter%s",
                value,
                bool(value),
                name_str,
            )
            value = self.value_type(value)

        if not isinstance(value, self.value_type):
            if self.value_type == nptypes:
                type_name = "scalar or np.ndarray"
            else:
                type_name = self.value_type.__name__
            type_error(f"expected '{type_name}' while setting parameter{name_str}")
        if self._in_range is not None:
            if not self._in_range(value):
                value_error(f"Illegal value{name_str}: {self.format_data(value, True)}")
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
            return self._not_in_str % (value_formatter(value, str_length))
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
        return self.repr()

    def repr(self, include_checkarg=True, include_name=True, include_description=True):
        """
        Returns an executable version of the Param including optional arguments

        Arguments
        ---------
        include_checkarg : bool
            If include checkargs in new Param
        include_name : bool
            If include name in new Param
        include_description : bool
            If include description in new Param
        """

        value_str = (
            str(self._expr)
            if isinstance(self, SlaveParam)
            else value_formatter(self.value)
        )

        return "%s(%s%s%s%s)" % (
            self.__class__.__name__,
            value_str,
            self._check_arg() if include_checkarg else "",
            self._name_arg() if include_name else "",
            self._description_arg() if include_description else "",
        )

    def _name_arg(self):
        return f", name='{self._name}'" if self._name else ""

    def _description_arg(self):
        return f", description='{self._description}'" if self._description else ""

    def _check_arg(self):
        return ""

    def __str__(self):
        """
        Returns a nice representation of the Param
        """
        return self.format_data()

    def convert_to(self, unit):
        """Convert parameter to a different unit than the current one.

        Parameters
        ----------
        unit : str
            The new unit

        Returns
        -------
        Param
            Return the same prameter with the new unit

        Example
        -------

        >>> p_s = ScalarParam(1.0, unit="s")
        >>> p_ms = p_s.convert_to('ms')
        >>> print('value = {}, unit = {}'.format(p_ms.value), p_ms.unit))
        value = 1000.0, unit = 'milliseconds'
        """
        new = ureg(f"{self.value}*{self.unit}").to(unit)
        return self.__class__(value=new.magnitude, unit=format_babel(new))

    def _op(self, other, operator, reverse=False, check_units=False):
        """
        Compute `self [op] other`.
        For example if op = * if will return
        the product in a pint Quantity object.


        Arguments
        ---------
        other : scalar or Param
            The other parameter
        operator : str
            The operator to apply
        reverse : bool
            Reverse the argumnents to the operator, i.e instead
            of `self [op] other` you return `other [op] self`.
            If operator is commutative then this is redundant.
        check_units: bool
            If you are trying to add together quantities with different
            units you are in trouble, but if you are adding a scalar you
            might don't want to throw an exception. Set this to true and
            scalars will be treated as if they had same units.

        Returns
        -------
        results : ScalarParam
            Returns `self [op] other` with correct units and value
        """
        other_value, other_name, other_unit = _process_other(other)

        self_value, self_name, self_unit = _process_other(self)

        assert isinstance(operator, str)

        if check_units:
            # Check if units match up
            if not (ureg(self_unit) == ureg(other_unit)):
                msg = (
                    "Units does not match when computing {} {} {}: "
                    "{} != {}".format(self, operator, other, self_unit, other_unit)
                )
                warning(msg)
                # If one is dimensionless assume that it is OK,
                # and keep the unit of the other
                if self_unit == "1":
                    self_unit = other_unit
                elif other_unit == "1":
                    other_unit = self_unit

        equation = (
            "({self_value}*{self_unit})" "{operator}" "({other_value}*{other_unit})"
        )
        if reverse:
            kwargs = dict(
                other_value=self_value,
                other_unit=self_unit,
                self_value=other_value,
                self_unit=other_unit,
            )
        else:
            kwargs = dict(
                other_value=other_value,
                other_unit=other_unit,
                self_value=self_value,
                self_unit=self_unit,
            )

        kwargs["operator"] = operator
        new = ureg(equation.format(**kwargs))

        return self.__class__(value=new.magnitude, unit=format_babel(new))

    def _cmp(self, other, cmp_op, check_units=True):
        """Compare self and other with custom
        comparison operator


        Parameters
        ----------
        other : Param or scalar
            The parameter you want to compare self to
        cmp_op : str
            Comparison operator

        Returns
        -------
        bool
            Returns the value of `self cmp_op other`.

        """
        other_value, other_name, other_unit = _process_other(other)

        self_value, self_name, self_unit = _process_other(self)

        if check_units:
            # Check if units match up
            if not (ureg(self_unit) == ureg(other_unit)):
                msg = (
                    "Units does not match when comparing {} {} {}: "
                    "{} != {}".format(self, cmp_op, other, self_unit, other_unit)
                )
                warning(msg)
                # If one is dimensionless assume that it is OK,
                # and keep the unit of the other
                if self_unit == "1":
                    self_unit = other_unit
                elif other_unit == "1":
                    other_unit = self_unit

        self_ureg = ureg(f"{self_value}*{self_unit}")  # noqa: F841
        other_ureg = ureg(f"{other_value}*{other_unit}")  # noqa: F841

        return eval(f"self_ureg {cmp_op} other_ureg")

    def __getstate__(self):
        """This is what is saved when you pickle this object."""
        unit = "1" if not hasattr(self, "unit") else self.unit
        return dict(
            name=self.name,
            unit=unit,
            value=self.value,
            description=self.description,
        )

    def __setstate__(self, state):
        """This is how we retrieve the pickled object."""
        self.__class__.__init__(self, **state)

    def __eq__(self, other):
        # return self._cmp(other, "==")
        return _eq(
            isinstance(other, self.__class__)
            and (
                self._name == other._name,
                self._value == other._value,
                self.__class__ == other.__class__,
            ),
        )

    def __lt__(self, other):
        return self._cmp(other, "<")

    def __gt__(self, other):
        return self._cmp(other, ">")

    def __le__(self, other):
        return self._cmp(other, "<=")

    def __ge__(self, other):
        return self._cmp(other, ">=")

    def __truediv__(self, other):
        # Python 3
        return self._op(other, "/")

    def __rtruediv__(self, other):
        # Python 3
        return self._op(other, "/", reverse=True)

    def __div__(self, other):
        # Python 2
        return self._op(other, "/")

    def __rdiv__(self, other):
        # Python 2
        return self._op(other, "/", reverse=True)

    def __mul__(self, other):
        return self._op(other, "*")

    def __rmul__(self, other):
        return self._op(other, "*", reverse=True)

    def __add__(self, other):
        return self._op(other, "+", check_units=True)

    def __radd__(self, other):
        return self._op(other, "+", reverse=True, check_units=True)

    def __sub__(self, other):
        return self._op(other, "-", check_units=True)

    def __rsub__(self, other):
        return self._op(other, "-", reverse=True, check_units=True)

    def __pow__(self, other):
        other_value, other_name, other_unit = _process_other(other)
        assert other_unit == "1", "Exponents cannot have unit"

        self_value, self_name, self_unit = _process_other(self)
        new = ureg(f"({self_value}*{self_unit})**{other_value}")
        return self.__class__(value=new.magnitude, unit=format_babel(new))

    def __abs__(self):
        return abs(self.value)


def format_babel(new):
    try:
        return new.u.format_babel()
    except ValueError:
        # Babel is not installed
        return str(new.u)
    except TypeError:
        # Babel is not able to format the expression
        return str(new.u)


class OptionParam(Param):
    """
    A simple type and options checking class for a single value
    """

    def __init__(self, value, options, name="", description=""):
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
        description : str (optional)
            A description associated with the Parameter
        """
        check_arg(options, list)
        if len(options) < 2:
            value_error("expected the options argument to be at least of length 2")

        super(OptionParam, self).__init__(value, name, description)

        # Check valid types for an 'option check'
        for option in options:
            if not isinstance(option, option_types):
                type_error(
                    "options can only be 'str' and scalars got: '%s'"
                    % type(option).__name__,
                )

        # Define a 'check function'
        self._in_range = lambda value: value in options

        # Define some string used for pretty print
        self._in_str = b"%%s \xe2\x88\x88 %s".decode("utf-8") % repr(options)
        self._not_in_str = b"%%s \xe2\x88\x89 %s".decode("utf-8") % repr(options)

        # Define a 'repr string'
        # self._repr_str = "OptionParam(%%s, %s)" % repr(options)

        # Set the value using the check functionality
        self.setvalue(value)

        # Check that all values in options has the same type
        for val in options:
            if not isinstance(val, self.value_type):
                type_error(
                    "All values of the 'option check' "
                    + f"need to be of type: '{type(self._value).__name__}'",
                )

        # Store options
        self._options = options

    def _check_arg(self):
        return f", {repr(self._options)}"

    def __eq__(self, other):
        return _eq(
            isinstance(other, self.__class__)
            and (
                self._name == other._name,
                self._value == other._value,
                self.__class__ == other.__class__,
                self._options == other._options,
            ),
        )

    def repr(self, include_checkarg=True, include_name=True, include_description=True):
        """
        Returns an executable version of the Param including optional arguments

        Arguments
        ---------
        include_checkarg : bool
            If include checkargs in new Param
        include_name : bool
            If include name in new Param
        include_description : bool
            If include description in new Param
        """
        if not include_checkarg:
            warning("'include_checkarg' must be 'True' in OptionParam.repr.")
            include_checkarg = True

        return super(OptionParam, self).repr(
            include_checkarg,
            include_name,
            include_description,
        )


class ConstParam(Param):
    """
    A Constant parameter which prevent any change of values
    """

    def __init__(self, value, name="", description=""):
        """
        Initialize the ConstParam

        Arguments
        ---------
        value : scalars or str
            The initial value of this parameter. The type of value is stored
            for future type checks
        name : str (optional)
            The name of the parameter. Used in pretty printing
        description : str (optional)
            A description associated with the Parameter
        """
        Param.__init__(self, value, name, description)

        # Define a 'check function'
        self._in_range = lambda x: x == self._value

        # Define some string used for pretty print
        self._in_str = "%s - Constant"
        self._not_in_str = "%%s != %s" % self._value
        self.setvalue(value)


class TypelessParam(Param):
    """
    A Typeless parameter allowing any change of value, including type changes
    """

    def __init__(self, value, name="", description=""):
        """
        Initialize the TypelessParam

        Arguments
        ---------
        value : scalars or str
            The initial value of this parameter. The type of value is stored
            for future type checks
        name : str (optional)
            The name of the parameter. Used in pretty printing
        description : str (optional)
            A description associated with the Parameter
        """
        Param.__init__(self, value, name, description)

        # Set allowed types to all Python objects
        self.value_type = object


class ScalarParam(Param):
    """
    A simple type and range checking class for a scalar value
    """

    def __init__(
        self,
        value,
        ge=None,
        le=None,
        gt=None,
        lt=None,
        unit="1",
        name="",
        description="",
    ):
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
        description : str (optional)
            A description associated with the Parameter
        """
        if isinstance(value, Param):
            param_value, param_name, param_unit = _process_other(value)
            if unit == "1":
                unit = param_unit
            value = param_value

        check_arg(value, scalars, 0, ScalarParam)
        super(ScalarParam, self).__init__(value, name, description)

        self._range = Range(ge, le, gt, lt)
        self._in_range = self._range._in_range

        check_kwarg(unit, "unit", str)
        self._unit = unit

        # Define some string used for pretty print
        self._in_str = self._range._in_str
        self._not_in_str = self._range._not_in_str

        # Create symbol
        if name == "":
            self._sym = dummy_sym
        elif sp is None:
            self._sym = None
        else:
            self._sym = sp.Symbol(
                name,
                real=True,
                imaginary=False,
                commutative=True,
                hermitian=True,
                complex=True,
            )

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
        check_arg(name, str)

        super(ScalarParam, self)._set_name(name)

        if sp is None:
            return

        # Create a new symbol with the updated name
        self._sym = sp.Symbol(
            name,
            real=True,
            imaginary=False,
            commutative=True,
            hermitian=True,
            complex=True,
        )

        # Store parameter
        store_symbol_parameter(self)

    def copy(
        self,
        include_checkarg=True,
        include_name=True,
        include_description=True,
        include_unit=True,
    ):
        """
        Return a copy of the parameter

        Arguments
        ---------
        include_checkarg : bool
            If include checkargs in new Param
        include_name : bool
            If include name in new Param
        include_description : bool
            If include description in new Param
        include_unit : bool
            If include unit in new Param
        """
        repr_str = "%s(value%s%s%s%s)" % (
            self.__class__.__name__,
            self._check_arg() if include_checkarg else "",
            self._unit_arg() if include_unit else "",
            self._name_arg() if include_name else "",
            self._description_arg() if include_description else "",
        )

        # FIXME: Over load copy in SlaveParam instead?
        if isinstance(self, SlaveParam):
            value = copy.copy(self._expr)
        else:
            value = copy.copy(self._value)

        # Evaluate the repr str with a copy of the value
        return eval(repr_str, globals(), dict(value=value))

    def repr(
        self,
        include_checkarg=True,
        include_name=True,
        include_description=True,
        include_unit=True,
    ):
        """
        Returns an executable version of the Param including optional arguments

        Arguments
        ---------
        include_checkarg : bool
            If include checkargs in new Param
        include_name : bool
            If include name in new Param
        include_description : bool
            If include description in new Param
        include_unit : bool
            If include unit in new Param
        """

        value_str = (
            str(self._expr)
            if isinstance(self, SlaveParam)
            else value_formatter(self.value)
        )

        return "%s(%s%s%s%s%s)" % (
            self.__class__.__name__,
            value_str,
            self._check_arg() if include_checkarg else "",
            self._unit_arg() if include_unit else "",
            self._name_arg() if include_name else "",
            self._description_arg() if include_description else "",
        )

    def update(self, param):
        """
        Update parameter with value of new parameter.
        Take into account unit conversion if applicable.

        Arguments
        ---------
        param : ScalarParameter or scalar
            The parameter with the new value
        """

        check_arg(param, scalars + (ScalarParam,))

        msg = f"Update parameter {self._get_name()}. "
        debug(msg)
        self_value, self_name, self_unit = _process_other(self)
        param_value, param_name, param_unit = _process_other(param)

        if param_unit == "1":
            # Assume same Units
            param_unit = self_unit
        if self_unit == "1":
            # Make the new unit the same as the given paramevter
            self_unit = param_unit

        # Convert to same unit as self
        quantity = ureg(f"{param_value}*{param_unit}").to(self_unit)

        return self.setvalue(quantity.m)

    def _unit_arg(self):
        return f", unit='{self._unit}'" if self._unit != "1" else ""

    def get_sym(self):
        return self._sym

    name = property(_get_name, _set_name)
    sym = property(get_sym)

    @property
    def unit(self):
        """
        Return the unit
        """
        return self._unit

    def _check_arg(self):
        """
        Return a repr of the check arguments
        """
        if self._range.arg_repr_str:
            return ", " + self._range.arg_repr_str
        return ""

    def __eq__(self, other):
        return _eq(
            isinstance(other, self.__class__)
            and (
                self._name == other._name,
                self._value == other._value,
                self.__class__ == other.__class__,
                self._range == other._range,
            ),
        )


class ArrayParam(ScalarParam):
    """
    A numpy Array based parameter
    """

    def __init__(
        self,
        value,
        size=None,
        ge=None,
        le=None,
        gt=None,
        lt=None,
        unit="1",
        name="",
        description="",
    ):
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
        description : str (optional)
            A description associated with the Parameter
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
            value = np.array(
                [value] * size,
                dtype=np.intc if isinstance(value, integers) else np.float_,
            )

        # If setting value using only value argument
        else:

            # Allow using list of scalars
            if isinstance(value, list):
                check_arg(value, list, 0, ArrayParam, scalars)
                if len(value) == 0:
                    value_error("expected a list with at least 1 element")
                value = np.fromiter(value, dtype=type(value[0]))

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
                type_error(
                    "expected a scalar or a scalar valued np.ndarray"
                    "or list as value argument.",
                )

        # Init super class with dummy value
        super(ArrayParam, self).__init__(
            value[0],
            ge,
            le,
            gt,
            lt,
            unit,
            name,
            description,
        )

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
        index = slice(0, len(self._value) + 1)

        # Tuple means index assignment
        # FIXME: Add support for slices
        if isinstance(value, tuple):
            if len(value) != 2:
                value_error(
                    "expected a tuple of length 2 when assigning " "single items",
                )
            if not isinstance(value[0], integers):
                value_error(
                    "expected first value in index assignment to be" " an integer",
                )
            if not isinstance(value[1], scalars):
                value_error(
                    "expected second value in index assignment to be" " an scalar",
                )
            index = value[0]
            value = value[1]

        check_arg(value, nptypes, context=ArrayParam.setvalue)

        if isinstance(value, np.ndarray):
            if len(value) != len(self._value):
                value_error(
                    "expected the passed array to be of "
                    "size: '%d'" % len(self._value),
                )

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

    def __init__(self, expr, unit="1", name="", description=""):

        if sp is None:
            error("sympy is not installed so SlaveParam is not available")

        if not isinstance(expr, (ScalarParam, sp.Basic)):
            type_error("expected an expression of model symbols.")

        if isinstance(expr, ScalarParam):
            expr = expr.sym

        if not all(
            isinstance(atom, (sp.NumberSymbol, sp.Number, sp.Symbol, sp.Dummy))
            for atom in expr.atoms()
        ):
            type_error("expected expression of model symbols.")

        ScalarParam.__init__(self, 0.0, name=name, description=description, unit=unit)

        # Store the original expression used to evaluate the value of
        # the SlaveParam
        self._expr = expr

        # Store parameters that are available at the time of construction
        # FIXME: Does not work...
        # self._param_ns = {}
        # for symbol in symbols_from_expr(expr, include_derivatives=True):
        #    try:
        #        self._param_ns[sympycode(symbol)] = symbol_to_param(symbol)
        #    except:
        #        pass

    def setvalue(self, value):
        """
        A setvalue method which always fails
        """
        type_error("cannot assign to a SlaveParam")

    def getvalue(self):
        """
        Return a computed value of the Parameters
        """
        timer = Timer("Eval Slave parameter")  # noqa: F841

        return eval_param_expr(self._expr, include_derivatives=True)

        # FIXME: Does not work...
        # return eval_param_expr(self._expr, param_ns=self._param_ns, \
        #                       include_derivatives=True)

    value = property(getvalue, setvalue)

    @property
    def expr(self):
        """
        Return the stored expression
        """
        return self._expr

    def format_data(self, value=None, not_in=False, str_length=0):
        "Print a nice formated version of the value and its range"

        # If no '_in_str' is defined
        return "%s - SlaveParam(%s)" % (
            value_formatter(self.getvalue(), str_length),
            str(self._expr),
        )


def eval_param_expr(expr, param_ns=None, include_derivatives=False, ns=None):
    """
    Eval an expression of symbols of ScalarParam

    Arguments
    ---------
    expr : expression of ParamSymbols
        The expression to be evaulated
    param_ns : dict (optional)
        A namespace containing the parameters for which the expr should be
        evaluated with.
    include_derivatives : bool (optional)
        If True not only symbols are evaulated but also derivatives
    ns : dict (optional)
        A namespace in which the expression will be evaluated in
    """

    if sp is None:
        error("sympy is not installed so evaluation of expressions" " is not available")

    # Create name space which the expression will be evaluated in
    ns = ns or {}

    # Get values
    if param_ns is None:
        value_ns = value_namespace(expr, include_derivatives=include_derivatives)
    else:

        value_ns = {}
        for symbol in symbols_from_expr(expr, include_derivatives=include_derivatives):

            sym_name = sympycode(symbol)

            # First try to get param from passed param_ns
            param = param_ns.get(sym_name)

            # If not available try to get it from the global dict
            if param is None:
                param = symbol_to_param(symbol)

                # And store it for future usage
                # param_ns[sym_name] = param

            # Store value
            value_ns[sym_name] = param.value

    # First check if we have numpy arrays
    if np and any(isinstance(value, np.ndarray) for value in list(value_ns.values())):

        # Second check if they have the same length
        all_length = [
            len(value)
            for value in list(value_ns.values())
            if isinstance(value, np.ndarray)
        ]
        same_length = all(all_length[0] == l_ for l_ in all_length)
        if not same_length:
            value_error(
                "expected all ArrayParams in an expression " "to be of equal size.",
            )

        # Update name space with numpy name space
        namespace = "np"
        ns["np"] = np

    else:

        # No numpy arrays and we choose math name space to evaulate expression
        import math

        namespace = "math"
        ns["math"] = math

    # Update namespace with values
    ns.update(value_ns)

    return eval(pythoncode(expr, namespace=namespace), {}, ns)


__all__ = [_name for _name in list(globals().keys()) if _name[0] != "_"]
