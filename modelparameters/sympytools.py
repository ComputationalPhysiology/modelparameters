# Copyright (C) 2012 Johan Hake
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

# System imports
import sympy as sp

from sympy.core import relational

# Local imports
from utils import check_arg
from logger import warning, error, value_error, type_error
from codegeneration import sympycode

# Update printer
sp.Basic.__str__ = sympycode
sp.Basic.__repr__ = sympycode

# A hack to get around evaluation of SymPy expressions
from sympy.core.operations import AssocOp as _AssocOp
from sympy.core.power import Pow as _Pow
from sympy.core.expr import Expr as _Expr
from sympy.core.add import Add as _Add
from sympy.core.cache import cacheit as _cacheit
from sympy.core import function as _function
from sympy.core.assumptions import ManagedProperties as _ManagedProperties
import types

_evaluate = False

def enable_evaluation():
    """
    Enable Add, Mul and Pow contractions
    """
    global _evaluate
    _evaluate = True
    
def disable_evaluation():
    """
    Disable Add, Mul and Pow contractions
    """
    global _evaluate
    _evaluate = False

def _assocop_new(cls, *args, **options):
    args = map(sp.sympify, args)
    args = [a for a in args if a is not cls.identity]

    if not options.pop('evaluate', _evaluate):
        return cls._from_args(args)

    if len(args) == 0:
        return cls.identity
    if len(args) == 1:
        return args[0]

    c_part, nc_part, order_symbols = cls.flatten(args)
    is_commutative = not nc_part
    obj = cls._from_args(c_part + nc_part, is_commutative)

    if order_symbols is not None:
        return C.Order(obj, *order_symbols)
    return obj

def _function_new(cls, *args, **options):
    # Handle calls like Function('f')
    if cls is _function.Function:
        return _function.UndefinedFunction(*args)

    if cls.nargs is not None:
        if isinstance(cls.nargs, tuple):
            nargs = cls.nargs
        else:
            nargs = (cls.nargs,)

        n = len(args)

        if n not in nargs:
            # XXX: exception message must be in exactly this format to make
            # it work with NumPy's functions like vectorize(). The ideal
            # solution would be just to attach metadata to the exception
            # and change NumPy to take advantage of this.
            temp = ('%(name)s takes exactly %(args)s '
                   'argument%(plural)s (%(given)s given)')
            raise TypeError(temp %
                {
                'name': cls,
                'args': cls.nargs,
                'plural': 's'*(n != 1),
                'given': n})

    evaluate = options.get('evaluate', _evaluate)
    result = super(_function.Function, cls).__new__(cls, *args, **options)
    if not evaluate or not isinstance(result, cls):
        return result

    pr = max(cls._should_evalf(a) for a in result.args)
    pr2 = min(cls._should_evalf(a) for a in result.args)
    if pr2 > 0:
        return result.evalf(mlib.libmpf.prec_to_dps(pr))
    return result

def _pow_new(cls, b, e, evaluate=False):
    # don't optimize "if e==0; return 1" here; it's better to handle that
    # in the calling routine so this doesn't get called
    b = sp.sympify(b)
    e = sp.sympify(e)
    if _evaluate or evaluate:
        if e is sp.S.Zero:
            return sp.S.One
        elif e is sp.S.One:
            return b
        elif sp.S.NaN in (b, e):
            if b is sp.S.One: # already handled e == 0 above
                return sp.S.One
            return sp.S.NaN
        else:
            obj = b._eval_power(e)
            if obj is not None:
                return obj
    
    obj = _Expr.__new__(cls, b, e)
    obj.is_commutative = (b.is_commutative and e.is_commutative)
    return obj

