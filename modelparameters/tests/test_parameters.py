"""test for parameters module"""

import unittest

from modelparameters.logger import suppress_logging
from modelparameters.utils import *
from modelparameters.parameters import *
from modelparameters.sympytools import *

try:
    import numpy as np
except:
    np = None

try:
    import sympy as sp
except:
    sp = None

suppress_logging()

def dummy():pass

class TestParam(unittest.TestCase):
    def test_init(self):
        with self.assertRaises(TypeError) as cm:
            Param(45, 56)
        self.assertEqual(str(cm.exception), "expected a 'str' (got '56' "\
                         "which is 'int') as the 'name' argument")
        self.assertEqual(repr(Param(45, "jada")), "Param(45, name='jada')")
        self.assertEqual(str(Param(45, "jada")), "45")
        
    def test_name_assign(self):
        with self.assertRaises(ValueError) as cm:
            p0 = Param(45, name="jada")
            p0.name = "bada"
        self.assertEqual(str(cm.exception), "Cannot set name attribute of "\
                         "Param, it is already set to 'jada'")

        p0 = Param(45)
        p0.name = "bada"
        self.assertEqual(p0.name, "bada")

        with self.assertRaises(ValueError) as cm:
            p0 = Param(45)
            p0.name = "bada"
            p0.name = "snada"
        self.assertEqual(str(cm.exception), "Cannot set name attribute of "\
                         "Param, it is already set to 'bada'")

    def test_assign(self):
        with self.assertRaises(TypeError) as cm:
            p = Param(45, "bada")
            p.value = "jada"
        self.assertEqual(str(cm.exception), "expected 'int' while "\
                         "setting parameter 'bada'")

        with self.assertRaises(TypeError) as cm:
            p = Param("jada", "bada")
            p.value = 45
        self.assertEqual(str(cm.exception), "expected 'str' while "\
                         "setting parameter 'bada'")

        with self.assertRaises(ValueError) as cm:
            p = Param("jada", "bada")
            p.name = "snaba"
        self.assertEqual(str(cm.exception), "Cannot set name attribute of "\
                         "Param, it is already set to 'bada'")

        p0 = Param(45, "bada")
        p1 = Param("jada", "snada")
        p0.value = 56
        self.assertEqual(p0.value, 56)
        p1.value = "bada"
        self.assertEqual(p1.value, "bada")

    def test_equal(self):
        p0 = Param("snada", "bada")
        p1 = Param("snada", "bada")
        self.assertTrue(p0==p1)
        p0.value = "bada"
        self.assertTrue(p0!=p1)
        
