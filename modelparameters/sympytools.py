__author__ = "Johan Hake <hake.dev@gmail.com>"
__date__ = "2012-06-29 -- 2012-08-31"
__copyright__ = "Copyright (C) 2008-2012 " + __author__
__license__  = "GNU LGPL Version 3.0 or later"

# System imports
import sympy as sp

from sympy.printing import StrPrinter as _StrPrinter

from sympy.core import relational

# Local imports
from utils import check_arg
from logger import warning, error, value_error, type_error

class _ModelParameterPrinter(_StrPrinter):
    """
    Custom printer for sympy expressions
    """
    def _print_ModelSymbol(self, expr):
        return expr.abbrev

_printer = _ModelParameterPrinter()

# Update printer
sp.Basic.__str__ = lambda self: _printer.doprint(self)
sp.Basic.__repr__ = lambda self: _printer.doprint(self)

class ModelSymbol(sp.Symbol):
    """
    Class for all Symbols used in ScalarParam
    """

    __slots__ = ("abbrev",)

    def __new__(cls, name, abbrev, **assumptions):
        obj = sp.Symbol.__new__(cls, name, **assumptions)
        assert isinstance(name, str),repr(type(name))
        assert isinstance(abbrev, str),repr(type(abbrev))
        obj.abbrev = abbrev

        return obj

    def __getnewargs__(self):
        return (self.name, self.abbrev)

    def __eq__(self, other):
        return isinstance(other, ModelSymbol) and self.abbrev == other.abbrev

    def __hash__(self):
        return super(ModelSymbol, self).__hash__()

    def _hashable_content(self):
        return (self.name, self.abbrev)

def Conditional(cond, true_value, false_value):
    """
    Declares a conditional

    Arguments
    ---------
    cond : A conditional
        The conditional which should be evaluated
    true_value : Any model expression
         Model expression for a true evaluation of the conditional
    false_value : Any model expression
         Model expression for a false evaluation of the conditional
    """
    return sp.functions.Piecewise((true_value, cond), (false_value, True))

# Collect all parameters
_all_symbol_parameters = {}

def store_symbol_parameter(param):
    """
    Store a symbol parameter
    """
    from parameters import ScalarParam
    check_arg(param, ScalarParam)
    sym = param.sym
    if str(sym) in _all_symbol_parameters:
        warning("Parameter with symbol name '%s' already "\
                "excist" % sym)
    _all_symbol_parameters[str(sym)] = param

def symbol_to_params(sym):
    """
    Take a symbol or expression of symbols and returns the corresponding
    Parameters
    """
    if sp is None:
        error("sympy is needed for symbol_to_params to work.")
        
    check_arg(sym, ModelSymbol, context=symbol_to_params)
    param = _all_symbol_parameters.get(str(sym))

    if param is None:
        value_error("No parameter with name '{0}' "\
                    "registered. Remember to declare Params which should be "\
                    "used in expression with names.".format(sym.abbrev))
    return param

def symbol_params_from_expr(expr):
    """
    Return a list of ModelSymbols from expr
    """
    check_arg(expr, sp.Basic)
    return [atom for atom in expr.atoms() if isinstance(atom, ModelSymbol)]

def iter_symbol_params_from_expr(expr):
    """
    Return an iterator over ModelSymbols from expr
    """
    check_arg(expr, sp.Basic)
    return (atom for atom in expr.atoms() if isinstance(atom, ModelSymbol))

def symbol_param_value_namespace(expr):
    """
    Extract a list of ModelSymbols from expr
    """
    check_arg(expr, sp.Basic)
    return dict((str(symbol_param), symbol_to_params(symbol_param).value) \
                for symbol_param in iter_symbol_params_from_expr(expr))


# Create a sympy evaulation namespace
sp_namespace = {}
sp_namespace.update((name, op) for name, op in sp.functions.__dict__.items() \
                    if name[0] != "_")
sp_namespace["Conditional"] = Conditional
sp_namespace.update((name, op) for name, op in relational.__dict__.items() \
                    if name in ["Eq", "Ne", "Gt", "Ge", "Lt", "Le"])

__all__ = [_name for _name in globals().keys() if _name[0] != "_"]
