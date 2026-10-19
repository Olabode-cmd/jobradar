import { useCallback, useState } from 'react';

import { toApiError } from '../../api/api-error';
import { clearData, type ClearDataResult } from '../../api/data-api';
import { fetchJobs } from '../../api/jobs-api';
import { JOB_STATUSES } from '../../types/job';

interface JobTotals {
  all: number;
  untriaged: number;
}

export function useClearData() {
  const [open, setOpen] = useState(false);
  const [totals, setTotals] = useState<JobTotals | null>(null);
  const [keepTriaged, setKeepTriaged] = useState(true);
  const [clearing, setClearing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ClearDataResult | null>(null);

  const begin = useCallback(async () => {
    setOpen(true);
    setResult(null);
    setError(null);
    setTotals(null);
    try {
      // A one-row page is enough: the response carries the per-status counts.
      const page = await fetchJobs({
        status: 'all',
        includeRestricted: true,
        query: '',
        remoteOnly: false,
        sort: 'score',
        limit: 1,
        offset: 0,
      });
      setTotals({
        all: JOB_STATUSES.reduce((sum, status) => sum + page.counts[status], 0),
        untriaged: page.counts.new,
      });
    } catch (failure) {
      setError(toApiError(failure).message);
    }
  }, []);

  const cancel = useCallback(() => {
    setOpen(false);
    setError(null);
  }, []);

  const confirm = useCallback(async () => {
    setClearing(true);
    setError(null);
    try {
      setResult(await clearData(keepTriaged));
      setOpen(false);
    } catch (failure) {
      setError(toApiError(failure).message);
    } finally {
      setClearing(false);
    }
  }, [keepTriaged]);

  const toDelete = totals ? (keepTriaged ? totals.untriaged : totals.all) : null;

  return {
    open,
    totals,
    toDelete,
    keepTriaged,
    setKeepTriaged,
    clearing,
    error,
    result,
    begin,
    cancel,
    confirm,
  };
}
