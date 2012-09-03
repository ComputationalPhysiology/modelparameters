__author__ = "Johan Hake <hake.dev@gmail.com>"
__date__ = "2012-06-29 -- 2012-08-31"
__copyright__ = "Copyright (C) 2008-2012 " + __author__
__license__  = "GNU LGPL Version 3.0 or later"

# System imports
import sympy as sp

from sympy.printing import StrPrinter as _StrPrinter
from sympy.printing.ccode import CCodePrinter as _CCodePrinter
from sympy.printing.precedence import precedence as _precedence

class _CustomPythonPrinter(_StrPrinter):
    
    # Better output to c for conditionals
    def _print_Piecewise(self, expr):
        result = ""
        num_par = 0
        for e, c in expr.args[:-1]:
            num_par += 1
            result += "(%s if %s else "%(self._print(e), self._print(c))
        last_line = self._print(expr.args[-1].expr) + ")"*num_par
        return result+last_line
    
    def _print_ModelSymbol(self, expr):
        return expr.name

    def _print_Function(self, expr):
        #print expr.func.__name__, expr.args
        if expr.func.__name__ == "Max":
            return "max(%s)" % self.stringify(expr.args, ", ")
        elif expr.func.__name__ == "Min":
            return "min(%s)" % (self._prefix, self.stringify(expr.args, ", "))
        elif expr.func.__name__ == "ceiling":
            return "ceil(%s)" % (self._prefix, self.stringify(expr.args, ", "))
        elif expr.func.__name__ == "Abs" and not expr.args[0].is_integer:
            return "abs(%s)" % (self._prefix, self.stringify(expr.args, ", "))
        else:
            return "%s" % expr.func.__name__.lower() + \
                   "(%s)"%self.stringify(expr.args, ", ")
    
    def _print_Pow(self, expr):
        PREC = _precedence(expr)
        if expr.exp is sp.S.NegativeOne:
            return '1.0/%s'%(self.parenthesize(expr.base, PREC))
        elif expr.exp.is_integer and expr.exp<4:
            return "(%s)" % ("*".join(self._print(expr.base) \
                                      for i in xrange(int(expr.exp))))
        elif expr.exp == 0.5:
            return 'sqrt(%s)' % self._print(expr.base)
        else:
            return 'pow(%s, %s)'%(self._print(expr.base),
                                    self._print(expr.exp))

class _CustomCCodePrinter(_CCodePrinter):
    """
    Overload some ccode generation
    """
    
    def __init__(self, cpp=False, settings={}):
        super(_CustomCCodePrinter, self).__init__(settings=settings)
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

_python_code_printer = _CustomPythonPrinter()
_ccode_printer = _CustomCCodePrinter()
_cppcode_printer = _CustomCCodePrinter(cpp=True)

def ccode(expr, assign_to=None):
    """
    Return a C-code representation of a sympy expression
    """
    return _ccode_printer.doprint(expr, assign_to)

def cppcode(expr, assign_to=None):
    """
    Return a C++-code representation of a sympy expression
    """
    return _cppcode_printer.doprint(expr, assign_to)

def pythoncode(expr, assign_to=None):
    """
    Return a Python-code representation of a sympy expression
    """
    if assign_to is not None:
        return "{0} = {1}".format(assign_to, \
                                  _python_code_printer.doprint(expr))
    return _python_code_printer.doprint(expr)

__all__ = [_name for _name in globals().keys() if _name[0] != "_"]