class TestOptionParam(unittest.TestCase):
    def test_init(self):
        with self.assertRaises(TypeError) as cm:
            OptionParam(45, [45, 56], 56)
        self.assertEqual(str(cm.exception), "expected a 'str' (got '56' "\
                         "which is 'int') as the 'name' argument")

        with self.assertRaises(ValueError) as cm:
            OptionParam(46, [])
        self.assertEqual(str(cm.exception), "expected the options argument "\
                         "to be at least of length 2")
    
        with self.assertRaises(ValueError) as cm:
            OptionParam(46, [46])
        self.assertEqual(str(cm.exception), "expected the options argument "\
                         "to be at least of length 2")
    
        with self.assertRaises(TypeError) as cm:
            OptionParam(45, [45, []])
        self.assertEqual(str(cm.exception), "options can only be 'str' and "\
                         "scalars got: 'list'")

        with self.assertRaises(ValueError) as cm:
            OptionParam(46, [45, 56])
        self.assertEqual(str(cm.exception), "Illegal value: 46 "\
                         "\xe2\x88\x89 [45, 56]")
        
        with self.assertRaises(TypeError) as cm:
            p = OptionParam(45, [45, "bada"], "jada")
        self.assertEqual(str(cm.exception), "All values of the 'option check' "\
                         "need to be of type: 'int'")

        self.assertEqual(repr(OptionParam(45, [45, 56])), "OptionParam(45, [45, 56])")
        self.assertEqual(repr(OptionParam(45, [45, 56], "bada")), \
                         "OptionParam(45, [45, 56], name='bada')")
        self.assertEqual(str(OptionParam(45, [45, 56], "bada")), \
                         "45 \xe2\x88\x88 [45, 56]")
    
    def test_name_assign(self):
        with self.assertRaises(ValueError) as cm:
            p0 = OptionParam(45, [45, 56], name="jada")
            p0.name = "bada"
        self.assertEqual(str(cm.exception), "Cannot set name attribute of "\
                         "OptionParam, it is already set to 'jada'")

        p0 = OptionParam(45, [45, 56])
        p0.name = "bada"
        self.assertEqual(p0.name, "bada")

        with self.assertRaises(ValueError) as cm:
            p0 = OptionParam(45, [45, 56])
            p0.name = "bada"
            p0.name = "snada"
        self.assertEqual(str(cm.exception), "Cannot set name attribute of "\
                         "OptionParam, it is already set to 'bada'")

    def test_assign(self):
        with self.assertRaises(ValueError) as cm:
            p = OptionParam(45, [45, 56], "jada")
            p.name = "snaba"
        self.assertEqual(str(cm.exception), "Cannot set name attribute of "\
                         "OptionParam, it is already set to 'jada'")

        with self.assertRaises(ValueError) as cm:
            p = OptionParam(45, [45, 56], "jada")
            p.value = 57
        self.assertEqual(str(cm.exception), "Illegal value 'jada': 57 "\
                         "\xe2\x88\x89 [45, 56]")
        
        with self.assertRaises(TypeError) as cm:
            p = OptionParam(45, [45, 56], "jada")
            p.value = "bada"
        self.assertEqual(str(cm.exception), "expected 'int' while setting "\
                         "parameter 'jada'")

        p0 = OptionParam(45, [45, 56])
        p1 = OptionParam("wuabba", ["snada", "bada", "wuabba"])

        p0.value = 56
        self.assertEqual(p0.value, 56)
        self.assertEqual(p1.value, "wuabba")

        p1.value = "bada"
        self.assertEqual(p1.value, "bada")
        
    def test_equal(self):
        p0 = OptionParam("snada", ["snada", "bada"], "bada")
        p1 = OptionParam("snada", ["snada", "bada"], "bada")
        self.assertTrue(p0==p1)
        p0.value = "bada"
        self.assertTrue(p0!=p1)
        
class TestConstParam(unittest.TestCase):
    def test_init(self):
        with self.assertRaises(TypeError) as cm:
            ConstParam(45, 56)
        self.assertEqual(str(cm.exception), "expected a 'str' (got '56' "\
                         "which is 'int') as the 'name' argument")
        self.assertEqual(repr(ConstParam(45)),
                         "ConstParam(45)")
        self.assertEqual(str(ConstParam(45)), "45 - Constant")
    
    def test_name_assign(self):
        with self.assertRaises(ValueError) as cm:
            p0 = ConstParam(45, name="jada")
            p0.name = "bada"
        self.assertEqual(str(cm.exception), "Cannot set name attribute of "\
                         "ConstParam, it is already set to 'jada'")

        p0 = ConstParam(45)
        p0.name = "bada"
        self.assertEqual(p0.name, "bada")

        with self.assertRaises(ValueError) as cm:
            p0 = ConstParam(45)
            p0.name = "bada"
            p0.name = "snada"
        self.assertEqual(str(cm.exception), "Cannot set name attribute of "\
                         "ConstParam, it is already set to 'bada'")

    def test_assign(self):
        with self.assertRaises(ValueError) as cm:
            p = ConstParam(45, "bada")
            p.value = 56
        self.assertEqual(str(cm.exception), "Illegal value 'bada': 56 != 45")

        p = ConstParam(45, "bada")
        p.value = 45.
        self.assertEqual(p.value, 45)
        
