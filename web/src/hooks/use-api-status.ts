import { useEffect, useState } from 'react';

import { fetchHealth } from '../api/health-api';

export type ApiStatus = 'checking' | 'online' | 'degraded' | 'offline';

const POLL_INTERVAL_MS = 15_000;

export function useApiStatus(): ApiStatus {
  const [status, setStatus] = useState<ApiStatus>('checking');

  useEffect(() => {
    let cancelled = false;

    const check = () => {
      fetchHealth().then(
        (health) => !cancelled && setStatus(health.databaseOk ? 'online' : 'degraded'),
        () => !cancelled && setStatus('offline'),
      );
    };

    check();
    const timer = window.setInterval(check, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, []);

  return status;
}
