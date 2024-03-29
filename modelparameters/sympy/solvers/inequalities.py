"""Tools for solving inequalities and systems of inequalities. """

from __future__ import print_function, division

from ..core import Symbol, Dummy, sympify
from ..core.compatibility import iterable
from ..sets import Interval
from ..core.relational import Relational, Eq, Ge, Lt
from ..sets.sets import FiniteSet, Union
from ..sets.fancysets import ImageSet
from ..core.singleton import S

from ..functions import Abs
from ..logic import And
from ..polys import Poly, PolynomialError, parallel_poly_from_expr
from ..polys.polyutils import _nsort
from ..utilities.misc import filldedent

def solve_poly_inequality(poly, rel):
    """Solve a polynomial inequality with rational coefficients.

    Examples
    ========

    >>> from .. import Poly
    >>> from ..abc import x
    >>> from .inequalities import solve_poly_inequality

    >>> solve_poly_inequality(Poly(x, x, domain='ZZ'), '==')
    [{0}]

    >>> solve_poly_inequality(Poly(x**2 - 1, x, domain='ZZ'), '!=')
    [Interval.open(-oo, -1), Interval.open(-1, 1), Interval.open(1, oo)]

    >>> solve_poly_inequality(Poly(x**2 - 1, x, domain='ZZ'), '==')
    [{-1}, {1}]

    See Also
    ========
    solve_poly_inequalities
    """
    if not isinstance(poly, Poly):
        raise ValueError(
            'For efficiency reasons, `poly` should be a Poly instance')
    if poly.is_number:
        t = Relational(poly.as_expr(), 0, rel)
        if t is S.true:
            return [S.Reals]
        elif t is S.false:
            return [S.EmptySet]
        else:
            raise NotImplementedError(
                "could not determine truth value of %s" % t)

    reals, intervals = poly.real_roots(multiple=False), []

    if rel == '==':
        for root, _ in reals:
            interval = Interval(root, root)
            intervals.append(interval)
    elif rel == '!=':
        left = S.NegativeInfinity

        for right, _ in reals + [(S.Infinity, 1)]:
            interval = Interval(left, right, True, True)
            intervals.append(interval)
            left = right
    else:
        if poly.LC() > 0:
            sign = +1
        else:
            sign = -1

        eq_sign, equal = None, False

        if rel == '>':
            eq_sign = +1
        elif rel == '<':
            eq_sign = -1
        elif rel == '>=':
            eq_sign, equal = +1, True
        elif rel == '<=':
            eq_sign, equal = -1, True
        else:
            raise ValueError("'%s' is not a valid relation" % rel)

        right, right_open = S.Infinity, True

        for left, multiplicity in reversed(reals):
            if multiplicity % 2:
                if sign == eq_sign:
                    intervals.insert(
                        0, Interval(left, right, not equal, right_open))

                sign, right, right_open = -sign, left, not equal
            else:
                if sign == eq_sign and not equal:
                    intervals.insert(
                        0, Interval(left, right, True, right_open))
                    right, right_open = left, True
                elif sign != eq_sign and equal:
                    intervals.insert(0, Interval(left, left))

        if sign == eq_sign:
            intervals.insert(
                0, Interval(S.NegativeInfinity, right, True, right_open))

    return intervals


def solve_poly_inequalities(polys):
    """Solve polynomial inequalities with rational coefficients.

    Examples
    ========

    >>> from .inequalities import solve_poly_inequalities
    >>> from ..polys import Poly
    >>> from ..abc import x
    >>> solve_poly_inequalities(((
    ... Poly(x**2 - 3), ">"), (
    ... Poly(-x**2 + 1), ">")))
    Union(Interval.open(-oo, -sqrt(3)), Interval.open(-1, 1), Interval.open(sqrt(3), oo))
    """
    from .. import Union
    return Union(*[solve_poly_inequality(*p) for p in polys])


