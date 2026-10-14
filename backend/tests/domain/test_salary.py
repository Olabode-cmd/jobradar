import unittest

from app.domain.salary import annual_salary_range


class AnnualSalaryRangeTests(unittest.TestCase):
    def test_k_suffix_range(self):
        self.assertEqual(annual_salary_range("$80K - $120K"), (80_000, 120_000))

    def test_currency_code_with_period(self):
        self.assertEqual(annual_salary_range("USD 213500–390000 yearly"), (213_500, 390_000))

    def test_hourly_is_annualized(self):
        self.assertEqual(annual_salary_range("$50-70 per hour"), (104_000, 145_600))

    def test_euro_summary_with_trailing_text(self):
        self.assertEqual(annual_salary_range("€110K – €185K • Offers Equity"), (110_000, 185_000))

    def test_unsure_inputs_return_none(self):
        for text in [None, "", "Competitive", "5 years experience", "40 hours a week"]:
            with self.subTest(text=text):
                self.assertIsNone(annual_salary_range(text))


if __name__ == "__main__":
    unittest.main()
