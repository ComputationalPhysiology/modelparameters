"""test for parameters module"""

try:
    import numpy as np
except:
    np = None

try:
    import sympy as sp
except:
    sp = None

import unittest

from modelparameters.logger import suppress_logging
from modelparameters.utils import *
from modelparameters.parameters import *

suppress_logging()

def dummy():pass

class TestParam(unittest.TestCase):
    def test_init(self):
        with self.assertRaises(TypeError) as cm:
            Param(45, 56)
        self.assertEqual(str(cm.exception), "expected a 'str' (got '56' "\
                         "which is 'int') as the 'name' argument")
        self.assertEqual(repr(Param(45, "jada")), "Param(45, name='jada')")
        
    def test_assign(self):
        with self.assertRaises(TypeError) as cm:
            p = Param(45, "bada")
            p.setvalue("jada")
        self.assertEqual(str(cm.exception), "expected 'int' while "\
                         "setting parameter 'bada'")

        with self.assertRaises(TypeError) as cm:
            p = Param("jada", "bada")
            p.setvalue(45)
        self.assertEqual(str(cm.exception), "expected 'str' while "\
                         "setting parameter 'bada'")

        with self.assertRaises(ValueError) as cm:
            p = Param("jada", "bada")
            p.name = "snaba"
        self.assertEqual(str(cm.exception), "Cannot set name attribute of "\
                         "Param, it is already set to 'bada'")

        p0 = Param(45, "bada")
        p1 = Param("jada", "snada")
        self.assertIsNone(p0.setvalue(56))
        self.assertEqual(p0.getvalue(), 56)
        self.assertIsNone(p1.setvalue("bada"))
        self.assertEqual(p1.getvalue(), "bada")

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
    
    def test_assign(self):
        with self.assertRaises(ValueError) as cm:
            p = OptionParam(45, [45, 56], "jada")
            p.name = "snaba"
        self.assertEqual(str(cm.exception), "Cannot set name attribute of "\
                         "OptionParam, it is already set to 'jada'")

        with self.assertRaises(ValueError) as cm:
            p = OptionParam(45, [45, 56], "jada")
            p.setvalue(57)
        self.assertEqual(str(cm.exception), "Illegal value 'jada': 57 "\
                         "\xe2\x88\x89 [45, 56]")
        
        with self.assertRaises(TypeError) as cm:
            p = OptionParam(45, [45, 56], "jada")
            p.setvalue("bada")
        self.assertEqual(str(cm.exception), "expected 'int' while setting "\
                         "parameter 'jada'")

        p0 = OptionParam(45, [45, 56])
        p1 = OptionParam("wuabba", ["snada", "bada", "wuabba"])

        self.assertIsNone(p0.setvalue(56))
        self.assertEqual(p0.getvalue(), 56)
        self.assertEqual(p1.getvalue(), "wuabba")
        self.assertIsNone(p1.setvalue("bada"))
        self.assertEqual(p1.getvalue(), "bada")
        
if __name__ == "__main__":
    unittest.main()
