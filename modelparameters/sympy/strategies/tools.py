from __future__ import print_function, division

from . import rl
from .core import do_one, exhaust, switch
from .traverse import top_down

def subs(d, **kwargs):
    """ Full simultaneous exact substitution

    Examples
    ========

    >>> from .tools import subs
    >>> from .. import Basic
    >>> mapping = {1: 4, 4: 1, Basic(5): Basic(6, 7)}
    >>> expr = Basic(1, Basic(2, 3), Basic(4, Basic(5)))
    >>> subs(mapping)(expr)
    Basic(4, Basic(2, 3), Basic(1, Basic(6, 7)))
    """
    if d:
        return top_down(do_one(*map(rl.subs, *zip(*d.items()))), **kwargs)
    else:
        return lambda x: x

def canon(*rules, **kwargs):
    """ Strategy for canonicalization

    Apply each rule in a bottom_up fashion through the tree.
    Do each one in turn.
    Keep doing this until there is no change.
    """
    return exhaust(top_down(exhaust(do_one(*rules)), **kwargs))

def typed(ruletypes):
    """ Apply rules based on the expression type

    inputs:
        ruletypes -- a dict mapping {Type: rule}

    >>> from ..strategies import rm_id, typed
    >>> from .. import Add, Mul
    >>> rm_zeros = rm_id(lambda x: x==0)
    >>> rm_ones  = rm_id(lambda x: x==1)
    >>> remove_idents = typed({Add: rm_zeros, Mul: rm_ones})
    """
    return switch(type, ruletypes)