# Overload new method with none evaluating one
_AssocOp.__new__ = types.MethodType(_cacheit(_assocop_new), None, _ManagedProperties)
_Pow.__new__ = types.MethodType(_cacheit(_pow_new), None, _ManagedProperties)
_function.Function.__new__ = types.MethodType(_cacheit(_function_new), None, _ManagedProperties)
class ModelSymbol(sp.Symbol):
    """
    Class for all Symbols used in ScalarParam
    """

    __slots__ = ("abbrev",)

    def __new__(cls, name, abbrev, **assumptions):
        obj = sp.Symbol.__new__(cls, name, real=True, finite=True)
        assert isinstance(name, str), repr(type(name))
        assert isinstance(abbrev, str), repr(type(abbrev))
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
    cond = sp.sympify(cond)

    # If the conditional is a bool it is already evaluated
    if isinstance(cond, bool):
        return true_value if cond else false_value
        
    if not(hasattr(cond, "is_Relational") or hasattr(cond, "is_relational")):
        type_error("Expected sympy object to have is_{r,R}elational "\
                   "attribute.")
    
    if (hasattr(cond, "is_Relational") and not cond.is_Relational) or \
           (hasattr(cond, "is_relational") and not cond.is_relational):
        type_error("Expected a Relational as first argument.")
    
    return sp.functions.Piecewise((true_value, cond), (false_value, sp.sympify(True)),
                                  evaluate=True)

def ContinuousConditional(cond, true_value, false_value, sigma=1.0):
    """
    Declares a continuous conditional. Instead of a either or result the
    true and false values are weighted with a sigmoidal function which
    either evaluates to 0 or 1 instead of the true or false. 

    Arguments
    ---------
    cond : An InEquality conditional
        An InEquality conditional which should be evaluated
    true_value : Any model expression
        Model expression for a true evaluation of the conditional
    false_value : Any model expression
        Model expression for a false evaluation of the conditional
    sigma : float (optional)
        Determines the sharpness of the sigmoidal function
    """
    
    cond = sp.sympify(cond)
    if not(hasattr(cond, "is_Relational") or hasattr(cond, "is_relational")):
        type_error("Expected sympy object to have is_{r,R}elational "\
                   "attribute.")
    
    if (hasattr(cond, "is_Relational") and not cond.is_Relational) or \
           (hasattr(cond, "is_relational") and not cond.is_relational):
        type_error("Expected a Relational as first argument.")
    
    # FIXME: Use the rel_op for check, as some changes has been applied
    # FIXME: in latest sympy making comparision difficult
    if "<" not in cond.rel_op and ">" not in cond.rel_op:
        type_error("Expected a lesser or greater than relational for "\
                   "a continuous conditional .")
    
    # Create Heaviside
    H = 1/(1 + sp.exp((cond.args[0]-cond.args[1])/sigma))

    # Desides which should be weighted with 1 and 0
    if "<" in cond.rel_op:
        return true_value*(1-H) + false_value*H

    return true_value*H + false_value*(1-H)
    
# Collect all parameters
_all_symbol_parameters = {}

def store_symbol_parameter(param):
    """
    Store a symbol parameter
    """
    from parameters import ScalarParam
    check_arg(param, ScalarParam)
    sym = param.sym
    #if str(sym) in _all_symbol_parameters:
    #    warning("Parameter with symbol name '%s' already "\
    #            "excist" % sym)
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

def add_pair_to_subs(subs, old, new):
    """
    Add a pair of old and new symbols to subs. If a subs with old as a
    key already excist it will be removed before insertion.
    """
    check_arg(subs, list, 0)
    check_arg(old, sp.Basic, 1)
    check_arg(new, sp.Basic, 2)
    
    for ind, (old0, new0) in enumerate(subs):
        if old0 == old:
            subs.pop(ind)
            break
    subs.append((old, new))

# Create a sympy evaulation namespace
sp_namespace = {}
sp_namespace.update((name, op) for name, op in sp.functions.__dict__.items() \
                    if name[0] != "_")
sp_namespace["Conditional"] = Conditional
sp_namespace["ContinuousConditional"] = ContinuousConditional
sp_namespace.update((name, op) for name, op in relational.__dict__.items() \
                    if name in ["Eq", "Ne", "Gt", "Ge", "Lt", "Le"])
sp_namespace["pi"] = sp.numbers.pi
sp_namespace["E"] = sp.numbers.E

__all__ = [_name for _name in globals().keys() if _name[0] != "_"]
