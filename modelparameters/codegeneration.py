__author__ = "Johan Hake <hake.dev@gmail.com>"
__date__ = "2012-06-29 -- 2012-10-10"
__copyright__ = "Copyright (C) 2008-2012 " + __author__
__license__  = "GNU LGPL Version 3.0 or later"

# System imports
import sympy as sp

from sympy.printing import StrPrinter as _StrPrinter
from sympy.printing.ccode import CCodePrinter as _CCodePrinter
from sympy.printing.precedence import precedence as _precedence

class _CustomPythonPrinter(_StrPrinter):
    def __init__(self, namespace=""):
        assert(namespace in ["", "math", "np", "numpy"])
        self._namespace = namespace if not namespace else namespace + "."
        _StrPrinter.__init__(self)
        
    def _print_ModelSymbol(self, expr):
        return expr.name

    def _print_One(self, expr):
        return "1.0"

    def _print_Integer(self, expr):
        return str(expr.p) + ".0"

    def _print_NegativeOne(self, expr):
        return "-1.0"

    def _print_Sqrt(self, expr):
        return "{0}sqrt({1})".format(self._namespace,self._print(expr.args[0]))
    
    def _print_Pow(self, expr):
        PREC = _precedence(expr)
        if expr.exp is sp.S.NegativeOne:
            return "1.0/{0}".format(self.parenthesize(expr.base, PREC))
        elif expr.exp.is_integer and int(expr.exp) in [2, 3]:
            return "({0})".format("*".join(self._print(expr.base) \
                                           for i in xrange(int(expr.exp))))
        elif expr.exp.is_integer and int(expr.exp) in [-2, -3]:
            return "1.0/({0})".format("*".join(self._print(expr.base) \
                                           for i in xrange(int(expr.exp))))
        elif expr.exp == 0.5:
            return "{0}sqrt({1})".format(self._namespace,
                                         self._print(expr.base))
        elif expr.exp == -0.5:
            return "1/{0}sqrt({1})".format(self._namespace,
                                         self._print(expr.base))
        else:
            return "{0}pow({1}, {2})".format(self._namespace,
                                             self._print(expr.base),
                                             self._print(expr.exp))

class _CustomPythonCodePrinter(_CustomPythonPrinter):


    def _print_Min(self, expr):
        return "%s" % expr.func.__name__.lower() + \
               "(%s)"%self.stringify(expr.args, ", ")

    def _print_Max(self, expr):
        return "%s" % expr.func.__name__.lower() + \
               "(%s)"%self.stringify(expr.args, ", ")

    def _print_Function(self, expr):
        #print expr.func.__name__, expr.args
        if expr.func.__name__ == "ceiling":
            return "{0}ceil({1})".format(self._namespace, \
                                         self.stringify(expr.args, ", "))
        else:
            return "{0}{1}".format(self._namespace, \
                        expr.func.__name__.lower() + \
                        "({0})".format(self.stringify(expr.args, ", ")))

    def _print_Piecewise(self, expr):
        result = ""
        num_par = 0
        for e, c in expr.args[:-1]:
            num_par += 1
            result += "(%s if %s else "%(self._print(e), self._print(c))
        last_line = self._print(expr.args[-1].expr) + ")"*num_par
        return result+last_line
    
class _CustomCCodePrinter(_StrPrinter):
    """
    Overload some ccode generation
    """
    
    def __init__(self, cpp=False, settings={}):
        super(_CustomCCodePrinter, self).__init__(settings=settings)
        self._prefix = "std::" if cpp else ""

    # Better output to c for conditionals
    def _print_One(self, expr):
        return "1.0"

    def _print_Integer(self, expr):
        return str(expr.p) + ".0"

    def _print_NegativeOne(self, expr):
        return "-1.0"

    def _print_Min(self, expr):
        "fmin and fmax is not contained in std namespace untill -ansi g++ 4.7"
        return "fmin(%s)" % (self.stringify(expr.args, ", "))

    def _print_Max(self, expr):
        "fmin and fmax is not contained in std namespace untill -ansi g++ 4.7"
        return "fmax(%s)" % (self.stringify(expr.args, ", "))

    def _print_Ceiling(self, expr):
        return "%sceil(%s)" % (self._prefix, self.stringify(expr.args, ", "))
        
    def _print_Abs(self, expr):
        return "%sfabs(%s)" % (self._prefix, self.stringify(expr.args, ", "))

    def _print_ModelSymbol(self, expr):
        return expr.name

    def _print_Piecewise(self, expr):
        result = ""
        for e, c in expr.args[:-1]:
            result += "(%s ? %s : "%(self._print(c), self._print(e))
        last_line = "%s)" % self._print(expr.args[-1].expr)
        return result+last_line
    
    def _print_Function(self, expr):
        #print expr.func.__name__, expr.args
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

# Different math namespace python printer
_python_code_printer = {"":_CustomPythonCodePrinter(""),
                        "np":_CustomPythonCodePrinter("np"),
                        "numpy":_CustomPythonCodePrinter("numpy"),
                        "math":_CustomPythonCodePrinter("math"),}
                        
_ccode_printer = _CustomCCodePrinter()
_cppcode_printer = _CustomCCodePrinter(cpp=True)
_sympy_printer = _CustomPythonPrinter()

def ccode(expr, assign_to=None):
    """
    Return a C-code representation of a sympy expression
    """
    ret = _ccode_printer.doprint(expr)
    if assign_to is None:
        return ret
    return "{0} = {1}".format(assign_to, ret)

def cppcode(expr, assign_to=None):
    """
    Return a C++-code representation of a sympy expression
    """
    ret = _cppcode_printer.doprint(expr)
    if assign_to is None:
        return ret
    return "{0} = {1}".format(assign_to, ret)

def pythoncode(expr, assign_to=None, namespace="math"):
    """
    Return a Python-code representation of a sympy expression
    """
    ret = _python_code_printer[namespace].doprint(expr)
    if assign_to is None:
        return ret
    return "{0} = {1}".format(assign_to, ret)

def sympycode(expr, assign_to=None):
    ret = _sympy_printer.doprint(expr)
    if assign_to is None:
        return ret
    return "{0} = {1}".format(assign_to, ret)
    

__all__ = [_name for _name in globals().keys() if _name[0] != "_"]