def solve_rational_inequalities(eqs):
    """Solve a system of rational inequalities with rational coefficients.

    Examples
    ========

    >>> from ..abc import x
    >>> from .. import Poly
    >>> from .inequalities import solve_rational_inequalities

    >>> solve_rational_inequalities([[
    ... ((Poly(-x + 1), Poly(1, x)), '>='),
    ... ((Poly(-x + 1), Poly(1, x)), '<=')]])
    {1}

    >>> solve_rational_inequalities([[
    ... ((Poly(x), Poly(1, x)), '!='),
    ... ((Poly(-x + 1), Poly(1, x)), '>=')]])
    Union(Interval.open(-oo, 0), Interval.Lopen(0, 1))

    See Also
    ========
    solve_poly_inequality
    """
    result = S.EmptySet

    for _eqs in eqs:
        if not _eqs:
            continue

        global_intervals = [Interval(S.NegativeInfinity, S.Infinity)]

        for (numer, denom), rel in _eqs:
            numer_intervals = solve_poly_inequality(numer*denom, rel)
            denom_intervals = solve_poly_inequality(denom, '==')

            intervals = []

            for numer_interval in numer_intervals:
                for global_interval in global_intervals:
                    interval = numer_interval.intersect(global_interval)

                    if interval is not S.EmptySet:
                        intervals.append(interval)

            global_intervals = intervals

            intervals = []

            for global_interval in global_intervals:
                for denom_interval in denom_intervals:
                    global_interval -= denom_interval

                if global_interval is not S.EmptySet:
                    intervals.append(global_interval)

            global_intervals = intervals

            if not global_intervals:
                break

        for interval in global_intervals:
            result = result.union(interval)

    return result


def reduce_rational_inequalities(exprs, gen, relational=True):
    """Reduce a system of rational inequalities with rational coefficients.

    Examples
    ========

    >>> from .. import Poly, Symbol
    >>> from .inequalities import reduce_rational_inequalities

    >>> x = Symbol('x', real=True)

    >>> reduce_rational_inequalities([[x**2 <= 0]], x)
    Eq(x, 0)

    >>> reduce_rational_inequalities([[x + 2 > 0]], x)
    (-2 < x) & (x < oo)
    >>> reduce_rational_inequalities([[(x + 2, ">")]], x)
    (-2 < x) & (x < oo)
    >>> reduce_rational_inequalities([[x + 2]], x)
    Eq(x, -2)
    """
    exact = True
    eqs = []
    solution = S.Reals if exprs else S.EmptySet
    for _exprs in exprs:
        _eqs = []

        for expr in _exprs:
            if isinstance(expr, tuple):
                expr, rel = expr
            else:
                if expr.is_Relational:
                    expr, rel = expr.lhs - expr.rhs, expr.rel_op
                else:
                    expr, rel = expr, '=='

            if expr is S.true:
                numer, denom, rel = S.Zero, S.One, '=='
            elif expr is S.false:
                numer, denom, rel = S.One, S.One, '=='
            else:
                numer, denom = expr.together().as_numer_denom()

            try:
                (numer, denom), opt = parallel_poly_from_expr(
                    (numer, denom), gen)
            except PolynomialError:
                raise PolynomialError(filldedent('''
                    only polynomials and
                    rational functions are supported in this context'''))

            if not opt.domain.is_Exact:
                numer, denom, exact = numer.to_exact(), denom.to_exact(), False

            domain = opt.domain.get_exact()

            if not (domain.is_ZZ or domain.is_QQ):
                expr = numer/denom
                expr = Relational(expr, 0, rel)
                solution &= solve_univariate_inequality(expr, gen, relational=False)
            else:
                _eqs.append(((numer, denom), rel))

        if _eqs:
            eqs.append(_eqs)

    if eqs:
        solution &= solve_rational_inequalities(eqs)

    if not exact:
        solution = solution.evalf()

    if relational:
        solution = solution.as_relational(gen)

    return solution


