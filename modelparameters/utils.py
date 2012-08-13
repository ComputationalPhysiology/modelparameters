__author__ = "Johan Hake (hake.dev@gmail.com)"
__copyright__ = "Copyright (C) 2010 " + __author__
__date__ = "2010-09-22 -- 2012-08-13"
__license__  = "GNU LGPL Version 3.0 or later"

# System imports

# Conditional numpy dependency
try:
    import numpy as _np
    list_types = (_np.ndarray, list)
    scalars = tuple(t for t in _np.ScalarType if not (issubclass(t, basestring) or \
                                                      t is _np.void))
    integers = tuple(t for t in scalars if "int" in t.__name__) + (int,)
    nptypes = (scalars, _np.ndarray)
    range_types = scalars + (_np.ndarray,)
    _all = _np.all
except Exception, e:
    print e
    _np = None
    list_types = (list,)
    scalars = (int, float)
    integers = (int,)
    nptypes = ()
    range_types = scalars 
    _all = lambda value : value

import time as _time
import math as _math
import types as _types
import string as _string

# local imports
from logger import *
from config import float_format

_toc_time = 0.0

_argument_positions = ["first", "second", "third", "fourth", "fifth", "sixth",\
                       "seventh", "eigth", "ninth", "tenth"]

VALUE_JUST = _string.rjust
inf = float("inf")

def value_formatter(value, width=0):
    """
    Return a formated string of a value

    Arguments
    ---------
    value : any
        The value which is formatted
    width : int
        A min str length value
    """
    ret = None
    if isinstance(value, list_types):
        if len(value)>4:
            if isinstance(value[0], integers):
                formatstr = "[%d, %d, ..., %d, %d]"
            elif isinstance(value[0], scalars):
                formatstr = "[%%.%(ff)s, %%.%(ff)s, ..., %%.%(ff)s, %%.%(ff)s]" % \
                            float_format()
            else:
                formatstr = "[%s, %s, ..., %s, %s]"
            ret = formatstr % (value[0], value[1], value[-2], value[-1])
        elif len(value) == 0:
            ret = "[]"
        else:
            if isinstance(value[0], integers):
                formatstr = "%d"
            elif isinstance(value[0], scalars):
                formatstr = "%%.%(ff)s" % float_format()
            else:
                formatstr = "%s"

            formatstr = "[%s]" % (", ".join(formatstr for i in range(len(value))) )
            ret = formatstr % tuple(value)
    
    elif isinstance(value, float):
        if value == inf:
            ret = "\xe2\x88\x9e"
        elif value == -inf:
            ret = "-\xe2\x88\x9e"
    
    elif isinstance(value, str):
        ret = repr(value)
        
    if ret is None:
        ret = str(value)
    
    if width == 0:
        return ret
    return VALUE_JUST(ret, width)

