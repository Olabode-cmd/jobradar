import { useId } from 'react';

import { Banner } from '../../components/ui/banner';
import { Button } from '../../components/ui/button';
import { SectionPanel } from '../../components/ui/section-panel';
import { TextField } from '../../components/ui/text-field';
import type { LlmProvider } from '../../types/settings';
import { LlmTestPanel } from './llm-test-panel';
import { useSettings } from './use-settings';

const PROVIDER_OPTIONS: Array<{ value: LlmProvider; label: string }> = [
  { value: '', label: 'Detect from the key' },
  { value: 'anthropic', label: 'Anthropic' },
  { value: 'openai-compatible', label: 'OpenAI-compatible (OpenAI, OpenRouter, Groq, Ollama…)' },
];

export function SettingsPage() {
  const s = useSettings();
  const providerId = useId();

  return (
    <div>
      <h1 className="text-4xl font-extrabold tracking-tight">Settings</h1>
      <p className="mt-2 mb-10 max-w-2xl text-forest-300">
        JobRadar works without any key. Add one to let an AI model double-check postings and explain
        its fit score. It reads job descriptions only, never your CV, and checks at most 50 jobs per
        run.
      </p>

      {s.loadError ? (
        <Banner
          tone="error"
          title="Couldn't load settings"
          action={
            <Button variant="ghost" onClick={s.reload} className="h-9 px-4">
              Try again
            </Button>
          }
        >
          {s.loadError.message}
        </Banner>
      ) : null}

      {s.settings && s.draft ? (
        <div className="max-w-3xl space-y-6">
          <SectionPanel
            title="AI model"
            description="The key is saved to the .env file in your project folder and is never shown here in full."
          >
            <TextField
              label="API key"
              type="password"
              autoComplete="new-password"
              value={s.draft.apiKey}
              onChange={(value) => s.setField('apiKey', value)}
              placeholder={s.settings.apiKeySet ? `Saved: ${s.settings.apiKeyHint}` : 'sk-…'}
              hint={
                s.settings.apiKeySet
                  ? 'A key is saved. Type a new one to replace it, or leave this empty to keep it.'
                  : 'Keys starting with sk-ant- are treated as Anthropic. Anything else as OpenAI-compatible.'
              }
            />

            <div>
              <label htmlFor={providerId} className="mb-2 block text-sm font-bold">
                Provider
              </label>
              <select
                id={providerId}
                value={s.draft.provider}
                onChange={(event) => s.setField('provider', event.target.value as LlmProvider)}
                className="h-11 w-full rounded-lg border border-forest-700 bg-forest-800 px-3 text-base font-medium outline-none hover:border-forest-600 focus:border-lemon-400"
              >
                {PROVIDER_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              {s.settings.detectedProvider ? (
                <p className="mt-2 text-sm text-forest-300">
                  Currently using: {s.settings.detectedProvider}
                </p>
              ) : null}
            </div>

            <TextField
              label="Model"
              value={s.draft.model}
              onChange={(value) => s.setField('model', value)}
              placeholder="Leave empty for the provider's default"
              hint="Use this if your provider doesn't offer the default model."
              autoComplete="off"
            />
            <TextField
              label="Base URL"
              value={s.draft.baseUrl}
              onChange={(value) => s.setField('baseUrl', value)}
              placeholder="https://openrouter.ai/api/v1"
              hint="Only for OpenRouter, Groq, Ollama or another compatible service. Leave empty for OpenAI or Anthropic."
              autoComplete="off"
            />
          </SectionPanel>

          {s.saveError ? (
            <Banner tone="error" title="Couldn't save settings">
              {s.saveError}
            </Banner>
          ) : null}

          <div className="flex flex-wrap items-center gap-3">
            <Button onClick={() => void s.save()} disabled={!s.dirty || s.saving}>
              {s.saving ? 'Saving…' : 'Save settings'}
            </Button>
            <Button
              variant="ghost"
              onClick={() => void s.runTest()}
              disabled={!s.settings.apiKeySet || s.dirty || s.test.status === 'running'}
            >
              Test connection
            </Button>
            {s.settings.apiKeySet ? (
              <Button
                variant="ghost"
                className="text-danger"
                onClick={() => void s.removeKey()}
                disabled={s.saving}
              >
                Remove key
              </Button>
            ) : null}
            {s.justSaved ? (
              <p role="status" className="text-sm font-bold text-lemon-400">
                Saved to .env
              </p>
            ) : null}
          </div>
          {s.dirty && s.settings.apiKeySet ? (
            <p className="text-sm text-forest-300">
              Save your changes before testing the connection.
            </p>
          ) : null}
          <LlmTestPanel state={s.test} />
        </div>
      ) : null}
    </div>
  );
}
