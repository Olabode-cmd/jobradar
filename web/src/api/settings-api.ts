import { parseLlmTest, parseSettings } from '../lib/parse-settings';
import type { LlmTestResult, Settings, SettingsChanges } from '../types/settings';
import { toApiError } from './api-error';
import { http } from './http-client';

export async function fetchSettings(): Promise<Settings> {
  try {
    const response = await http.get<unknown>('/settings');
    return parseSettings(response.parsedBody);
  } catch (error) {
    throw toApiError(error);
  }
}

// `apiKey` is only sent when provided: leaving it out keeps the saved key, "" removes it.
export async function saveSettings(changes: SettingsChanges): Promise<Settings> {
  try {
    const response = await http.put<unknown>('/settings', {
      api_key: changes.apiKey,
      provider: changes.provider,
      model: changes.model,
      base_url: changes.baseUrl,
    });
    return parseSettings(response.parsedBody);
  } catch (error) {
    throw toApiError(error);
  }
}

// The test makes a real request to the provider, so allow it time and never retry.
export async function testLlm(): Promise<LlmTestResult> {
  try {
    const response = await http.post<unknown>('/settings/test-llm', undefined, {
      timeout: 75_000,
      retries: 0,
    });
    return parseLlmTest(response.parsedBody);
  } catch (error) {
    throw toApiError(error);
  }
}