class Range(object):
    """
    A simple class for helping checking a given value is within a certain range
    """
    def __init__(self, ge=None, le=None, gt=None, lt=None):
        """
        Create a Range

        Arguments
        ---------
        ge : scalar (optional)
            Greater than or equal, range control of argument
        le : scalar (optional)
            Lesser than or equal, range control of argument
        gt : scalar (optional)
            Greater than, range control of argument
        lt : scalar (optional)
            Lesser than, range control of argument
        """
        ops = [ge, gt, le, lt]
        opnames = ["ge", "gt", "le", "lt"]

        # Checking valid combinations of kwargs
        if le is not None and lt is not None:
            value_error("Cannot create a 'Range' including "\
                        "both 'le' and 'lt'")
        if ge is not None and gt is not None:
            value_error("Cannot create a 'Range' including "\
                        "both 'ge' and 'gt'")
        
        # Checking valid types for 'RangeChecks'
        for op, opname in zip(ops, opnames):
            if not (op is None or isinstance(op, scalars)):
                type_error("expected a scalar for the '%s' arg" % opname)

        # get limits
        minval = gt if gt is not None else ge if ge is not None else -inf
        maxval = lt if lt is not None else le if le is not None else inf

        if minval > maxval:
            value_error("expected the maxval to be larger than minval")

        # Dict for test and repr
        range_formats = {}
        range_formats["minop"] = ">=" if gt is None else ">"
        range_formats["maxop"] = "<=" if lt is None else "<"
        range_formats["minvalue"] = str(minval)
        range_formats["maxvalue"] = str(maxval)
        
        # Dict for pretty print
        range_formats["minop_format"] = "[" if gt is None else "("
        range_formats["maxop_format"] = "]" if lt is None else ")"
        range_formats["minformat"] = value_formatter(minval)
        range_formats["maxformat"] = value_formatter(maxval)

        self._in_range = eval(("lambda value : _all(value %(minop)s %(minvalue)s) "\
                               "and _all(value %(maxop)s %(maxvalue)s)")%\
                              range_formats)
        
        # Define some string used for pretty print
        self._range_str = "%(minop_format)s%(minformat)s, "\
                          "%(maxformat)s%(maxop_format)s" % range_formats
        
        self._in_str = "%%s \xe2\x88\x88 %s" % self._range_str
        
        self._not_in_str = "%%s \xe2\x88\x89 %s" % self._range_str

        self.arg_repr_str = ", ".join("%s=%s" % (opname, op) \
                                      for op, opname in zip(ops, opnames) \
                                      if op is not None)

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.arg_repr_str)

    def __str__(self):
        return self._range_str

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
               self._in_str == other._in_str

    def __contains__(self, value):
        """
        Return True of value is in range

        Arguments
        ---------
        value : scalar%s
            A value to be used in checking range
        """ % ("" if _np is None else " and np.ndarray")
        if not isinstance(value, range_types):
            type_error("only scalars%s can be ranged checked" % \
                       ("" if _np is None else " and np.ndarray"))
        return self._in_range(value)

    def format(self, value, width=0):
        """
        Return a formated range check of the value

        Arguments
        ---------
        value : scalar
            A value to be used in checking range
        width : int
            A min str length value
        """
        in_range = self.__contains__(value)
        
        if value in self:
            return self.format_in(value, width)
        return self.format_not_in(value, width)
        
    def format_in(self, value, width=0):
        """
        Return a formated range check 

        Arguments
        ---------
        value : scalar
            A value to be used in checking range
        width : int
            A min str length value
        """
        
        return self._in_str % value_formatter(value, width)

    def format_not_in(self, value, width=0):
        """
        Return a formated range check

        Arguments
        ---------
        value : scalar
            A value to be used in checking range
        width : int
            A min str length value
        """
        
        return self._not_in_str % value_formatter(value, width)
        
    
def _floor(value):
    return int(_math.floor(value))

def format_time(time):
    """
    Return a formated version of the time argument

    Arguments
    ---------
    time : float
        Time given in sections
    """
    minutes = _floor(time/60)
    seconds = _floor(time%60)
    if minutes == 0:
        return "%d s"%seconds
    seconds_str =  " %d s" % seconds if seconds else ""

    hours = _floor(minutes/60)
    minutes = _floor(minutes%60)
    if hours == 0:
        return "%d m%s"%(minutes, seconds_str)
    minutes_str =  " %d m" % minutes if minutes else ""

    days = _floor(hours/24)
    hours = _floor(hours%24)
    
    if days == 0:
        return "%d h%s%s"%(hours, minutes_str, seconds_str)
    hours_str =  " %d h" % hours if hours else ""

    return "%d day%s%s%s%s"%(days, "s" if days>1 else "", hours_str, \
                             minutes_str, seconds_str)

def tic():
    """
    Start timing
    """
    global _toc_time
    _toc_time = _time.time()

def toc():
    """
    Return timing since last toc/tic
    """
    global _toc_time
    old_toc_time = _toc_time
    _toc_time = _time.time()
    return _toc_time - old_toc_time

def is_iterable(obj):
    """
    Test for iterable

    Argument:
    obj : any
        Object which is beeing tested
    """
    try:
        iter(obj)
        return True
    except Exception, e:
        pass
    return False

def add_iterable(iterable, initial=None):
    """
    Sum the content of an iterable
    """
    from operator import add
    if not is_iterable(iterable):
        error("expected an iterable")
    if initial is None:
        return reduce(add, iterable)
    return reduce(add, iterable, initial)

def camel_capitalize(name):
    """
    Camel capitalize a str
    """
    check_arg(name, str, context=camel_capitalize)
    return "".join(n.capitalize() for n in name.split("_"))

def tuplewrap(arg):
    """
    Wrap the argument to a tuple if it is not a tuple
    """
    if arg is None:
        return ()
    return arg if isinstance(arg, tuple) else (arg,)
    
def listwrap(arg):
    """
    Wrap the argument to a list if it is not a list
    """
    if arg is None:
        return []
    return arg if isinstance(arg, list) else [arg,]

def _context_message(context):
    """
    Help function to add context information to error message
    """
    # Add contexttual information if passed
    if context is None:
        return ""

    assert(isinstance(context, (type, _types.ClassType, _types.FunctionType, \
                                _types.MethodType)))
        
    if isinstance(context, (_types.ClassType, type)):
        return " while instantiating '{0}'".format(context.__name__)

    if isinstance(context, (_types.MethodType)):
        return " while calling '{0}.{1}'".format(\
            context.im_class.__name__, context.im_func.func_name)

    return " while calling '{0}'".format(context.func_name)

