import unittest

from app.llm import LlmError, LlmSettings, create_client
from app.llm.anthropic import AnthropicClient
from app.llm.openai_compatible import OpenAICompatibleClient
from tests.llm.fake_provider import FakeProvider

SECRET = "sk-test-SECRET-value-1234"


def anthropic_ok(text="OK"):
    return (200, {"model": "claude-test", "content": [{"type": "text", "text": text}]})


def openai_ok(text="OK"):
    return (200, {"model": "gpt-test", "choices": [{"message": {"content": text}}]})


class AnthropicAdapterTests(unittest.TestCase):
    def client(self, provider, **overrides):
        settings = LlmSettings(enabled=True, provider="anthropic", api_key=SECRET, base_url=provider.url, **overrides)
        return create_client(settings)

    def test_sends_the_messages_api_request_and_reads_the_reply(self):
        fake = FakeProvider({"/v1/messages": anthropic_ok("hello")})
        self.addCleanup(fake.close)
        reply = self.client(fake, model="claude-x").complete("be brief", "ping", max_tokens=7)

        request = fake.requests[0]
        self.assertEqual(request["headers"]["x-api-key"], SECRET)
        self.assertEqual(request["headers"]["anthropic-version"], "2023-06-01")
        self.assertEqual(request["body"], {"model": "claude-x", "max_tokens": 7, "system": "be brief",
                                           "messages": [{"role": "user", "content": "ping"}]})
        self.assertEqual((reply.text, reply.model), ("hello", "claude-test"))

    def test_picked_for_sk_ant_keys(self):
        self.assertIsInstance(create_client(LlmSettings(enabled=True, provider="anthropic", api_key="sk-ant-x")), AnthropicClient)

    def test_error_statuses_map_to_kinds_and_never_leak_the_key(self):
        cases = {401: "auth", 404: "not_found", 429: "rate_limit", 400: "bad_request", 500: "server"}
        for status, kind in cases.items():
            with self.subTest(status=status):
                fake = FakeProvider({"/v1/messages": (status, {"error": {"message": "nope"}})})
                self.addCleanup(fake.close)
                with self.assertRaises(LlmError) as raised:
                    self.client(fake).complete("s", "p")
                self.assertEqual(raised.exception.kind, kind)
                self.assertNotIn(SECRET, str(raised.exception))
                self.assertIn("nope", str(raised.exception))

    def test_unexpected_shape(self):
        fake = FakeProvider({"/v1/messages": (200, {"unexpected": True})})
        self.addCleanup(fake.close)
        with self.assertRaises(LlmError) as raised:
            self.client(fake).complete("s", "p")
        self.assertEqual(raised.exception.kind, "unexpected")


class OpenAICompatibleAdapterTests(unittest.TestCase):
    def client(self, provider, **overrides):
        settings = LlmSettings(enabled=True, provider="openai-compatible", api_key=SECRET, base_url=f"{provider.url}/v1", **overrides)
        return create_client(settings)

    def test_sends_the_chat_completions_request_and_reads_the_reply(self):
        fake = FakeProvider({"/v1/chat/completions": openai_ok("hi there")})
        self.addCleanup(fake.close)
        reply = self.client(fake, model="llama3").complete("be brief", "ping", max_tokens=9)

        request = fake.requests[0]
        self.assertEqual(request["headers"]["Authorization"], f"Bearer {SECRET}")
        self.assertEqual(request["body"]["model"], "llama3")
        self.assertEqual(request["body"]["messages"], [{"role": "system", "content": "be brief"}, {"role": "user", "content": "ping"}])
        self.assertEqual(reply.text, "hi there")

    def test_trailing_slash_in_base_url_is_tolerated(self):
        fake = FakeProvider({"/v1/chat/completions": openai_ok()})
        self.addCleanup(fake.close)
        settings = LlmSettings(enabled=True, provider="openai-compatible", api_key="k", base_url=f"{fake.url}/v1/")
        create_client(settings).complete("s", "p")
        self.assertEqual(fake.requests[0]["path"], "/v1/chat/completions")

    def test_error_statuses_map_to_kinds_and_never_leak_the_key(self):
        for status, kind in {401: "auth", 404: "not_found", 429: "rate_limit", 503: "server"}.items():
            with self.subTest(status=status):
                fake = FakeProvider({"/v1/chat/completions": (status, {"error": {"message": "denied"}})})
                self.addCleanup(fake.close)
                with self.assertRaises(LlmError) as raised:
                    self.client(fake).complete("s", "p")
                self.assertEqual(raised.exception.kind, kind)
                self.assertNotIn(SECRET, str(raised.exception))

    def test_unreachable_server_is_a_network_error(self):
        settings = LlmSettings(enabled=True, provider="openai-compatible", api_key="k", base_url="http://127.0.0.1:9/v1")
        with self.assertRaises(LlmError) as raised:
            create_client(settings).complete("s", "p")
        self.assertEqual(raised.exception.kind, "network")


class FactoryTests(unittest.TestCase):
    def test_disabled_settings_are_not_configured(self):
        with self.assertRaises(LlmError) as raised:
            create_client(LlmSettings(enabled=False))
        self.assertEqual(raised.exception.kind, "not_configured")

    def test_openai_compatible_is_the_default_family(self):
        client = create_client(LlmSettings(enabled=True, provider="openai-compatible", api_key="k"))
        self.assertIsInstance(client, OpenAICompatibleClient)


if __name__ == "__main__":
    unittest.main()
