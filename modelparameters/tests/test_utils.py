"""test for utils module"""

import unittest

from modelparameters.logger import suppress_logging
from modelparameters.utils import *

suppress_logging()

def dummy():pass

class CheckArgs(unittest.TestCase):
    def test_check_arg(self):

        with self.assertRaises(TypeError) as cm:
            check_arg(1, str)
        self.assertEqual(str(cm.exception), \
                         "expected a 'str' (got '1' which is 'int')")

        with self.assertRaises(TypeError) as cm:
            check_arg(1, str, 0)
        self.assertEqual(str(cm.exception), "expected a 'str' (got '1' which is "\
                         "'int') as the first argument")

        with self.assertRaises(TypeError) as cm:
            check_arg(["s"], list, itemtype=int)
        self.assertEqual(str(cm.exception), "expected a 'list' of 'int'")

        with self.assertRaises(TypeError) as cm:
            check_arg(1, str, 2)
        self.assertEqual(str(cm.exception), "expected a 'str' (got '1' which is "\
                         "'int') as the third argument")

        with self.assertRaises(TypeError) as cm:
            check_arg(1, str, 2, CheckArgs.test_check_arg)
        self.assertEqual(str(cm.exception), "expected a 'str' (got '1' which is "\
                         "'int') as the third argument while calling "\
                         "'CheckArgs.test_check_arg'")

        with self.assertRaises(TypeError) as cm:
            check_arg(1, str, 2, CheckArgs)

        self.assertEqual(str(cm.exception), "expected a 'str' (got '1' which is "\
                         "'int') as the third argument while instantiating "\
                         "'CheckArgs'")

        with self.assertRaises(ValueError) as cm:
            check_arg(1, int, context=dummy, gt=2)
        self.assertEqual(str(cm.exception), "1 \xe2\x88\x89 (2, \xe2\x88\x9e] "\
                         "while calling 'dummy'")

        with self.assertRaises(ValueError) as cm:
            check_arg(1, int, gt=2, le=3)
        self.assertEqual(str(cm.exception), "1 \xe2\x88\x89 (2, 3]")

        with self.assertRaises(ValueError) as cm:
            check_arg(5, int, ge=2, lt=3)
        self.assertEqual(str(cm.exception), "5 \xe2\x88\x89 [2, 3)")

        self.assertIsNone(check_arg(1, int))
        self.assertIsNone(check_arg(1, scalars))
        self.assertIsNone(check_arg(1.0, scalars))
        self.assertIsNone(check_arg(1.0, (float, int)))
        self.assertIsNone(check_arg([1.0, 2.0], list, itemtype=float))
        self.assertIsNone(check_arg(1.0, scalars, gt=0, lt=2))
        self.assertIsNone(check_arg(5, scalars, ge=0, le=10))

    def test_check_kwarg(self):

        with self.assertRaises(TypeError) as cm:
            check_kwarg(1, "jada", str)
        self.assertEqual(str(cm.exception), \
                         "expected a 'str' (got '1' which is 'int')")

        with self.assertRaises(TypeError) as cm:
            check_arg(1, str, 0)
        self.assertEqual(str(cm.exception), "expected a 'str' (got '1' which is "\
                         "'int') as the first argument")

        with self.assertRaises(TypeError) as cm:
            check_arg(["s"], list, itemtype=int)
        self.assertEqual(str(cm.exception), "expected a 'list' of 'int'")

        with self.assertRaises(TypeError) as cm:
            check_arg(1, str, 2)
        self.assertEqual(str(cm.exception), "expected a 'str' (got '1' which is "\
                         "'int') as the third argument")

        with self.assertRaises(TypeError) as cm:
            check_arg(1, str, 2, CheckArgs.test_check_arg)
        self.assertEqual(str(cm.exception), "expected a 'str' (got '1' which is "\
                         "'int') as the third argument while calling "\
                         "'CheckArgs.test_check_arg'")

        with self.assertRaises(TypeError) as cm:
            check_arg(1, str, 2, CheckArgs)

        self.assertEqual(str(cm.exception), "expected a 'str' (got '1' which is "\
                         "'int') as the third argument while instantiating "\
                         "'CheckArgs'")

        with self.assertRaises(ValueError) as cm:
            check_arg(1, int, context=dummy, gt=2)
        self.assertEqual(str(cm.exception), "1 \xe2\x88\x89 (2, \xe2\x88\x9e] "\
                         "while calling 'dummy'")

        with self.assertRaises(ValueError) as cm:
            check_arg(1, int, gt=2, le=3)
        self.assertEqual(str(cm.exception), "1 \xe2\x88\x89 (2, 3]")

        with self.assertRaises(ValueError) as cm:
            check_arg(5, int, ge=2, lt=3)
        self.assertEqual(str(cm.exception), "5 \xe2\x88\x89 [2, 3)")

        self.assertIsNone(check_arg(1, int))
        self.assertIsNone(check_arg(1, scalars))
        self.assertIsNone(check_arg(1.0, scalars))
        self.assertIsNone(check_arg(1.0, (float, int)))
        self.assertIsNone(check_arg([1.0, 2.0], list, itemtype=float))
        self.assertIsNone(check_arg(1.0, scalars, gt=0, lt=2))
        self.assertIsNone(check_arg(5, scalars, ge=0, le=10))

if __name__ == "__main__":
    unittest.main()
