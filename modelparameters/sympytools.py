__author__ = "Johan Hake <hake.dev@gmail.com>"
__date__ = "2012-06-29 -- 2012-07-05"
__copyright__ = "Copyright (C) 2008-2012 " + __author__
__license__  = "GNU LGPL Version 3.0 or later"

# System imports
import sympy as sp

from sympy.printing import StrPrinter
from sympy.printing.ccode import CCodePrinter
from sympy.printing.precedence import precedence

class ModelParameterPrinter(StrPrinter):
    """
    Custom printer for sympy expressions
    """
    def _print_SymbolParam(self, expr):
        return expr.abbrev

_printer = ModelParameterPrinter()

# Update printer
sp.Basic.__str__ = lambda self: _printer.doprint(self)

class SymbolParam(sp.AtomicExpr):
    """
    Class for all Symbols used in ScalarParam
    """
    is_positive = True    # make (m**2)**Rational(1,2) --> m
    is_commutative = True

    __slots__ = ["name", "abbrev"]

    def __new__(cls, name, abbrev, **assumptions):
        obj = AtomicExpr.__new__(cls, **assumptions)
        assert isinstance(name, str),repr(type(name))
        assert isinstance(abbrev, str),repr(type(abbrev))
        obj.name = name
        obj.abbrev = abbrev
        return obj

    def __getnewargs__(self):
        return (self.name, self.abbrev)

    def __eq__(self, other):
        return isinstance(other, SymbolParam) and self.name == other.name

    def __hash__(self):
        return super(SymbolParam, self).__hash__()

    def _hashable_content(self):
        return (self.name,self.abbrev)

def Conditional(cond, true_value, false_value):
    """
    Declares a conditional

    Arguments
    ---------
    cond : A conditional
        The conditional which should be evaluated
    true_value : Any model expression
         Model expression for a true evaluation of the conditional
    true_value : Any model expression
         Model expression for a false evaluation of the conditional
    """
    return sp.functions.Piecewise((true_value, cond), (false_value, True))

class CustomCCodePrinter(CCodePrinter):
    """
    Overload some ccode generation
    """
    
    def __init__(self, cpp=False, settings={}):
        super(CustomCCodePrinter, self).__init__(self, settings={})
        self._prefix = "std::" if cpp else ""

    # Better output to c for conditionals
    def _print_Piecewise(self, expr):
        result = ""
        for e, c in expr.args[:-1]:
            result += "(%s ? %s : "%(self._print(c), self._print(e))
        last_line = "%s)" % self._print(expr.args[-1].expr)
        return result+last_line
    
    def _print_Function(self, expr):
        #print expr.func.__name__, expr.args
        if expr.func.__name__ == "Max":
            return "%smax(%s)" % (self._prefix, self.stringify(expr.args, ", "))
        elif expr.func.__name__ == "Min":
            return "%smin(%s)" % (self._prefix, self.stringify(expr.args, ", "))
        elif expr.func.__name__ == "ceiling":
            return "%sceil(%s)" % (self._prefix, self.stringify(expr.args, ", "))
        elif expr.func.__name__ == "Abs" and not expr.args[0].is_integer:
            return "%sfabs(%s)" % (self._prefix, self.stringify(expr.args, ", "))
        else:
            return "%s" % self._prefix + expr.func.__name__.lower() + \
                   "(%s)"%self.stringify(expr.args, ", ")
    
    def _print_Pow(self, expr):
        PREC = precedence(expr)
        if expr.exp is S.NegativeOne:
            return '1.0/%s'%(self.parenthesize(expr.base, PREC))
        elif expr.exp.is_integer:
            return "(%s)" % ("*".join(self._print(expr.base) \
                                      for i in xrange(int(expr.exp))))
        elif expr.exp == 0.5:
            return '%ssqrt(%s)' % (self._prefix, self._print(expr.base))
        else:
            return '%spow(%s, %s)'%(self._prefix, self._print(expr.base),
                                    self._print(expr.exp))

_ccode_printer = CustomCCodePrinter()
_cppcode_printer = CustomCCodePrinter(cpp=True)

def ccode(expr, assign_to=None):
    """
    Return a C-code representation of a sympy expression
    """
    _ccode_printer.do_print(expr, assign_to)

def cppcode(expr, assign_to=None):
    """
    Return a C++-code representation of a sympy expression
    """
    _cppcode_printer.do_print(expr, assign_to)

