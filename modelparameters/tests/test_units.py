import unittest

from modelparameters.logger import suppress_logging
import pint
from modelparameters.parameters import ScalarParam, ureg

suppress_logging()

def get_unit_and_value(p):
    p_value = p if not hasattr(p, 'value') else p.value
    p_unit = "1" if not hasattr(p, 'unit') else p.unit
    return p_value, p_unit


class TestUnits(unittest.TestCase):

    p1 = ScalarParam(1.0, unit="m**2", name="area")
    p2 = ScalarParam(2.0, unit="s", name="time")
    p3 = ScalarParam(2.0, unit="m**2", name="some other area")
    p4 = ScalarParam(0.5, name="unitless parameter")
    v1 = 2.0
    v2 = -2.0
    

    def test_division(self):

        pairs = [(self.p1, self.p2), (self.p2, self.p1),
                 (self.p1, self.v1), (self.v1, self.p1),
                 (self.p1, self.v2), (self.v2, self.p1),
                 (self.p1, self.p4), (self.p4, self.p1)]

        for p1, p2 in pairs:
            p = p1 / p2
            
            p1_value, p1_unit = get_unit_and_value(p1)
            p2_value, p2_unit = get_unit_and_value(p2)
            
            self.assertEqual(p.value, p1_value / p2_value)
            self.assertEqual(ureg(p.unit).u, ureg("{}/{}".format(p1_unit,
                                                                 p2_unit)).u)

    def test_multiplication(self):

        pairs = [(self.p1, self.p2), (self.p2, self.p1),
                 (self.p1, self.v1), (self.v1, self.p1),
                 (self.p1, self.v2), (self.v2, self.p1),
                 (self.p1, self.p4), (self.p4, self.p1)]

        for p1, p2 in pairs:
            p = p1 * p2
            
            p1_value, p1_unit = get_unit_and_value(p1)
            p2_value, p2_unit = get_unit_and_value(p2)

            self.assertEqual(p.value, p1_value * p2_value)
            self.assertEqual(ureg(p.unit).u, ureg("{}*{}".format(p1_unit,
                                                                 p2_unit)).u)

    def test_addition(self):

        pairs = [(self.p1, self.v1), (self.v1, self.p1),
                 (self.p1, self.v2), (self.v2, self.p1),
                 (self.p1, self.p3), (self.p3, self.p1),
                 (self.p1, self.p4), (self.p4, self.p1)]

        for p1, p2 in pairs:
            p = p1 + p2
            
            p1_value, p1_unit = get_unit_and_value(p1)
            p2_value, p2_unit = get_unit_and_value(p2)

            if p1_unit == "1":
                p1_unit = p2_unit
            elif p2_unit == "1":
                p2_unit = p1_unit

            self.assertEqual(p.value, p1_value + p2_value)
            self.assertEqual(ureg(p.unit).u, ureg("{}+{}".format(p1_unit,
                                                                 p2_unit)).u)

        pairs = [(self.p1, self.p2), (self.p2, self.p1)]
        with self.assertRaises(pint.errors.DimensionalityError):
            for p1, p2 in pairs:
                p = p1 + p2

    def test_subtraction(self):

        pairs = [(self.p1, self.v1), (self.v1, self.p1),
                 (self.p1, self.v2), (self.v2, self.p1),
                 (self.p1, self.p3), (self.p3, self.p1),
                 (self.p1, self.p4), (self.p4, self.p1)]

        for p1, p2 in pairs:
            p = p1 - p2
            
            p1_value, p1_unit = get_unit_and_value(p1)
            p2_value, p2_unit = get_unit_and_value(p2)

            if p1_unit == "1":
                p1_unit = p2_unit
            elif p2_unit == "1":
                p2_unit = p1_unit

            self.assertEqual(p.value, p1_value - p2_value)
            self.assertEqual(ureg(p.unit).u, ureg("{}-{}".format(p1_unit,
                                                                 p2_unit)).u)

        pairs = [(self.p1, self.p2), (self.p2, self.p1)]
        with self.assertRaises(pint.errors.DimensionalityError):
            for p1, p2 in pairs:
                p = p1 - p2

    def test_power(self):

        pairs = [(self.p1, self.v1),
                 (self.p1, self.v2),
                 (self.p1, self.p4)]

        for p1, p2 in pairs:
            p = p1 ** p2
            
            p1_value, p1_unit = get_unit_and_value(p1)
            p2_value, p2_unit = get_unit_and_value(p2)

            self.assertEqual(p.value, p1_value ** p2_value)
            self.assertEqual(ureg(p.unit).u, ureg("({})**{}".format(p1_unit, p2_value)).u)

        with self.assertRaises(AssertionError):
            p = self.p1**self.p2


if __name__ == "__main__":
    unittest.main()
