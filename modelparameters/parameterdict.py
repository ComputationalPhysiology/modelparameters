#!/usr/bin/env python
"""Contains the ParameterDict class, useful for defining
recursive dictionaries of parameters and using attribute
syntax for later access.

Some useful features:
- Recursive copy function of parameter subsets
- Recursive update function including parameter subsets
- Recursive indented pretty-print
- Valid parameters are declared as keyword arguments to the constructor, 
  and assigning to indeclared variables is not allowed.

See help(ParameterDict) for an interactive example.
"""

__author__ = "Martin Sandve Alnaes <martin.alnes@gmail.com>, "\
             "Johan Hake <hake.dev@gmail.com>"
__date__ = "2008-06-22 -- 2012-06-27"
__copyright__ = "Copyright (C) 2008-2010 " + __author__
__license__  = "GNU LGPL Version 3.0 or later"

__all__ = ["Param", "RangeParam", "OptionParam", "ConstParam", "ArrayParam", \
           "inf", "ParameterDict"]

# System imports
import sympy
from string import ljust, rjust, center

# local imports
from parcheck import *
from logger import *

KEY_JUST = ljust
PAR_PREFIX = "--"
FORMAT_CONVERTER = {int:"int", float:"float", str:"string", \
                    list:None, tuple:None, bool:"int"}

value_formatter = repr

def par_cmp(obj1, obj2):
    assert(isinstance(obj1, tuple))
    assert(isinstance(obj2, tuple))
    assert(isinstance(obj1[0], str))
    assert(isinstance(obj2[0], str))
    if isinstance(obj1[1], ParameterDict) and \
           not isinstance(obj2[1], ParameterDict):
        return -1
    if not isinstance(obj1[1], ParameterDict) and \
           isinstance(obj2[1], ParameterDict):
        return 1
    return cmp(obj1[0], obj2[0])
        

