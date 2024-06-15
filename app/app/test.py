from django.test import SimpleTestCase

from .calc import add


class CalcTests(SimpleTestCase):
    """Test calc module"""

    def test_add_numbers(self):
        test_cases = [(1, 2, 3), (5, 7, 12), (-1, -1, -2), (100, 200, 300)]

        for x, y, expected in test_cases:
            with self.subTest(x=x, y=y, expected=expected):
                res = add(x, y)
                self.assertEqual(res, expected)