def _range_check(arg, argtype, ge, le, gt, lt):

    # First check if we are interested in any range check
    if all(comp is None for comp in [ge, le, gt, lt]):

        # Return empty string 
        return ""

    # Check we want a scalar
    if isinstance(argtype, tuple):
        assert(all(argtype_item in range_types for argtype_item in argtype))
    else:
        assert(argtype in range_types)

    range_checker = Range(ge, le, gt, lt)
    if arg in range_checker:
        return ""
    return range_checker.format_not_in(arg)

def _check_arg(arg, argtype, identifyer, context, itemtypes, ge, le, gt, lt):
    """
    Helper function for arg checking
    """
    assert(isinstance(argtype, (tuple, type)))

    # First check for correct range
    message = _range_check(arg, argtype, ge, le, gt, lt)
    
    # If we have a message we failed the range check
    if message:

        raise_error = value_error
        
    # Check the argument
    elif isinstance(arg, argtype):
        if itemtypes is None or not isinstance(arg, (list, tuple)):
            return
        iterativetype = type(arg).__name__
        assert(isinstance(itemtypes, (type, tuple)))
        if all(isinstance(item, itemtypes) for item in arg):
            return
        
        itemtypes = tuplewrap(itemtypes)
        
        message = "expected a '%s' of '%s'"%(iterativetype,\
                                ", ".join(argt.__name__ for argt in itemtypes))
        raise_error = type_error
    else:
        argtype = tuplewrap(argtype)
        if argtype == integers:
            argtype_str = "integer"
        elif argtype == scalars:
            argtype_str = "scalar"
        elif argtype == nptypes:
            argtype_str = "scalar or np.ndarray"
        else:
            argtype_str = ", ".join(argt.__name__ for argt in argtype)
        message = "expected a '%s' (got '%s' which is '%s')"%\
                  (argtype_str, arg, type(arg).__name__)
        raise_error = type_error

    # Add identifyer information if passed
    if isinstance(identifyer, int) and identifyer != -1:
        message += " as the %s argument" % _argument_positions[identifyer]
    elif isinstance(identifyer, str):
        message += " as the '%s' argument" % identifyer

    # Add context message
    message += _context_message(context)

    # Display error message
    raise_error(message)

def check_arg(arg, argtype, num=-1, context=None, itemtypes=None,
              ge=None, le=None, gt=None, lt=None):
    """
    Type check for positional arguments

    Arguments
    ---------
    arg : any
        The argument to be checked
    argtype : type, tuple
        The type of which arg should be
    num : int (optional)
        The argument positional number
    context : type, function/method (optional)
        The context of the check. If context is a class the check is
        assumed to be during creation. If a function/method the contex is
        assumed to be a call to that function/method
    itemtypes : type (optional)
        If given argtype must be a tuple or list and itemtypes forces each item
        to be a certain type
    ge : scalar (optional)
        Greater than or equal, range control of argument
    le : scalar (optional)
        Lesser than or equal, range control of argument
    gt : scalar (optional)
        Greater than, range control of argument
    lt : scalar (optional)
        Lesser than, range control of argument
    """
    assert(isinstance(num, int))
    _check_arg(arg, argtype, num, context, itemtypes, ge, le, gt, lt)


def check_kwarg(kwarg, name, argtype, context=None, itemtypes=None,
                ge=None, le=None, gt=None, lt=None):
    """
    Type check for keyword arguments

    Arguments
    ---------
    kwarg : any
        The keyword argument to be checked
    name : str
        The name of the keyword argument
    argtype : type, tuple
        The type of which arg should be
    context : type, function/method (optional)
        The context of the check. If context is a class the check is
        assumed to be during creation. If a function/method the contex is
        assumed to be a call to that function/method
    itemtypes : type (optional)
        If given argtype must be a tuple or list and itemtypes forces each item
        to be a certain type
    ge : scalar (optional)
        Greater than or equal, range control of argument
    le : scalar (optional)
        Lesser than or equal, range control of argument
    gt : scalar (optional)
        Greater than, range control of argument
    lt : scalar (optional)
        Lesser than, range control of argument
    """
    assert(isinstance(name, str) and len(name)>0)
    _check_arg(kwarg, argtype, name, context, itemtypes, ge, le, gt, lt)

def quote_join(list_of_str):
    """
    Join a list of strings with quotes and commans
    """
    assert(isinstance(list_of_str, (tuple, list)))
    assert(all(isinstance(item, str) for item in list_of_str))
    return ", ".join(["'%s'"%item for item in list_of_str])

__all__ = [_name for _name in globals().keys() if _name[0] != "_"]

