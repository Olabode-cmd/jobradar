import { useCallback, useEffect, useState } from 'react';

import { toApiError, type ApiError } from '../../api/api-error';
import { fetchJobs } from '../../api/jobs-api';
import type { JobQuery, JobStatus, JobSummary, StatusCounts } from '../../types/job';

export const PAGE_SIZE = 50;

export type InboxFilters = Omit<JobQuery, 'limit' | 'offset'>;

type LoadStatus = 'loading' | 'ready' | 'error';

export function useJobsList(filters: InboxFilters) {
  const [items, setItems] = useState<JobSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [counts, setCounts] = useState<StatusCounts | null>(null);
  const [status, setStatus] = useState<LoadStatus>('loading');
  const [error, setError] = useState<ApiError | null>(null);
  const [reloadToken, setReloadToken] = useState(0);
  // The page is remembered together with the filters it was chosen under, so changing any
  // filter drops back to page 1 without a second fetch.
  const [pageState, setPageState] = useState({ filters, index: 0 });
  const page = pageState.filters === filters ? pageState.index : 0;

  const goToPage = useCallback(
    (index: number) => setPageState({ filters, index: Math.max(0, index) }),
    [filters],
  );

  useEffect(() => {
    let cancelled = false;
    setStatus('loading');
    fetchJobs({ ...filters, limit: PAGE_SIZE, offset: page * PAGE_SIZE }).then(
      (result) => {
        if (cancelled) return;
        // Triaging can empty the last page; step back rather than show an empty list.
        if (result.items.length === 0 && result.total > 0 && page > 0) {
          setPageState({ filters, index: Math.ceil(result.total / PAGE_SIZE) - 1 });
          return;
        }
        setItems(result.items);
        setTotal(result.total);
        setCounts(result.counts);
        setError(null);
        setStatus('ready');
      },
      (failure: unknown) => {
        if (cancelled) return;
        setError(toApiError(failure));
        setStatus('error');
      },
    );
    return () => {
      cancelled = true;
    };
  }, [filters, page, reloadToken]);

  const reload = useCallback(() => setReloadToken((token) => token + 1), []);

  // Mirrors a status change locally so the list responds before the API round trip finishes.
  const applyStatusChange = useCallback(
    (ids: number[], to: JobStatus) => {
      const affected = new Set(ids);
      const moved = items.filter((job) => affected.has(job.id) && job.status !== to);
      const leavesList = filters.status !== 'all' && to !== filters.status;

      setItems((current) =>
        leavesList
          ? current.filter((job) => !affected.has(job.id))
          : current.map((job) => (affected.has(job.id) ? { ...job, status: to } : job)),
      );
      if (leavesList) setTotal((current) => Math.max(0, current - moved.length));
      setCounts((current) => {
        if (!current) return current;
        const next = { ...current };
        for (const job of moved) {
          next[job.status] = Math.max(0, next[job.status] - 1);
          next[to] += 1;
        }
        return next;
      });
    },
    [filters.status, items],
  );

  return { items, total, counts, status, error, page, goToPage, reload, applyStatusChange };
}
