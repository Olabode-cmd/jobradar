import { useCallback, useEffect, useState } from 'react';

import { toApiError } from '../../api/api-error';
import { fetchConfig, saveConfig } from '../../api/config-api';
import { startRun } from '../../api/runs-api';
import type { ConfigSnapshot } from '../../types/config';
import { applyAnswers, EMPTY_ANSWERS, type OnboardingAnswers } from './onboarding-answers';

export const STEP_COUNT = 4;

export function useOnboarding() {
  const [base, setBase] = useState<ConfigSnapshot | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [answers, setAnswers] = useState<OnboardingAnswers>(EMPTY_ANSWERS);
  const [step, setStep] = useState(0);
  const [saved, setSaved] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchConfig().then(
      (snapshot) => !cancelled && setBase(snapshot),
      (failure: unknown) => !cancelled && setLoadError(toApiError(failure).message),
    );
    return () => {
      cancelled = true;
    };
  }, []);

  const update = useCallback(
    <K extends keyof OnboardingAnswers>(key: K, value: OnboardingAnswers[K]) =>
      setAnswers((current) => ({ ...current, [key]: value })),
    [],
  );

  const canAdvance = step !== 0 || answers.role.trim().length > 0;
  const next = useCallback(() => setStep((current) => Math.min(STEP_COUNT - 1, current + 1)), []);
  const back = useCallback(() => setStep((current) => Math.max(0, current - 1)), []);

  const finish = useCallback(async () => {
    if (!base) return;
    setBusy(true);
    setError(null);
    try {
      await saveConfig(applyAnswers(base.editable, answers));
      setSaved(true);
    } catch (failure) {
      setError(toApiError(failure).message);
    } finally {
      setBusy(false);
    }
  }, [answers, base]);

  const fetchFirstJobs = useCallback(async (): Promise<boolean> => {
    setBusy(true);
    setError(null);
    try {
      await startRun();
      return true;
    } catch (failure) {
      setError(toApiError(failure).message);
      return false;
    } finally {
      setBusy(false);
    }
  }, []);

  return {
    ready: base !== null,
    loadError,
    answers,
    update,
    step,
    canAdvance,
    next,
    back,
    saved,
    busy,
    error,
    finish,
    fetchFirstJobs,
  };
}
