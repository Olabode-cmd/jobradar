import { useCallback, useEffect, useState } from 'react';

import { toApiError, type ApiError } from '../../api/api-error';
import { fetchSettings, saveSettings, testLlm } from '../../api/settings-api';
import type { LlmProvider, LlmTestResult, Settings } from '../../types/settings';

export interface SettingsDraft {
  apiKey: string;
  provider: LlmProvider;
  model: string;
  baseUrl: string;
}

export type TestState =
  | { status: 'idle' }
  | { status: 'running' }
  | { status: 'done'; result: LlmTestResult }
  | { status: 'failed'; message: string };

function toDraft(settings: Settings): SettingsDraft {
  return {
    apiKey: '',
    provider: settings.provider,
    model: settings.model,
    baseUrl: settings.baseUrl,
  };
}

export function useSettings() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [draft, setDraft] = useState<SettingsDraft | null>(null);
  const [loadError, setLoadError] = useState<ApiError | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [justSaved, setJustSaved] = useState(false);
  const [test, setTest] = useState<TestState>({ status: 'idle' });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let cancelled = false;
    fetchSettings().then(
      (loaded) => {
        if (cancelled) return;
        setSettings(loaded);
        setDraft(toDraft(loaded));
        setLoadError(null);
      },
      (failure: unknown) => {
        if (!cancelled) setLoadError(toApiError(failure));
      },
    );
    return () => {
      cancelled = true;
    };
  }, [attempt]);

  const reload = useCallback(() => setAttempt((count) => count + 1), []);

  const setField = useCallback(<K extends keyof SettingsDraft>(key: K, value: SettingsDraft[K]) => {
    setDraft((current) => (current ? { ...current, [key]: value } : current));
    setJustSaved(false);
    setSaveError(null);
  }, []);

  const dirty =
    settings !== null &&
    draft !== null &&
    (draft.apiKey.trim() !== '' ||
      draft.provider !== settings.provider ||
      draft.model.trim() !== settings.model ||
      draft.baseUrl.trim() !== settings.baseUrl);

  const persist = useCallback(
    async (apiKey: string | undefined) => {
      if (!draft) return;
      setSaving(true);
      setSaveError(null);
      setTest({ status: 'idle' });
      try {
        const saved = await saveSettings({
          ...(apiKey !== undefined ? { apiKey } : {}),
          provider: draft.provider,
          model: draft.model.trim(),
          baseUrl: draft.baseUrl.trim(),
        });
        setSettings(saved);
        setDraft(toDraft(saved));
        setJustSaved(true);
      } catch (failure) {
        setSaveError(toApiError(failure).message);
      } finally {
        setSaving(false);
      }
    },
    [draft],
  );

  const save = useCallback(
    () => persist(draft && draft.apiKey.trim() ? draft.apiKey.trim() : undefined),
    [draft, persist],
  );
  const removeKey = useCallback(() => persist(''), [persist]);

  const runTest = useCallback(async () => {
    setTest({ status: 'running' });
    try {
      setTest({ status: 'done', result: await testLlm() });
    } catch (failure) {
      setTest({ status: 'failed', message: toApiError(failure).message });
    }
  }, []);

  return {
    settings,
    draft,
    loadError,
    reload,
    setField,
    dirty,
    saving,
    saveError,
    justSaved,
    save,
    removeKey,
    test,
    runTest,
  };
}
