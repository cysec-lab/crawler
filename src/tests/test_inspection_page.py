import unittest

from inspection_page import str_mix_upper_lower

class TestStringMethods(unittest.TestCase):
    def test_str_mix_upper_lower(self):
        list_str = str_mix_upper_lower("abcd")
        list_str.sort()
        self.assertEqual(16, len(list_str))

        self.assertEqual([
            'ABCD', 'ABCd', 'ABcD', 'ABcd', 'AbCD', 'AbCd', 'AbcD', 'Abcd', 'aBCD', 'aBCd', 'aBcD', 'aBcd', 'abCD', 'abCd', 'abcD', 'abcd'],
            list_str
        )

        list_longstr = str_mix_upper_lower("abcdefgh")
        self.assertEqual(256, len(list_longstr))

if __name__ == '__main__':
    unittest.main()