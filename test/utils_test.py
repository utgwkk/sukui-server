import unittest
import json
from urllib.parse import quote
import utils


class UtilsTest(unittest.TestCase):
    def test_ngram(self):
        self.assertEqual(
            '+美玲',
            utils.ngram('美玲')
        )

    def test_ngram_2(self):
        self.assertEqual(
            '+しょ +ょう +うさ +さち',
            utils.ngram('しょうさち')
        )

    def test_ngram_3(self):
        self.assertEqual(
            '薫*',
            utils.ngram('薫')
        )


if __name__ == '__main__':
    unittest.main()
