export type LlmProvider = '' | 'anthropic' | 'openai-compatible';

export interface Settings {
  envFileExists: boolean;
  apiKeySet: boolean;
  apiKeyHint: string | null;
  provider: LlmProvider;
  detectedProvider: string | null;
  model: string;
  baseUrl: string;
  llmEnabled: boolean;
}

export interface SettingsChanges {
  apiKey?: string;
  provider: LlmProvider;
  model: string;
  baseUrl: string;
}

export type LlmTestResult =
  | { ok: true; provider: string; model: string | null; reply: string; durationMs: number }
  | { ok: false; provider: string | null; kind: string; message: string };
