"""
Generating and counting primes.

"""
from __future__ import print_function, division

import random
from bisect import bisect
# Using arrays for sieving instead of lists greatly reduces
# memory consumption
from array import array as _array

from .primetest import isprime
from ..core.compatibility import as_int, range


def _arange(a, b):
    ar = _array('l', [0]*(b - a))
    for i, e in enumerate(range(a, b)):
        ar[i] = e
    return ar


class Sieve:
    """An infinite list of prime numbers, implemented as a dynamically
    growing sieve of Eratosthenes. When a lookup is requested involving
    an odd number that has not been sieved, the sieve is automatically
    extended up to that number.

    Examples
    ========

    >>> from .. import sieve
    >>> sieve._reset() # this line for doctest only
    >>> 25 in sieve
    False
    >>> sieve._list
    array('l', [2, 3, 5, 7, 11, 13, 17, 19, 23])
    """

    # data shared (and updated) by all Sieve instances
    _list = _array('l', [2, 3, 5, 7, 11, 13])

    def __repr__(self):
        return "<Sieve with %i primes sieved: 2, 3, 5, ... %i, %i>" % \
            (len(self._list), self._list[-2], self._list[-1])

    def _reset(self):
        """Return sieve to its initial state for testing purposes.
        """
        self._list = self._list[:6]

    def extend(self, n):
        """Grow the sieve to cover all primes <= n (a real number).

        Examples
        ========

        >>> from .. import sieve
        >>> sieve._reset() # this line for doctest only
        >>> sieve.extend(30)
        >>> sieve[10] == 29
        True
        """
        n = int(n)
        if n <= self._list[-1]:
            return

        # We need to sieve against all bases up to sqrt(n).
        # This is a recursive call that will do nothing if there are enough
        # known bases already.
        maxbase = int(n**0.5) + 1
        self.extend(maxbase)

        # Create a new sieve starting from sqrt(n)
        begin = self._list[-1] + 1
        newsieve = _arange(begin, n + 1)

        # Now eliminate all multiples of primes in [2, sqrt(n)]
        for p in self.primerange(2, maxbase):
            # Start counting at a multiple of p, offsetting
            # the index to account for the new sieve's base index
            startindex = (-begin) % p
            for i in range(startindex, len(newsieve), p):
                newsieve[i] = 0

        # Merge the sieves
        self._list += _array('l', [x for x in newsieve if x])

    def extend_to_no(self, i):
        """Extend to include the ith prime number.

        i must be an integer.

        The list is extended by 50% if it is too short, so it is
        likely that it will be longer than requested.

        Examples
        ========

        >>> from .. import sieve
        >>> sieve._reset() # this line for doctest only
        >>> sieve.extend_to_no(9)
        >>> sieve._list
        array('l', [2, 3, 5, 7, 11, 13, 17, 19, 23])
        """
        i = as_int(i)
        while len(self._list) < i:
            self.extend(int(self._list[-1] * 1.5))

    def primerange(self, a, b):
        """Generate all prime numbers in the range [a, b).

        Examples
        ========

        >>> from .. import sieve
        >>> print([i for i in sieve.primerange(7, 18)])
        [7, 11, 13, 17]
        """
        from ..functions.elementary.integers import ceiling

        # wrapping ceiling in int will raise an error if there was a problem
        # determining whether the expression was exactly an integer or not
        a = max(2, int(ceiling(a)))
        b = int(ceiling(b))
        if a >= b:
            return
        self.extend(b)
        i = self.search(a)[1]
        maxi = len(self._list) + 1
        while i < maxi:
            p = self._list[i - 1]
            if p < b:
                yield p
                i += 1
            else:
                return

    def search(self, n):
        """Return the indices i, j of the primes that bound n.

        If n is prime then i == j.

        Although n can be an expression, if ceiling cannot convert
        it to an integer then an n error will be raised.

        Examples
        ========

        >>> from .. import sieve
        >>> sieve.search(25)
        (9, 10)
        >>> sieve.search(23)
        (9, 9)
        """
        from ..functions.elementary.integers import ceiling

        # wrapping ceiling in int will raise an error if there was a problem
        # determining whether the expression was exactly an integer or not
        test = int(ceiling(n))
        n = int(n)
        if n < 2:
            raise ValueError("n should be >= 2 but got: %s" % n)
        if n > self._list[-1]:
            self.extend(n)
        b = bisect(self._list, n)
        if self._list[b - 1] == test:
            return b, b
        else:
            return b, b + 1

    def __contains__(self, n):
        try:
            n = as_int(n)
            assert n >= 2
        except (ValueError, AssertionError):
            return False
        if n % 2 == 0:
            return n == 2
        a, b = self.search(n)
        return a == b

    def __getitem__(self, n):
        """Return the nth prime number"""
        if isinstance(n, slice):
            self.extend_to_no(n.stop)
            return self._list[n.start - 1:n.stop - 1:n.step]
        else:
            n = as_int(n)
            self.extend_to_no(n)
            return self._list[n - 1]

