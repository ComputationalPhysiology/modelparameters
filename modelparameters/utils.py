__author__ = "Johan Hake (hake.dev@gmail.com)"
__copyright__ = "Copyright (C) 2010 " + __author__
__date__ = "2010-09-22 -- 2012-06-30"
__license__  = "GNU LGPL Version 3.0 or later"

# System imports
import time as _time
import math as _math
import types as _types
import numpy as np
from numpy import inf


# local imports
from logger import *

# Define scalars
scalars = np.ScalarType

_toc_time = 0.0

_argument_positions = ["first", "second", "third", "fourth", "fifth", "sixth",\
                       "seventh", "eigth", "ninth", "tenth"]

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
    if minutes < 1:
        return "%d s"%seconds
    hours = _floor(minutes/60)
    minutes = _floor(minutes%60)
    if hours < 1:
        return "%d m %d s"%(minutes, seconds)
    
    days = _floor(hours/24)
    hours = _floor(hours%24)
    
    if days < 1:
        return "%d h %d m %d s"%(hours, minutes, seconds)

    return "%d days %d h %d m %d s"%(days, hours, minutes, seconds)

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
    arg_check(name, str, context=camel_capitalize)
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

def _range_check(arg, argtype, gt, ge, lt, le):

    # First check if we are interested in any range check
    if all(comp is None for comp in [gt, ge, lt, le]):

        # Return empty string 
        return ""

    # Check we want a scalar
    if isinstance(argtype, tuple):
        assert(all(argtype_item in scalars for argtype_item in argtype))
    else:
        assert(argtype in scalars)

    # Checking valid combinations of kwargs
    assert(not all([ge, gt]))
    assert(not all([le, lt]))

    # Check for valid type
    if not isinstance(arg, argtype):
        
        # Return almost empty string
        return ""

    # Checking valid types for 'range checks'
    wrong_range_check_type = False
    for value in [ge, le, gt, lt]:
        if not value is None:
            wrong_range_check_type |= not isinstance(value, scalars)
                
    assert(not wrong_range_check_type)
    
    # Pick the min and max values
    if not ge is None:
        min_val = ge
    elif not gt is None:
        min_val = gt
    else:
        min_val = -inf
    
    if not le is None:
        max_val = le
    elif not lt is None:
        max_val = lt
    else:
        max_val = inf

    # Check the relation between the min and max value
    if min_val > max_val:
        error("Please provide a 'max value' that is "\
              "larger than the 'min value'.")
    
    range_check_dict = {}

    # Dict for test and repr
    range_check_dict["min_op"] = ">=" if gt is None else ">"
    range_check_dict["max_op"] = "<=" if lt is None else "<"
    range_check_dict["min_value"] = str(min_val)
    range_check_dict["max_value"] = str(max_val)
    range_check_dict["value"] = arg
    
    # Define a 'check function'
    if eval(("%(value)f %(min_op)s %(min_value)s "\
             "and %(value)f %(max_op)s %(max_value)s")%\
            range_check_dict):
        return ""
    
    # Dict for pretty print
    from parcheck import value_formatter
    range_check_dict["min_op_format"] = "[" if gt is None else "("
    range_check_dict["max_op_format"] = "]" if lt is None else ")"
    range_check_dict["min_format"] = value_formatter(min_val)
    range_check_dict["max_format"] = value_formatter(max_val)
    range_check_dict["value"] = value_formatter(arg)

    return "%(value)s \xe2\x88\x89 %(min_op_format)s%(min_format)s"\
           ", %(max_format)s%(max_op_format)s" % range_check_dict
    
def check_arg(arg, argtype, num=-1, context=None, itemtype=None,
              gt=None, ge=None, lt=None, le=None):
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
    itemtype : type (optional)
        If given argtype must be a tuple or list and itemtype forces each item
        to be a certain type
    gt : scalar (optional)
        Greater than, range control of argument
    ge : scalar (optional)
        Greater than or equal, range control of argument
    lt : scalar (optional)
        Lesser than, range control of argument
    le : scalar (optional)
        Lesser than or equal, range control of argument
    """
    assert(isinstance(argtype, (tuple, type)))

    # First check for correct range
    message = _range_check(arg, argtype, gt, ge, lt, le)
    
    # If we have a message we failed the range check
    if message:

        raise_error = value_error
        
    # Check the argument
    elif isinstance(arg, argtype):
        if itemtype is None or not isinstance(arg, (list, tuple)):
            return
        iterativetype = type(arg).__name__
        assert(isinstance(itemtype, (type, tuple)))
        if all(isinstance(item, itemtype) for item in arg):
            return
        
        assert(isinstance(num, int))
        itemtype = tuplewrap(itemtype)
        
        message = "expected a '%s' of '%s'"%(iterativetype,\
                                ", ".join(argt.__name__ for argt in itemtype))
        raise_error = type_error
    else:
        assert(isinstance(num, int))
        argtype = tuplewrap(argtype)
        message = "expected a '%s' (got '%s' which is '%s')"%\
                  (", ".join(argt.__name__ for argt in argtype), \
                   str(arg), type(arg).__name__)
        raise_error = type_error

    # Add positional information if passed
    if num != -1:
        message += " as the %s argument"%(_argument_positions[num])

    # Add context message
    message += _context_message(context)

    # Display error message
    raise_error(message)

def check_kwarg(kwarg, name, argtype, context=None, itemtype=None,
              gt=None, ge=None, lt=None, le=None):
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
    itemtype : type (optional)
        If given argtype must be a tuple or list and itemtype forces each item
        to be a certain type
    gt : scalar (optional)
        Greater than, range control of argument
    ge : scalar (optional)
        Greater than or equal, range control of argument
    lt : scalar (optional)
        Lesser than, range control of argument
    le : scalar (optional)
        Lesser than or equal, range control of argument
    """
    assert(isinstance(argtype, (tuple, type)))
    
    # First check for correct range
    message = _range_check(arg, argtype, gt, ge, lt, le)
    
    # If we have a message we failed the range check
    if message:
        pass

    elif isinstance(kwarg, argtype):
        if itemtype is None or not isinstance(kwarg, (list, tuple)):
            return
        iterativetype = type(kwarg).__name__
        assert(isinstance(itemtype, (type, tuple)))
        if all(isinstance(item, itemtype) for item in kwarg):
            return
        
        assert(isinstance(num, int))
        message = "expected a '%s' of '%s'"%(iterativetype, itemtype.__name__)
    else:
        assert(isinstance(name, str))
        argtype = tuplewrap(argtype)
        message = "expected a '%s'"%(", ".join(argt.__name__ \
                                               for argt in argtype))
    
    message += " as the '%s' argument"%name

    # Add context message
    message += _context_message(context)

    # Display error message
    error(message)

def quote_join(list_of_str):
    """
    Join a list of strings with quotes and commans
    """
    assert(isinstance(list_of_str, (tuple, list)))
    assert(all(isinstance(item, str) for item in list_of_str))
    return ", ".join(["'%s'"%item for item in list_of_str])

__all__ = [_name for _name in globals().keys() if _name[0] != "_"]

