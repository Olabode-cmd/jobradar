import unittest

from app.domain.text import fix_mojibake, html_to_text


class HtmlToTextTests(unittest.TestCase):
    def test_blocks_become_lines_and_scripts_are_dropped(self):
        html = "<p>Build <b>things</b></p><script>alert(1)</script><ul><li>React</li><li>Node</li></ul>"
        self.assertEqual(html_to_text(html), "Build things\n\n- React\n- Node")

    def test_plain_text_passes_through(self):
        self.assertEqual(html_to_text("  Hello   world "), "Hello world")

    def test_empty_is_none(self):
        self.assertIsNone(html_to_text(""))
        self.assertIsNone(html_to_text(None))


class FixMojibakeTests(unittest.TestCase):
    def test_repairs_double_encoded_text(self):
        broken = "We\u00e2\u0080\u0099re hiring \u00e2\u0080\u0094 apply"
        self.assertEqual(fix_mojibake(broken), "We\u2019re hiring \u2014 apply")

    def test_leaves_clean_and_unfixable_text_alone(self):
        self.assertEqual(fix_mojibake("Caf\u00e9 \u2014 ok"), "Caf\u00e9 \u2014 ok")
        mixed = "\u00e2\u0080\u0094 and \u2014"
        self.assertEqual(fix_mojibake(mixed), mixed)


if __name__ == "__main__":
    unittest.main()
