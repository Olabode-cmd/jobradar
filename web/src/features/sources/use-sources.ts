import { useCallback, useEffect, useState } from 'react';

import { toApiError, type ApiError } from '../../api/api-error';
import { fetchSources, setSourceEnabled, testSource } from '../../api/sources-api';
import type { Source, SourceTestResult } from '../../types/source';

export type TestState =
  | { status: 'running' }
  | { status: 'done'; result: SourceTestResult }
  | { status: 'failed'; message: string };

export function useSources() {
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [tests, setTests] = useState<Record<string, TestState>>({});
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetchSources().then(
      (items) => {
        if (cancelled) return;
        setSources(items);
        setError(null);
        setLoading(false);
      },
      (failure: unknown) => {
        if (cancelled) return;
        setError(toApiError(failure));
        setLoading(false);
      },
    );
    return () => {
      cancelled = true;
    };
  }, [attempt]);

  const reload = useCallback(() => setAttempt((count) => count + 1), []);

  const toggle = useCallback(async (id: string, enabled: boolean) => {
    setActionError(null);
    setSources((current) =>
      current.map((source) => (source.id === id ? { ...source, enabled } : source)),
    );
    try {
      const updated = await setSourceEnabled(id, enabled);
      setSources((current) => current.map((source) => (source.id === id ? updated : source)));
    } catch (failure) {
      setActionError(toApiError(failure).message);
      setSources((current) =>
        current.map((source) => (source.id === id ? { ...source, enabled: !enabled } : source)),
      );
    }
  }, []);

  const runTest = useCallback(async (id: string) => {
    setTests((current) => ({ ...current, [id]: { status: 'running' } }));
    try {
      const result = await testSource(id);
      setTests((current) => ({ ...current, [id]: { status: 'done', result } }));
    } catch (failure) {
      setTests((current) => ({
        ...current,
        [id]: { status: 'failed', message: toApiError(failure).message },
      }));
    }
  }, []);

  const dismissTest = useCallback(
    (id: string) =>
      setTests((current) => {
        const next = { ...current };
        delete next[id];
        return next;
      }),
    [],
  );

  return { sources, loading, error, actionError, tests, reload, toggle, runTest, dismissTest };
}
