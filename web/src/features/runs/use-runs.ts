import { useCallback, useEffect, useRef, useState } from 'react';

import { toApiError, type ApiError } from '../../api/api-error';
import { fetchCurrentRun, fetchRunHistory, startRun } from '../../api/runs-api';
import type { RunHistoryItem, RunProgress } from '../../types/run';

const POLL_INTERVAL_MS = 1000;

export function useRuns() {
  const [progress, setProgress] = useState<RunProgress | null>(null);
  const [history, setHistory] = useState<RunHistoryItem[]>([]);
  const [error, setError] = useState<ApiError | null>(null);
  const [starting, setStarting] = useState(false);
  const wasRunning = useRef(false);
  const running = progress?.state === 'running';

  const refreshProgress = useCallback(async () => {
    try {
      setProgress(await fetchCurrentRun());
    } catch (failure) {
      setError(toApiError(failure));
    }
  }, []);

  const refreshHistory = useCallback(async () => {
    try {
      setHistory(await fetchRunHistory());
    } catch (failure) {
      setError(toApiError(failure));
    }
  }, []);

  useEffect(() => {
    void refreshProgress();
    void refreshHistory();
  }, [refreshProgress, refreshHistory]);

  useEffect(() => {
    if (!running) return;
    const timer = window.setInterval(() => void refreshProgress(), POLL_INTERVAL_MS);
    return () => window.clearInterval(timer);
  }, [running, refreshProgress]);

  useEffect(() => {
    if (wasRunning.current && !running) void refreshHistory();
    wasRunning.current = running;
  }, [running, refreshHistory]);

  const start = useCallback(
    async (options: { sources?: string[]; dryRun?: boolean }) => {
      setStarting(true);
      setError(null);
      try {
        await startRun(options);
        await refreshProgress();
      } catch (failure) {
        setError(toApiError(failure));
      } finally {
        setStarting(false);
      }
    },
    [refreshProgress],
  );

  return { progress, history, error, starting, running, start };
}
