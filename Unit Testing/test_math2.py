from .. import math2
from .. import math2
import unittest

class TestMath(unittest.TestCase):
    def test_sum(self):
        a = 123
        b = 456
        self.assertEqual(add(a,b), a + b)

    def test_substract(self):
        a = 123
        b = 456
        self.assertEqual(subtract(a,b), a - b)

if __name__ == '__main__':
    unittest.main()
