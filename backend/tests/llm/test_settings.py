import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from app.config import env_file, paths
from app.llm import load_llm_settings


class LlmSettingsTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.env_path = Path(tmp.name) / ".env"
        patcher = mock.patch.object(paths, "ENV_PATH", self.env_path)
        patcher.start()
        self.addCleanup(patcher.stop)
        environ = mock.patch.dict(os.environ, {}, clear=False)
        environ.start()
        self.addCleanup(environ.stop)
        for key in env_file.LLM_KEYS:
            os.environ.pop(key, None)

    def test_disabled_without_a_key(self):
        self.assertFalse(load_llm_settings().enabled)

    def test_provider_is_detected_from_the_key_prefix(self):
        self.env_path.write_text("API_KEY=sk-ant-abc\n", encoding="utf-8")
        self.assertEqual(load_llm_settings().provider, "anthropic")
        self.env_path.write_text("API_KEY=sk-abc\n", encoding="utf-8")
        self.assertEqual(load_llm_settings().provider, "openai-compatible")

    def test_explicit_provider_overrides_detection(self):
        self.env_path.write_text("API_KEY=sk-ant-abc\nLLM_PROVIDER=openai-compatible\n", encoding="utf-8")
        self.assertEqual(load_llm_settings().provider, "openai-compatible")

    def test_hand_editing_env_applies_without_a_restart(self):
        self.env_path.write_text("API_KEY=\n", encoding="utf-8")
        os.environ["API_KEY"] = ""  # what an empty line loaded at startup leaves behind
        self.assertFalse(load_llm_settings().enabled)
        self.env_path.write_text("API_KEY=sk-new-key\nLLM_MODEL=my-model\n", encoding="utf-8")
        settings = load_llm_settings()
        self.assertEqual((settings.enabled, settings.api_key, settings.model), (True, "sk-new-key", "my-model"))

    def test_empty_env_line_does_not_hide_a_shell_variable(self):
        os.environ["API_KEY"] = "sk-from-shell"
        self.env_path.write_text("API_KEY=\n", encoding="utf-8")
        self.assertEqual(load_llm_settings().api_key, "sk-from-shell")

    def test_nonempty_env_value_beats_the_shell(self):
        os.environ["API_KEY"] = "sk-from-shell"
        self.env_path.write_text("API_KEY=sk-from-file\n", encoding="utf-8")
        self.assertEqual(load_llm_settings().api_key, "sk-from-file")

    def test_base_url_and_model_are_passed_through(self):
        self.env_path.write_text("API_KEY=k\nLLM_BASE_URL=http://localhost:11434/v1\nLLM_MODEL=llama3\n", encoding="utf-8")
        settings = load_llm_settings()
        self.assertEqual((settings.base_url, settings.model), ("http://localhost:11434/v1", "llama3"))


if __name__ == "__main__":
    unittest.main()