class ParameterDict(dict):
    """A dictionary with attribute-style access, 
    that maps attribute access to the real dictionary.
    
    Interactive example:
    >>> m = ParameterDict(Re = 1.0, f = "sin(x)")
    >>> print m
    Re = 1.0
    f  = 'sin(x)'
    >>> s = ParameterDict(max_iterations = 10, tolerance = 1e-8)
    >>> print s
    max_iterations =    10
    tolerance      = 1e-08
    >>> p = ParameterDict(model = m, solver = s)
    >>> print p
    model = {
        Re = 1.0
        f  = 'sin(x)'
    }
    solver = {
        max_iterations =    10
        tolerance      = 1e-08
    }
    >>> q = p.copy()
    >>> q.model.Re = 2.3e6
    >>> q.solver.max_iterations = 100
    >>> print q
    model = {
        Re = 2300000.0
        f  =  'sin(x)'
    }
    solver = {
        max_iterations =   100
        tolerance      = 1e-08
    }
    >>> print p
    model = {
        Re = 1.0
        f  = 'sin(x)'
    }
    solver = {
        max_iterations =    10
        tolerance      = 1e-08
    }
    >>> p.update(q)
    >>> print p
    model = {
        Re = 2300000.0
        f  =  'sin(x)'
    }
    solver = {
        max_iterations =   100
        tolerance      = 1e-08
    }
    >>> s.nothere = 123
    Traceback (most recent call last):
    AttributeError: 'nothere' is not an item in this ParameterDict.
    >>> p0 = RangeParam(5., ge=0, le=10)
    >>> p1 = RangeParam(6., ge=0, le=10)
    >>> p = ParameterDict(p0=p0, p1=p1, slave=(2 + p0)/p1)
    >>> print p
    p0    =           5.0 \xe2\x88\x88 [0, 10]
    p1    =           6.0 \xe2\x88\x88 [0, 10]
    slave = 1.16666666667 - ParSlave((2 + p0)/p1)
    >>> q = p.copy()
    >>> p.p0 = 10
    >>> print p.slave
    2.0
    >>> print q
    p0    =           5.0 \xe2\x88\x88 [0, 10]
    p1    =           6.0 \xe2\x88\x88 [0, 10]
    slave = 1.16666666667 - ParSlave((2 + p0)/p1)
    """
    def __init__(self, **params):

        # Init the dict with the provided parameters
        for key, value in params.items():
            if key in list(dict.__dict__) + ["format_data", \
                                             "parse_args", "optstr"]:
                raise TypeError, "The name of a parameter cannot be "\
                      "an attribute of 'ParameterDict': %s"%key
            if isinstance(value, sympy.Basic) and \
                   all(isinstance(atom, (sympy.Number, ParSymbol))
                       for atom in value.atoms()):
                params[key] = ParSlave(value, key)
            elif isinstance(value, Param):
                if value.name is None:
                    value.name = key
            elif not isinstance(value, ParameterDict):
                params[key] = Param(value, key)

        assert(all(params.keys()))
        dict.__init__(self, **params)
        
    def __getstate__(self):
        return self.__dict__.items()
    
    def __setstate__(self, items):
        for key, val in items:
            self.__setattr__(key, val)
    
    def __str__(self):
        return self.format_data()
    
    def __repr__(self):
        return "%s(%s)"%(self.__class__.__name__, ", ".join("%s=%s" %\
            (k, repr(v)) for k, v in sorted(dict.iteritems(self), par_cmp)))
    
    def __delitem__(self, key):
        return dict.__delitem__(self, key)
    
    def __setattr__(self, key, value):
        assert isinstance(key, str)
        
        # Check if key is a registered parameter
        if not dict.__contains__(self, key):
            raise AttributeError("'%s' is not an item in this "\
                                 "ParameterDict."%key)

        # Get the original value, used for checks 
        org_value = dict.__getitem__(self, key)
        
        # Set the new value
        if isinstance(org_value, Param):
            org_value.setvalue(value)
        else:
            dict.__setitem__(self, key, value)
    
    def __getattr__(self, key):
        if not dict.__contains__(self, key):
            raise AttributeError("'%s' is not an item in this "\
                                 "ParameterDict."%key)
        
        value = dict.__getitem__(self, key)
        
        if isinstance(value, Param):
            value = value.getvalue()
        return value
    
    def __setitem__(self, key, value):
        self.__setattr__(key, value)

    def __getitem__(self, key):
        return self.__getattr__(key)

    # A nice string to use '\xe2\x88\x88'= \in and '\xe2\x88\x9e'= \infty
    def format_data(self, indent=None):
        """
        Make a recursive indented pretty-print string of
        self and parameter subsets."""
        if indent is None:
            indent = 0
        max_key_length   = 0
        max_value_length = 0
        max_length       = 15
        for key, value in dict.iteritems(self):
            if not isinstance(value, type(self)):
                if len(key) > max_key_length:
                    max_key_length = min(len(key), max_length)
                    value_length = value.length_value_format() \
                                   if isinstance(value, Param) \
                                   else len(str(value))
                if value_length > max_value_length:
                    max_value_length = min(value_length, max_length)
        s = ""
        for key, value in sorted(dict.iteritems(self), par_cmp):
            # If the value is a ParameterDict
            if isinstance(value, type(self)):
                s += "    "*indent + "%s = {\n"%key
                s += value.format_data(indent+1)
                s += "\n" + "    "*indent + "}\n"
            elif isinstance(value, Param):
                s += "    "*indent + "%s = %s\n"%\
                     (KEY_JUST(key, max_key_length), \
                      value.format_data(str_length=max_value_length))
            else:
                s += "    "*indent + "%s = %s\n"%\
                     (KEY_JUST(key, max_key_length), \
                      VALUE_JUST(str(value), max_value_length))
        return s[:-1]
    
    def copy(self, to_dict=False):
        """
        Make a copy of self, including recursive copying of parameter subsets.
        Parameter values themselves are not copied."""
        items = {}
        slaves = []
        for key in dict.iterkeys(self):
            value = dict.__getitem__(self, key)
            # If the value is a ParameterDict
            if isinstance(value, ParameterDict):
                items[key] = value.copy(to_dict)
            else:
                if to_dict and isinstance(value, Param):
                    items[key] = value.getvalue()
                elif isinstance(value, ParSlave):
                    slaves.append(value)
                else:
                    items[key] = eval(repr(value))
        
        if slaves:
            for slave in slaves:
                items[slave.name] = eval(slave._str_repr(), items)

        # FIXME: Why is this nessesary?
        items.pop("__builtins__", None)
        
        if to_dict:
            ch = dict(**items)
        else:
            ch = ParameterDict(**items)
        return ch

    def update(self, other):
        """
        A recursive update that handles parameter subsets
        correctly unlike dict.update."""
        for key in dict.iterkeys(other):
            if key not in self:
                continue
            self_value  = self[key]
            other_value = other[key]
            if isinstance(self_value, dict):
                # Update my own subdict with others subdict
                self_value.update(other_value)
            else:
                # Set my own value to others value
                self[key] = other_value

    def parse_args(self):
        " Parse a list of options. use sys.argv as default"
        import optparse

        parser = optparse.OptionParser(usage = "usage: %prog [options]")
        
        def callback(parent, key, value_type, sequence_type=None):
            " Return a callback function that is used to parse the argument"
            if value_type in [int, float, str, bool]:
                def par_setter(option, opt_str, value, parser):
                    " Callback function to set the parameter from the options."
                    try:
                        parent[key] = value
                        #debug("Setting parameter %s to %s"%\
                        # (opt_str.replace(PAR_PREFIX, ""), str(value)))
                    except ValueError, e:
                        raise optparse.OptionValueError(\
                            "Trying to set '%s' but %s"%(key, str(e)))

            else:
                def par_setter(option, opt_str, value, parser):
                    assert value is None
                    done = 0
                    value = []
                    rargs = parser.rargs
                    while rargs:
                        arg = rargs[0]
                        
                        # Stop if we hit an arg like "--par", i.e, PAR_PREFIX
                        if PAR_PREFIX in arg:
                            break
                        else:
                            try:
                                # Convert the value
                                item = sequence_type(arg)
                                value.append(item)
                            except  ValueError, e:
                                raise optparse.OptionValueError(\
                                    "Could not convert %s to '%s', while "\
                                    "setting parameter %s; %s"%\
                                    (arg, sequence_type.__name__, key, str(e)))
                                
                            del rargs[0]
                            
                    try:
                        # Changing a list to a tuple if needed
                        parent[key] = value_type(value)
                        #debug("Setting parameter %s to %s"%\
                        #(opt_str.replace(PAR_PREFIX, ""), str(value)))
                    except ValueError, e:
                        raise optparse.OptionValueError(\
                            "Trying to set '%s' but %s"%(key, str(e)))
                
            return par_setter
        
        def add_options(parent, opt_base):
            for key, value in sorted(dict.iteritems(parent), par_cmp):
                opt_base_copy = opt_base[:]
                if opt_base != PAR_PREFIX:
                    opt_base_copy += "."
                # If the value is a ParameterDict
                if isinstance(value, ParameterDict):
                    # Call the function recursively
                    add_options(value, "%s%s"%(opt_base_copy, key))
                elif isinstance(value, Param):

                    # ConstParam, ArrayParam cannot be parsed, yet
                    if isinstance(value, ArrayParam, ConstParam):
                        continue
                    
                    # If the value is a Param get the value
                    value = value.getvalue()
                
                # Check for available types
                if not type(value) in FORMAT_CONVERTER.keys():
                    continue

                if isinstance(value, (list, tuple)):
                    # If a default length of the list or tuple is 0, 
                    # assume sequence type to be int
                    if len(value) == 0:
                        sequence_type = int
                    else:
                        # Else assume it to be equal to the first argument
                        sequence_type = type(value[0])
                else:
                    sequence_type = None
                
                # Add option with callback function
                parser.add_option("%s%s"%(opt_base_copy, key), \
                        action = "callback", 
                        callback = callback(\
                                parent, key, type(value), sequence_type), 
                        type = FORMAT_CONVERTER[type(value)], 
                        help = "Default: %s"%str(value),
                        )
        
        # Start recursively adding options
        add_options(self, PAR_PREFIX)

        # Parse command line options
        parser.parse_args()

    def optstr(self):
        """ Return an string with option set
        
        An option string can be sent to a script useing a parameter dict
        to set its parameters from command line options
        """
        def option_list(parent, opt_base):
            ret_list = []
            opt_base_copy = opt_base[:]
            if opt_base != PAR_PREFIX:
                opt_base_copy += "."
            for key, value in sorted(dict.iteritems(parent), par_cmp):
                # If the value is a ParameterDict
                if isinstance(value, ParameterDict):
                    # Call the function recursively
                    ret_list.extend(\
                        option_list(value, "%s%s"%(opt_base_copy, key)))
                elif isinstance(value, Param):
                    if isinstance(value, (ConstParam, ParSlave)):
                        continue
                    # If the value is a Param get the value
                    value = value.getvalue()
                    
                # Check for available types
                if not type(value) in FORMAT_CONVERTER.keys():
                    continue

                ret_list.append("%s%s"%(opt_base_copy, key))
                if type(value) in [list, tuple]:
                    for item in value:
                        ret_list.append(str(item))
                else:
                    value = int(value) if isinstance(value, bool) else value
                    ret_list.append(str(value))
                        
            return ret_list
        
        return " " + " ".join(option_list(self, PAR_PREFIX))
    
