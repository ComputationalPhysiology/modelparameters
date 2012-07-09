__author__ = "Johan Hake <hake.dev@gmail.com>"
__date__ = "2012-06-29 -- 2012-07-09"
__copyright__ = "Copyright (C) 2008-2012 " + __author__
__license__  = "GNU LGPL Version 3.0 or later"

# System imports
import sympy as sp

from sympy.printing.ccode import CCodePrinter as _CCodePrinter
from sympy.printing.precedence import _precedence

class _CustomCCodePrinter(_CCodePrinter):
    """
    Overload some ccode generation
    """
    
    def __init__(self, cpp=False, settings={}):
        super(CustomCCodePrinter, self).__init__(settings=settings)
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
        PREC = _precedence(expr)
        if expr.exp is sp.S.NegativeOne:
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

__all__ = [_name for _name in globals().keys() if _name[0] != "_"]