def reduce_abs_inequality(expr, rel, gen):
    """Reduce an inequality with nested absolute values.

    Examples
    ========

    >>> from .. import Abs, Symbol
    >>> from .inequalities import reduce_abs_inequality
    >>> x = Symbol('x', real=True)

    >>> reduce_abs_inequality(Abs(x - 5) - 3, '<', x)
    (2 < x) & (x < 8)

    >>> reduce_abs_inequality(Abs(x + 2)*3 - 13, '<', x)
    (-19/3 < x) & (x < 7/3)

    See Also
    ========

    reduce_abs_inequalities
    """
    if gen.is_real is False:
         raise TypeError(filldedent('''
            can't solve inequalities with absolute
            values containing non-real variables'''))

    def _bottom_up_scan(expr):
        exprs = []

        if expr.is_Add or expr.is_Mul:
            op = expr.func

            for arg in expr.args:
                _exprs = _bottom_up_scan(arg)

                if not exprs:
                    exprs = _exprs
                else:
                    args = []

                    for expr, conds in exprs:
                        for _expr, _conds in _exprs:
                            args.append((op(expr, _expr), conds + _conds))

                    exprs = args
        elif expr.is_Pow:
            n = expr.exp
            if not n.is_Integer:
                raise ValueError("Only Integer Powers are allowed on Abs.")

            _exprs = _bottom_up_scan(expr.base)

            for expr, conds in _exprs:
                exprs.append((expr**n, conds))
        elif isinstance(expr, Abs):
            _exprs = _bottom_up_scan(expr.args[0])

            for expr, conds in _exprs:
                exprs.append(( expr, conds + [Ge(expr, 0)]))
                exprs.append((-expr, conds + [Lt(expr, 0)]))
        else:
            exprs = [(expr, [])]

        return exprs

    exprs = _bottom_up_scan(expr)

    mapping = {'<': '>', '<=': '>='}
    inequalities = []

    for expr, conds in exprs:
        if rel not in mapping.keys():
            expr = Relational( expr, 0, rel)
        else:
            expr = Relational(-expr, 0, mapping[rel])

        inequalities.append([expr] + conds)

    return reduce_rational_inequalities(inequalities, gen)


def reduce_abs_inequalities(exprs, gen):
    """Reduce a system of inequalities with nested absolute values.

    Examples
    ========

    >>> from .. import Abs, Symbol
    >>> from ..abc import x
    >>> from .inequalities import reduce_abs_inequalities
    >>> x = Symbol('x', real=True)

    >>> reduce_abs_inequalities([(Abs(3*x - 5) - 7, '<'),
    ... (Abs(x + 25) - 13, '>')], x)
    (-2/3 < x) & (x < 4) & (((-oo < x) & (x < -38)) | ((-12 < x) & (x < oo)))

    >>> reduce_abs_inequalities([(Abs(x - 4) + Abs(3*x - 5) - 7, '<')], x)
    (1/2 < x) & (x < 4)

    See Also
    ========

    reduce_abs_inequality
    """
    return And(*[ reduce_abs_inequality(expr, rel, gen)
        for expr, rel in exprs ])