# Generate a global object for repeated use in trial division etc
sieve = Sieve()


def prime(nth):
    """ Return the nth prime, with the primes indexed as prime(1) = 2,
        prime(2) = 3, etc.... The nth prime is approximately n*log(n).

        Logarithmic integral of x is a pretty nice approximation for number of
        primes <= x, i.e.
        li(x) ~ pi(x)
        In fact, for the numbers we are concerned about( x<1e11 ),
        li(x) - pi(x) < 50000

        Also,
        li(x) > pi(x) can be safely assumed for the numbers which
        can be evaluated by this function.

        Here, we find the least integer m such that li(m) > n using binary search.
        Now pi(m-1) < li(m-1) <= n,

        We find pi(m - 1) using primepi function.

        Starting from m, we have to find n - pi(m-1) more primes.

        For the inputs this implementation can handle, we will have to test
        primality for at max about 10**5 numbers, to get our answer.

        References
        ==========

        - https://en.wikipedia.org/wiki/Prime_number_theorem#Table_of_.CF.80.28x.29.2C_x_.2F_log_x.2C_and_li.28x.29
        - https://en.wikipedia.org/wiki/Prime_number_theorem#Approximations_for_the_nth_prime_number
        - https://en.wikipedia.org/wiki/Skewes%27_number

        Examples
        ========

        >>> from .. import prime
        >>> prime(10)
        29
        >>> prime(1)
        2
        >>> prime(100000)
        1299709

        See Also
        ========

        sympy.ntheory.primetest.isprime : Test if n is prime
        primerange : Generate all primes in a given range
        primepi : Return the number of primes less than or equal to n
    """
    n = as_int(nth)
    if n < 1:
        raise ValueError("nth must be a positive integer; prime(1) == 2")
    if n <= len(sieve._list):
        return sieve[n]

    from ..functions.special.error_functions import li
    from ..functions.elementary.exponential import log

    a = 2 # Lower bound for binary search
    b = int(n*(log(n) + log(log(n)))) # Upper bound for the search.

    while a < b:
        mid = (a + b) >> 1
        if li(mid) > n:
            b = mid
        else:
            a = mid + 1
    n_primes = primepi(a - 1)
    while n_primes < n:
        if isprime(a):
            n_primes += 1
        a += 1
    return a - 1


