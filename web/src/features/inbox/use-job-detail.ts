import { useEffect, useState } from 'react';

import { toApiError, type ApiError } from '../../api/api-error';
import { fetchJob } from '../../api/jobs-api';
import type { JobDetail } from '../../types/job';

export function useJobDetail(jobId: number | null) {
  const [detail, setDetail] = useState<JobDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  useEffect(() => {
    if (jobId === null) {
      setDetail(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetchJob(jobId).then(
      (job) => {
        if (cancelled) return;
        setDetail(job);
        setLoading(false);
      },
      (failure: unknown) => {
        if (cancelled) return;
        setDetail(null);
        setError(toApiError(failure));
        setLoading(false);
      },
    );
    return () => {
      cancelled = true;
    };
  }, [jobId]);

  return { detail, loading, error, replaceDetail: setDetail };
}
