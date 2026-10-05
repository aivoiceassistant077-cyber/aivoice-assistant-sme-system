"""Unit tests for the NLP engine (nlp/parser.py). Run with:  python -m pytest -v"""
import os
import sys
import unittest
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nlp.parser import extract_date, fold, parse, words_to_numbers  # noqa: E402
from tests.cases import NLP_CASES, PRODUCTS  # noqa: E402


class TestNLP(unittest.TestCase):
    def test_all_cases(self):
        for tid, sentence, lang, intent, entities in NLP_CASES:
            with self.subTest(case=tid):
                r = parse(sentence, PRODUCTS, today=date(2026, 10, 1))
                self.assertEqual(r["intent"], intent, "%s intent" % tid)
                self.assertEqual(r["language"], lang, "%s language" % tid)
                for k, v in entities.items():
                    self.assertEqual(r["entities"].get(k), v, "%s entity %s" % (tid, k))

    def test_fold_krio_letters(self):
        self.assertEqual(fold("Kɔstoma"), "kostoma")

    def test_number_words(self):
        self.assertEqual(words_to_numbers(["twenty", "five", "rice"]), ["25", "rice"])
        self.assertEqual(words_to_numbers(["two", "hundred", "fifty"]), ["250"])
        self.assertEqual(words_to_numbers(["one", "thousand", "five", "hundred"]), ["1500"])

    def test_tomorrow(self):
        d, _ = extract_date("book mariama tomorrow", today=date(2026, 10, 1))
        self.assertEqual(d, "2026-10-02")

    def test_next_weekday(self):
        d, _ = extract_date("see you on monday", today=date(2026, 10, 1))  # 1 Oct 2026 is a Thursday
        self.assertEqual(d, "2026-10-05")

    def test_empty_text(self):
        self.assertIsNone(parse("", PRODUCTS)["intent"])


if __name__ == "__main__":
    unittest.main()