# Test code
if __name__ == "__main__":
    
    def default_a():
        p = ParameterDict(abla="sin", abli=123)
        return p

    def default_b():
        p = ParameterDict(bblal=987, 
                          bling=OptionParam("akjh", \
                                            ["akjh", "bla", "jada", "smada"]))
        return p

    def default_params():
        p = ParameterDict(something = "3", 
                          other = RangeParam(.1239, le=10, gt=0), 
                          a = default_a(), 
                          b = default_b(), 
                          const = ConstParam(3), 
                         )
        return p

    # Get a defined set of parameters
    p = default_params()

    print "print p"
    print p
    # Test parameter setting
    p.something = "9"
    p.other     = 8.1340
    p.b.bling   = "jada"
    # Test parameter setting exceptions
    try:
        p.blatti = 7
        raise RuntimeError("Failed to throw exception on erroneous parameter"\
                           " assignment.")
    except RuntimeError, e:
        raise e
    except:
        pass

    # Test parameter setting exceptions
    try:
        p.other = "not a float"
        raise RuntimeError("Failed to throw exception on erroneous parameter"\
                           " assignment.")
    except RuntimeError, e:
        raise e
    except:
        pass

    # Test parameter setting exceptions
    try:
        p.other = 11.0
        raise RuntimeError("Failed to throw exception on erroneous parameter"\
                           " assignment.")
    except RuntimeError, e:
        raise e
    except:
        pass

    # Test parameter setting exceptions
    try:
        p.b.bling = "not in list"
        raise RuntimeError("Failed to throw exception on erroneous parameter"\
                           " assignment.")
    except RuntimeError, e:
        raise e
    except:
        pass

    # Test parameter setting exceptions
    try:
        p.const = 11.0
        raise RuntimeError("Failed to throw exception on erroneous parameter"\
                           " assignment.")
    except RuntimeError, e:
        raise e
    except:
        pass

    # Test ParameterDict creation
    try:
        fail = ParameterDict(jada = OptionParam(1, [0, 3, 4]))
        raise RuntimeError("Failed to throw exception on erroneous "\
                           "ParameterDict creation.")
    except RuntimeError, e:
        raise e
    except:
        pass
    
    # Test ParameterDict creation
    try:
        fail = ParameterDict(jada = OptionParam(1, [0, "jada", 4]))
        raise RuntimeError("Failed to throw exception on erroneous "\
                           "ParameterDict creation.")
    except RuntimeError, e:
        raise e
    except:
        pass
    
    # Test ParameterDict creation
    try:
        fail = ParameterDict(jada = RangeParam(1, lt=0))
        raise RuntimeError("Failed to throw exception on erroneous "\
                           "ParameterDict creation.")
    except RuntimeError, e:
        raise e
    except:
        pass
    
    # Test ParameterDict creation
    try:
        fail = ParameterDict(jada = OptionParam(True, [True, False]))
        raise RuntimeError("Failed to throw exception on erroneous "\
                           "ParameterDict creation.")
    except RuntimeError, e:
        raise e
    except:
        pass
    
    # Test ParameterDict creation
    try:
        fail = ParameterDict(jada = RangeParam(12, lt = "bada"))
        raise RuntimeError("Failed to throw exception on erroneous "\
                           "ParameterDict creation.")
    except RuntimeError, e:
        raise e
    except:
        pass
    
    # Test ParameterDict creation
    try:
        fail = ParameterDict(jada = RangeParam(12, le=45, gt=45))
        raise RuntimeError("Failed to throw exception on erroneous "\
                           "ParameterDict creation.")
    except RuntimeError, e:
        raise e
    except:
        pass
    
    # Test ParameterDict creation
    try:
        fail = ParameterDict(jada = RangeParam(12, le=45, gt=55))
        raise RuntimeError("Failed to throw exception on erroneous "\
                           "ParameterDict creation.")
    except RuntimeError, e:
        raise e
    except:
        pass
    
    # Test ParameterDict creation
    try:
        fail = ParameterDict(jada = RangeParam(12, le=45, gt=35))
        raise RuntimeError("Failed to throw exception on erroneous "\
                           "ParameterDict creation.")
    except RuntimeError, e:
        raise e
    except:
        pass
    
    # Test ParameterDict creation
    try:
        fail = ParameterDict(jada = RangeParam(12, le=45, lt=35))
        raise RuntimeError("Failed to throw exception on erroneous "\
                           "ParameterDict creation.")
    except RuntimeError, e:
        raise e
    except:
        pass

    # Test iteration:
    for k in p.keys():
        print k 
    for k in p.iterkeys():
        print k 
    for v in p.values():
        print v 
    for v in p.itervalues():
        print v 
    for k, v in p.items():
        print k, v
    for k, v in p.iteritems():
        print k, v
    
    # Test random access:
    ap1 = p.a
    ap2 = p["a"]
    assert ap1 is ap2
    
    # Test printing of parameter set
    print 
    print "str(p):"
    print str(p)
    print 
    print "repr(p):"
    print repr(p)
    print 
    
    # Test copy
    q = p.copy()
    q.something = "q specific!"
    q.a.abla = "q.a specific!"
    print 
    print "Should be different:"
    print repr(p)
    print repr(q)
    
    # Test update
    p.update(q)
    print 
    print "Should be equal:"
    print repr(q)
    print repr(p)

    # Test indented formatting:
    print
    print q.format_data()

    print p

    p.parse_args()

    print p

    # Run doctest
    import doctest
    doctest.testmod()