class TestScalarParam(unittest.TestCase):
    def test_init(self):
        with self.assertRaises(TypeError) as cm:
            ScalarParam("jada")
        self.assertEqual(str(cm.exception), "expected a 'scalar' (got 'jada' "\
                         "which is 'str') as the first argument while "\
                         "instantiating 'ScalarParam'")

        self.assertEqual(repr(ScalarParam(45)),
                         "ScalarParam(45)")
        self.assertEqual(repr(ScalarParam(45, name="jada")),
                         "ScalarParam(45, name='jada')")
        self.assertEqual(repr(ScalarParam(45, name="jada", symname="bada.jada")),
                         "ScalarParam(45, name='jada', symname='bada.jada')")

        with self.assertRaises(TypeError) as cm:
            ScalarParam(45, symname="jada")
        self.assertEqual(str(cm.exception), "expected no symname when name "\
                         "is not set")
        
        with self.assertRaises(ValueError) as cm:
            ScalarParam(45, ge=0, gt=0)
        self.assertEqual(str(cm.exception), "Cannot create a 'Range' "\
                         "including both 'ge' and 'gt'")

        with self.assertRaises(ValueError) as cm:
            ScalarParam(45, 50)
        self.assertEqual(str(cm.exception), "Illegal value: 45 \xe2\x88\x89 "\
                         "[50, \xe2\x88\x9e]")

        with self.assertRaises(ValueError) as cm:
            ScalarParam(45, 0, lt=10)
        self.assertEqual(str(cm.exception), "Illegal value: 45 \xe2\x88\x89 "\
                         "[0, 10)")

    def test_name_assign(self):
        with self.assertRaises(ValueError) as cm:
            p0 = ScalarParam(45, name="jada")
            p0.name = "bada"
        self.assertEqual(str(cm.exception), "Cannot set name attribute of "\
                         "ScalarParam, it is already set to 'jada'")

        with self.assertRaises(ValueError) as cm:
            p0 = ScalarParam(45)
            p0.name = "bada"
            p0.name = "snada"
        self.assertEqual(str(cm.exception), "Cannot set name attribute of "\
                         "ScalarParam, it is already set to 'bada'")

        if sp is None:
            return
        
        p0 = ScalarParam(45)
        p0.name = "bada", "bada.sym"
        self.assertEqual(p0.name, "bada")
        self.assertEqual(str(p0.sym), "bada.sym")

    def test_value_assign(self):
        with self.assertRaises(ValueError) as cm:
            p = ScalarParam(5, 0, lt=10)
            p.value = 56
        self.assertEqual(str(cm.exception), "Illegal value: 56 "\
                         "\xe2\x88\x89 [0, 10)")

        with self.assertRaises(TypeError) as cm:
            p = ScalarParam(5, 0, lt=10)
            p.value = []
        self.assertEqual(str(cm.exception), "expected 'int' while "\
                         "setting parameter")

        p = ScalarParam(5., 0, lt=10)
        p.value = 6
        self.assertEqual(p.value, 6.0)
        self.assertTrue(isinstance(p.value, float))
        
        p = ScalarParam(5, 0, lt=10)
        p.value = 6.3
        self.assertEqual(p.value, 6)
        self.assertTrue(isinstance(p.value, int))

        p = ScalarParam(5, 0, lt=10, name="jada")

    def test_equal(self):
        p0 = ScalarParam(50, 0, lt=100, name="bada")
        p1 = ScalarParam(50, 0, lt=100, name="bada")
        self.assertTrue(p0==p1)
        p0.value = 0
        self.assertTrue(p0!=p1)

        p0 = ScalarParam(50, 0, le=100, name="bada")
        p1 = ScalarParam(50, 0, lt=100, name="bada")
        self.assertTrue(p0!=p1)
        
    def test_sym_access(self):
        if sp is None:
            return

        p0 = ScalarParam(5, 0, lt=10, name="jada")
        p1 = ScalarParam(0.5, 0, lt=100, name="bada")

        expr = p0.sym*sp.exp(5*p1.sym)

        for symbol_param in symbol_params_from_expr(expr):
            self.assertTrue(symbol_param in [p0.sym, p1.sym])
        
        for symbol_param in iter_symbol_params_from_expr(expr):
            self.assertTrue(symbol_param in [p0.sym, p1.sym])
        
        ns = symbol_param_value_namespace(expr)

        import math
        ns.update(math.__dict__)
        
        self.assertEqual(eval(str(expr), ns), 5*math.exp(5*0.5))
        
        
            
        
        
if __name__ == "__main__":
    unittest.main()
