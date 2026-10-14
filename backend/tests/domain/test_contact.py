import unittest

from app.domain.contact import detect_apply_method, extract_emails, is_generic_inbox


class ExtractEmailsTests(unittest.TestCase):
    def test_finds_plain_and_mailto_addresses_once_each(self):
        html = '<a href="mailto:Jobs@Acme.com">Jobs@acme.com</a> or jane.doe@acme.co.uk.'
        self.assertEqual(extract_emails(html), ["jobs@acme.com", "jane.doe@acme.co.uk"])

    def test_ignores_noreply_and_image_names(self):
        self.assertEqual(extract_emails("noreply@acme.com logo@2x.png hello@acme.com"), ["hello@acme.com"])

    def test_empty_and_none(self):
        self.assertEqual(extract_emails(None), [])
        self.assertEqual(extract_emails("no addresses here"), [])

    def test_caps_the_list(self):
        text = " ".join(f"p{n}@acme.com" for n in range(20))
        self.assertEqual(len(extract_emails(text)), 5)


class GenericInboxTests(unittest.TestCase):
    def test_generic_versus_personal(self):
        self.assertTrue(is_generic_inbox("careers@acme.com"))
        self.assertFalse(is_generic_inbox("jane.doe@acme.com"))


class ApplyMethodTests(unittest.TestCase):
    def test_known_ats_hosts(self):
        self.assertEqual(detect_apply_method("https://boards.greenhouse.io/acme/jobs/1", []), "ats")
        self.assertEqual(detect_apply_method("https://acme.bamboohr.com/careers/8", []), "ats")

    def test_other_pages_are_forms(self):
        self.assertEqual(detect_apply_method("https://acme.com/careers/apply", []), "form")

    def test_lookalike_host_is_not_an_ats(self):
        self.assertEqual(detect_apply_method("https://evil-greenhouse.io/x", []), "form")

    def test_email_when_no_link_or_mailto(self):
        self.assertEqual(detect_apply_method(None, ["jobs@acme.com"]), "email")
        self.assertEqual(detect_apply_method("mailto:jobs@acme.com", []), "email")
        self.assertIsNone(detect_apply_method("", []))


if __name__ == "__main__":
    unittest.main()