def solve_univariate_inequality(expr, gen, relational=True, domain=S.Reals, continuous=False):
    """Solves a real univariate inequality.

    Parameters
    ==========

    expr : Relational
        The target inequality
    gen : Symbol
        The variable for which the inequality is solved
    relational : bool
        A Relational type output is expected or not
    domain : Set
        The domain over which the equation is solved
    continuous: bool
        True if expr is known to be continuous over the given domain
        (and so continuous_domain() doesn't need to be called on it)

    Raises
    ======

    NotImplementedError
        The solution of the inequality cannot be determined due to limitation
        in `solvify`.

    Notes
    =====

    Currently, we cannot solve all the inequalities due to limitations in
    `solvify`. Also, the solution returned for trigonometric inequalities
    are restricted in its periodic interval.

    See Also
    ========

    solvify: solver returning solveset solutions with solve's output API

    Examples
    ========

    >>> from .inequalities import solve_univariate_inequality
    >>> from .. import Symbol, sin, Interval, S
    >>> x = Symbol('x')

    >>> solve_univariate_inequality(x**2 >= 4, x)
    ((2 <= x) & (x < oo)) | ((x <= -2) & (-oo < x))

    >>> solve_univariate_inequality(x**2 >= 4, x, relational=False)
    Union(Interval(-oo, -2), Interval(2, oo))

    >>> domain = Interval(0, S.Infinity)
    >>> solve_univariate_inequality(x**2 >= 4, x, False, domain)
    Interval(2, oo)

    >>> solve_univariate_inequality(sin(x) > 0, x, relational=False)
    Interval.open(0, pi)

    """
    from ..calculus.util import (continuous_domain, periodicity,
        function_range)
    from .solvers import denoms
    from .solveset import solveset_real, solvify

    # This keeps the function independent of the assumptions about `gen`.
    # `solveset` makes sure this function is called only when the domain is
    # real.
    d = Dummy(real=True)
    expr = expr.subs(gen, d)
    _gen = gen
    gen = d
    rv = None

    if expr is S.true:
        rv = domain

    elif expr is S.false:
        rv = S.EmptySet

    else:
        e = expr.lhs - expr.rhs
        period = periodicity(e, gen)
        if period is not None:
            frange = function_range(e, gen, domain)

            rel = expr.rel_op
            if rel == '<' or rel == '<=':
                if expr.func(frange.sup, 0):
                    rv = domain
                elif not expr.func(frange.inf, 0):
                    rv = S.EmptySet

            elif rel == '>' or rel == '>=':
                if expr.func(frange.inf, 0):
                    rv = domain
                elif not expr.func(frange.sup, 0):
                    rv = S.EmptySet

            inf, sup = domain.inf, domain.sup
            if sup - inf is S.Infinity:
                domain = Interval(0, period, False, True)

        if rv is None:
            solns = solvify(e, gen, domain)
            if solns is None:
                raise NotImplementedError(filldedent('''The inequality cannot be
                    solved using solve_univariate_inequality.'''))
            singularities = []
            for d in denoms(expr, gen):
                singularities.extend(solvify(d, gen, domain))
            if not continuous:
                domain = continuous_domain(e, gen, domain)

            include_x = expr.func(0, 0)

            def valid(x):
                v = e.subs(gen, x)
                try:
                    r = expr.func(v, 0)
                except TypeError:
                    r = S.false
                if r in (S.true, S.false):
                    return r
                if v.is_real is False:
                    return S.false
                else:
                    v = v.n(2)
                    if v.is_comparable:
                        return expr.func(v, 0)
                    return S.false

            try:
                discontinuities = set(domain.boundary -
                    FiniteSet(domain.inf, domain.sup))
                # remove points that are not between inf and sup of domain
                critical_points = FiniteSet(*(solns + singularities + list(
                    discontinuities))).intersection(
                    Interval(domain.inf, domain.sup,
                    domain.inf not in domain, domain.sup not in domain))
                reals = _nsort(critical_points, separated=True)[0]
            except NotImplementedError:
                raise NotImplementedError('sorting of these roots is not supported')

            sol_sets = [S.EmptySet]

            start = domain.inf
            if valid(start) and start.is_finite:
                sol_sets.append(FiniteSet(start))

            for x in reals:
                end = x

                if valid(_pt(start, end)):
                    sol_sets.append(Interval(start, end, True, True))

                if x in singularities:
                    singularities.remove(x)
                else:
                    if x in discontinuities:
                        discontinuities.remove(x)
                        _valid = valid(x)
                    else:  # it's a solution
                        _valid = include_x
                    if _valid:
                        sol_sets.append(FiniteSet(x))

                start = end

            end = domain.sup
            if valid(end) and end.is_finite:
                sol_sets.append(FiniteSet(end))

            if valid(_pt(start, end)):
                sol_sets.append(Interval.open(start, end))

            rv = Union(*sol_sets).subs(gen, _gen)

    return rv if not relational else rv.as_relational(_gen)


def _pt(start, end):
    """Return a point between start and end"""
    if start.is_infinite and end.is_infinite:
        pt = S.Zero
    elif end.is_infinite:
        pt = start + 1
    elif start.is_infinite:
        pt = end - 1
    else:
        pt = (start + end)/2
    return pt