def primepi(n):
    """ Return the value of the prime counting function pi(n) = the number
        of prime numbers less than or equal to n.

        Algorithm Description:

        In sieve method, we remove all multiples of prime p
        except p itself.

        Let phi(i,j) be the number of integers 2 <= k <= i
        which remain after sieving from primes less than
        or equal to j.
        Clearly, pi(n) = phi(n, sqrt(n))

        If j is not a prime,
        phi(i,j) = phi(i, j - 1)

        if j is a prime,
        We remove all numbers(except j) whose
        smallest prime factor is j.

        Let x= j*a be such a number, where 2 <= a<= i / j
        Now, after sieving from primes <= j - 1,
        a must remain
        (because x, and hence a has no prime factor <= j - 1)
        Clearly, there are phi(i / j, j - 1) such a
        which remain on sieving from primes <= j - 1

        Now, if a is a prime less than equal to j - 1,
        x= j*a has smallest prime factor = a, and
        has already been removed(by sieving from a).
        So, we don't need to remove it again.
        (Note: there will be pi(j - 1) such x)

        Thus, number of x, that will be removed are:
        phi(i / j, j - 1) - phi(j - 1, j - 1)
        (Note that pi(j - 1) = phi(j - 1, j - 1))

        => phi(i,j) = phi(i, j - 1) - phi(i / j, j - 1) + phi(j - 1, j - 1)

        So,following recursion is used and implemented as dp:

        phi(a, b) = phi(a, b - 1), if b is not a prime
        phi(a, b) = phi(a, b-1)-phi(a / b, b-1) + phi(b-1, b-1), if b is prime

        Clearly a is always of the form floor(n / k),
        which can take at most 2*sqrt(n) values.
        Two arrays arr1,arr2 are maintained
        arr1[i] = phi(i, j),
        arr2[i] = phi(n // i, j)

        Finally the answer is arr2[1]

        Examples
        ========

        >>> from .. import primepi
        >>> primepi(25)
        9

        See Also
        ========

        sympy.ntheory.primetest.isprime : Test if n is prime
        primerange : Generate all primes in a given range
        prime : Return the nth prime
    """
    n = int(n)
    if n < 2:
        return 0
    if n <= sieve._list[-1]:
        return sieve.search(n)[0]
    lim = int(n ** 0.5)
    lim -= 1
    lim = max(lim,0)
    while lim * lim <= n:
        lim += 1
    lim-=1
    arr1 = [0] * (lim + 1)
    arr2 = [0] * (lim + 1)
    for i in range(1, lim + 1):
        arr1[i] = i - 1
        arr2[i] = n // i - 1
    for i in range(2, lim + 1):
        # Presently, arr1[k]=phi(k,i - 1),
        # arr2[k] = phi(n // k,i - 1)
        if arr1[i] == arr1[i - 1]:
            continue
        p = arr1[i - 1]
        for j in range(1,min(n // (i * i), lim) + 1):
            st = i * j
            if st <= lim:
                arr2[j] -= arr2[st] - p
            else:
                arr2[j] -= arr1[n // st] - p
        lim2 = min(lim, i*i - 1)
        for j in range(lim, lim2, -1):
            arr1[j] -= arr1[j // i] - p
    return arr2[1]


def nextprime(n, ith=1):
    """ Return the ith prime greater than n.

        i must be an integer.

        Notes
        =====

        Potential primes are located at 6*j +/- 1. This
        property is used during searching.

        >>> from .. import nextprime
        >>> [(i, nextprime(i)) for i in range(10, 15)]
        [(10, 11), (11, 13), (12, 13), (13, 17), (14, 17)]
        >>> nextprime(2, ith=2) # the 2nd prime after 2
        5

        See Also
        ========

        prevprime : Return the largest prime smaller than n
        primerange : Generate all primes in a given range

    """
    n = int(n)
    i = as_int(ith)
    if i > 1:
        pr = n
        j = 1
        while 1:
            pr = nextprime(pr)
            j += 1
            if j > i:
                break
        return pr

    if n < 2:
        return 2
    if n < 7:
        return {2: 3, 3: 5, 4: 5, 5: 7, 6: 7}[n]
    if n <= sieve._list[-2]:
        l, u = sieve.search(n)
        if l == u:
            return sieve[u + 1]
        else:
            return sieve[u]
    nn = 6*(n//6)
    if nn == n:
        n += 1
        if isprime(n):
            return n
        n += 4
    elif n - nn == 5:
        n += 2
        if isprime(n):
            return n
        n += 4
    else:
        n = nn + 5
    while 1:
        if isprime(n):
            return n
        n += 2
        if isprime(n):
            return n
        n += 4


def prevprime(n):
    """ Return the largest prime smaller than n.

        Notes
        =====

        Potential primes are located at 6*j +/- 1. This
        property is used during searching.

        >>> from .. import prevprime
        >>> [(i, prevprime(i)) for i in range(10, 15)]
        [(10, 7), (11, 7), (12, 11), (13, 11), (14, 13)]

        See Also
        ========

        nextprime : Return the ith prime greater than n
        primerange : Generates all primes in a given range
    """
    from ..functions.elementary.integers import ceiling

    # wrapping ceiling in int will raise an error if there was a problem
    # determining whether the expression was exactly an integer or not
    n = int(ceiling(n))
    if n < 3:
        raise ValueError("no preceding primes")
    if n < 8:
        return {3: 2, 4: 3, 5: 3, 6: 5, 7: 5}[n]
    if n <= sieve._list[-1]:
        l, u = sieve.search(n)
        if l == u:
            return sieve[l-1]
        else:
            return sieve[l]
    nn = 6*(n//6)
    if n - nn <= 1:
        n = nn - 1
        if isprime(n):
            return n
        n -= 4
    else:
        n = nn + 1
    while 1:
        if isprime(n):
            return n
        n -= 2
        if isprime(n):
            return n
        n -= 4


def primerange(a, b):
    """ Generate a list of all prime numbers in the range [a, b).

        If the range exists in the default sieve, the values will
        be returned from there; otherwise values will be returned
        but will not modify the sieve.

        Notes
        =====

        Some famous conjectures about the occurence of primes in a given
        range are [1]:

        - Twin primes: though often not, the following will give 2 primes
                    an infinite number of times:
                        primerange(6*n - 1, 6*n + 2)
        - Legendre's: the following always yields at least one prime
                        primerange(n**2, (n+1)**2+1)
        - Bertrand's (proven): there is always a prime in the range
                        primerange(n, 2*n)
        - Brocard's: there are at least four primes in the range
                        primerange(prime(n)**2, prime(n+1)**2)

        The average gap between primes is log(n) [2]; the gap between
        primes can be arbitrarily large since sequences of composite
        numbers are arbitrarily large, e.g. the numbers in the sequence
        n! + 2, n! + 3 ... n! + n are all composite.

        References
        ==========

        1. http://en.wikipedia.org/wiki/Prime_number
        2. http://primes.utm.edu/notes/gaps.html

        Examples
        ========

        >>> from .. import primerange, sieve
        >>> print([i for i in primerange(1, 30)])
        [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]

        The Sieve method, primerange, is generally faster but it will
        occupy more memory as the sieve stores values. The default
        instance of Sieve, named sieve, can be used:

        >>> list(sieve.primerange(1, 30))
        [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]

        See Also
        ========

        nextprime : Return the ith prime greater than n
        prevprime : Return the largest prime smaller than n
        randprime : Returns a random prime in a given range
        primorial : Returns the product of primes based on condition
        Sieve.primerange : return range from already computed primes
                           or extend the sieve to contain the requested
                           range.
    """
    from ..functions.elementary.integers import ceiling

    if a >= b:
        return
    # if we already have the range, return it
    if b <= sieve._list[-1]:
        for i in sieve.primerange(a, b):
            yield i
        return
    # otherwise compute, without storing, the desired range.

    # wrapping ceiling in int will raise an error if there was a problem
    # determining whether the expression was exactly an integer or not
    a = int(ceiling(a)) - 1
    b = int(ceiling(b))
    while 1:
        a = nextprime(a)
        if a < b:
            yield a
        else:
            return


def randprime(a, b):
    """ Return a random prime number in the range [a, b).

        Bertrand's postulate assures that
        randprime(a, 2*a) will always succeed for a > 1.

        References
        ==========

        - http://en.wikipedia.org/wiki/Bertrand's_postulate

        Examples
        ========

        >>> from .. import randprime, isprime
        >>> randprime(1, 30) #doctest: +SKIP
        13
        >>> isprime(randprime(1, 30))
        True

        See Also
        ========

        primerange : Generate all primes in a given range

    """
    if a >= b:
        return
    a, b = map(int, (a, b))
    n = random.randint(a - 1, b)
    p = nextprime(n)
    if p >= b:
        p = prevprime(b)
    if p < a:
        raise ValueError("no primes exist in the specified range")
    return p


def primorial(n, nth=True):
    """
    Returns the product of the first n primes (default) or
    the primes less than or equal to n (when ``nth=False``).

    >>> from .generate import primorial, randprime, primerange
    >>> from .. import factorint, Mul, primefactors, sqrt
    >>> primorial(4) # the first 4 primes are 2, 3, 5, 7
    210
    >>> primorial(4, nth=False) # primes <= 4 are 2 and 3
    6
    >>> primorial(1)
    2
    >>> primorial(1, nth=False)
    1
    >>> primorial(sqrt(101), nth=False)
    210

    One can argue that the primes are infinite since if you take
    a set of primes and multiply them together (e.g. the primorial) and
    then add or subtract 1, the result cannot be divided by any of the
    original factors, hence either 1 or more new primes must divide this
    product of primes.

    In this case, the number itself is a new prime:

    >>> factorint(primorial(4) + 1)
    {211: 1}

    In this case two new primes are the factors:

    >>> factorint(primorial(4) - 1)
    {11: 1, 19: 1}

    Here, some primes smaller and larger than the primes multiplied together
    are obtained:

    >>> p = list(primerange(10, 20))
    >>> sorted(set(primefactors(Mul(*p) + 1)).difference(set(p)))
    [2, 5, 31, 149]

    See Also
    ========

    primerange : Generate all primes in a given range

    """
    if nth:
        n = as_int(n)
    else:
        n = int(n)
    if n < 1:
        raise ValueError("primorial argument must be >= 1")
    p = 1
    if nth:
        for i in range(1, n + 1):
            p *= prime(i)
    else:
        for i in primerange(2, n + 1):
            p *= i
    return p


def cycle_length(f, x0, nmax=None, values=False):
    """For a given iterated sequence, return a generator that gives
    the length of the iterated cycle (lambda) and the length of terms
    before the cycle begins (mu); if ``values`` is True then the
    terms of the sequence will be returned instead. The sequence is
    started with value ``x0``.

    Note: more than the first lambda + mu terms may be returned and this
    is the cost of cycle detection with Brent's method; there are, however,
    generally less terms calculated than would have been calculated if the
    proper ending point were determined, e.g. by using Floyd's method.

    >>> from .generate import cycle_length

    This will yield successive values of i <-- func(i):

        >>> def iter(func, i):
        ...     while 1:
        ...         ii = func(i)
        ...         yield ii
        ...         i = ii
        ...

    A function is defined:

        >>> func = lambda i: (i**2 + 1) % 51

    and given a seed of 4 and the mu and lambda terms calculated:

        >>> next(cycle_length(func, 4))
        (6, 2)

    We can see what is meant by looking at the output:

        >>> n = cycle_length(func, 4, values=True)
        >>> list(ni for ni in n)
        [17, 35, 2, 5, 26, 14, 44, 50, 2, 5, 26, 14]

    There are 6 repeating values after the first 2.

    If a sequence is suspected of being longer than you might wish, ``nmax``
    can be used to exit early (and mu will be returned as None):

        >>> next(cycle_length(func, 4, nmax = 4))
        (4, None)
        >>> [ni for ni in cycle_length(func, 4, nmax = 4, values=True)]
        [17, 35, 2, 5]

    Code modified from:
        http://en.wikipedia.org/wiki/Cycle_detection.
    """

    nmax = int(nmax or 0)

    # main phase: search successive powers of two
    power = lam = 1
    tortoise, hare = x0, f(x0)  # f(x0) is the element/node next to x0.
    i = 0
    while tortoise != hare and (not nmax or i < nmax):
        i += 1
        if power == lam:   # time to start a new power of two?
            tortoise = hare
            power *= 2
            lam = 0
        if values:
            yield hare
        hare = f(hare)
        lam += 1
    if nmax and i == nmax:
        if values:
            return
        else:
            yield nmax, None
            return
    if not values:
        # Find the position of the first repetition of length lambda
        mu = 0
        tortoise = hare = x0
        for i in range(lam):
            hare = f(hare)
        while tortoise != hare:
            tortoise = f(tortoise)
            hare = f(hare)
            mu += 1
        if mu:
            mu -= 1
        yield lam, mu


def composite(nth):
    """ Return the nth composite number, with the composite numbers indexed as
        composite(1) = 4, composite(2) = 6, etc....

        Examples
        ========

        >>> from .. import composite
        >>> composite(36)
        52
        >>> composite(1)
        4
        >>> composite(17737)
        20000

        See Also
        ========

        sympy.ntheory.primetest.isprime : Test if n is prime
        primerange : Generate all primes in a given range
        primepi : Return the number of primes less than or equal to n
        prime : Return the nth prime
        compositepi : Return the number of positive composite numbers less than or equal to n
    """
    n = as_int(nth)
    if n < 1:
        raise ValueError("nth must be a positive integer; composite(1) == 4")
    composite_arr = [4, 6, 8, 9, 10, 12, 14, 15, 16, 18]
    if n <= 10:
        return composite_arr[n - 1]

    a, b = 4, sieve._list[-1]
    if n <= b - primepi(b) - 1:
        while a < b - 1:
            mid = (a + b) >> 1
            if mid - primepi(mid) - 1 > n:
                b = mid
            else:
                a = mid
        if isprime(a):
            a -= 1
        return a

    from ..functions.special.error_functions import li
    from ..functions.elementary.exponential import log

    a = 4 # Lower bound for binary search
    b = int(n*(log(n) + log(log(n)))) # Upper bound for the search.

    while a < b:
        mid = (a + b) >> 1
        if mid - li(mid) - 1 > n:
            b = mid
        else:
            a = mid + 1

    n_composites = a - primepi(a) - 1
    while n_composites > n:
        if not isprime(a):
            n_composites -= 1
        a -= 1
    if isprime(a):
        a -= 1
    return a


def compositepi(n):
    """ Return the number of positive composite numbers less than or equal to n.
        The first positive composite is 4, i.e. compositepi(4) = 1.

        Examples
        ========

        >>> from .. import compositepi
        >>> compositepi(25)
        15
        >>> compositepi(1000)
        831

        See Also
        ========

        sympy.ntheory.primetest.isprime : Test if n is prime
        primerange : Generate all primes in a given range
        prime : Return the nth prime
        primepi : Return the number of primes less than or equal to n
        composite : Return the nth composite number
    """
    n = int(n)
    if n < 4:
        return 0
    return n - primepi(n) - 1
