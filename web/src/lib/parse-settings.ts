import { ApiError } from '../api/api-error';
import type { LlmProvider, LlmTestResult, Settings } from '../types/settings';
import { asNumberOrNull, asString, asStringOrNull, isRecord } from './guards';

function asProvider(value: unknown): LlmProvider {
  return value === 'anthropic' || value === 'openai-compatible' ? value : '';
}

export function parseSettings(body: unknown): Settings {
  if (!isRecord(body)) {
    throw new ApiError('unexpected', 'The API returned settings in an unexpected shape.');
  }
  return {
    envFileExists: body.env_file_exists === true,
    apiKeySet: body.api_key_set === true,
    apiKeyHint: asStringOrNull(body.api_key_hint),
    provider: asProvider(body.provider),
    detectedProvider: asStringOrNull(body.detected_provider),
    model: asString(body.model),
    baseUrl: asString(body.base_url),
    llmEnabled: body.llm_enabled === true,
    dbPath: asString(body.db_path),
    configPath: asString(body.config_path),
  };
}

export function parseLlmTest(body: unknown): LlmTestResult {
  if (!isRecord(body)) {
    throw new ApiError('unexpected', 'The API returned a test result in an unexpected shape.');
  }
  if (body.ok === true) {
    return {
      ok: true,
      provider: asString(body.provider),
      model: asStringOrNull(body.model),
      reply: asString(body.reply),
      durationMs: asNumberOrNull(body.duration_ms) ?? 0,
    };
  }
  return {
    ok: false,
    provider: asStringOrNull(body.provider),
    kind: asString(body.kind, 'unexpected'),
    message: asString(body.message, 'The test failed.'),
  };
}