def _solve_inequality(ie, s):
    """ A hacky replacement for solve, since the latter only works for
        univariate inequalities. """
    expr = ie.lhs - ie.rhs
    try:
        p = Poly(expr, s)
        if p.degree() != 1:
            raise NotImplementedError
    except (PolynomialError, NotImplementedError):
        try:
            return reduce_rational_inequalities([[ie]], s)
        except PolynomialError:
            return solve_univariate_inequality(ie, s)
    a, b = p.all_coeffs()
    if a.is_positive or ie.rel_op in ('!=', '=='):
        return ie.func(s, -b/a)
    elif a.is_negative:
        return ie.reversed.func(s, -b/a)
    else:
        raise NotImplementedError


def _reduce_inequalities(inequalities, symbols):
    # helper for reduce_inequalities

    poly_part, abs_part = {}, {}
    other = []

    for inequality in inequalities:

        expr, rel = inequality.lhs, inequality.rel_op  # rhs is 0

        # check for gens using atoms which is more strict than free_symbols to
        # guard against EX domain which won't be handled by
        # reduce_rational_inequalities
        gens = expr.atoms(Symbol)

        if len(gens) == 1:
            gen = gens.pop()
        else:
            common = expr.free_symbols & symbols
            if len(common) == 1:
                gen = common.pop()
                other.append(_solve_inequality(Relational(expr, 0, rel), gen))
                continue
            else:
                raise NotImplementedError(filldedent('''
                    inequality has more than one
                    symbol of interest'''))

        if expr.is_polynomial(gen):
            poly_part.setdefault(gen, []).append((expr, rel))
        else:
            components = expr.find(lambda u:
                u.has(gen) and (
                u.is_Function or u.is_Pow and not u.exp.is_Integer))
            if components and all(isinstance(i, Abs) for i in components):
                abs_part.setdefault(gen, []).append((expr, rel))
            else:
                other.append(_solve_inequality(Relational(expr, 0, rel), gen))

    poly_reduced = []
    abs_reduced = []

    for gen, exprs in poly_part.items():
        poly_reduced.append(reduce_rational_inequalities([exprs], gen))

    for gen, exprs in abs_part.items():
        abs_reduced.append(reduce_abs_inequalities(exprs, gen))

    return And(*(poly_reduced + abs_reduced + other))


def reduce_inequalities(inequalities, symbols=[]):
    """Reduce a system of inequalities with rational coefficients.

    Examples
    ========

    >>> from .. import sympify as S, Symbol
    >>> from ..abc import x, y
    >>> from .inequalities import reduce_inequalities

    >>> reduce_inequalities(0 <= x + 3, [])
    (-3 <= x) & (x < oo)

    >>> reduce_inequalities(0 <= x + y*2 - 1, [x])
    x >= -2*y + 1
    """
    if not iterable(inequalities):
        inequalities = [inequalities]
    inequalities = [sympify(i) for i in inequalities]

    gens = set().union(*[i.free_symbols for i in inequalities])

    if not iterable(symbols):
        symbols = [symbols]
    symbols = (set(symbols) or gens) & gens
    if any(i.is_real is False for i in symbols):
        raise TypeError(filldedent('''
            inequalities cannot contain symbols that are not real.'''))

    # make vanilla symbol real
    recast = dict([(i, Dummy(i.name, real=True))
        for i in gens if i.is_real is None])
    inequalities = [i.xreplace(recast) for i in inequalities]
    symbols = {i.xreplace(recast) for i in symbols}

    # prefilter
    keep = []
    for i in inequalities:
        if isinstance(i, Relational):
            i = i.func(i.lhs.as_expr() - i.rhs.as_expr(), 0)
        elif i not in (True, False):
            i = Eq(i, 0)
        if i == True:
            continue
        elif i == False:
            return S.false
        if i.lhs.is_number:
            raise NotImplementedError(
                "could not determine truth value of %s" % i)
        keep.append(i)
    inequalities = keep
    del keep

    # solve system
    rv = _reduce_inequalities(inequalities, symbols)

    # restore original symbols and return
    return rv.xreplace({v: k for k, v in recast.items()})
