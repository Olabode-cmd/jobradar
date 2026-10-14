import { useCallback, useEffect, useState } from 'react';

import { fetchConfig, saveConfig } from '../api/config-api';
import { toApiError, type ApiError } from '../api/api-error';
import type { ConfigSnapshot, EditableConfig } from '../types/config';

export type ConfigState =
  | { status: 'loading' }
  | { status: 'error'; error: ApiError }
  | { status: 'ready'; snapshot: ConfigSnapshot };

export function useConfig() {
  const [state, setState] = useState<ConfigState>({ status: 'loading' });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setState({ status: 'loading' });
    fetchConfig().then(
      (snapshot) => !cancelled && setState({ status: 'ready', snapshot }),
      (error: unknown) => !cancelled && setState({ status: 'error', error: toApiError(error) }),
    );
    return () => {
      cancelled = true;
    };
  }, [attempt]);

  const reload = useCallback(() => setAttempt((count) => count + 1), []);
  const save = useCallback((update: EditableConfig) => saveConfig(update), []);

  return { state, reload, save };
}
