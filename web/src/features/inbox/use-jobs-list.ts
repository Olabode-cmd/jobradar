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
  const [loadingMore, setLoadingMore] = useState(false);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setStatus('loading');
    fetchJobs({ ...filters, limit: PAGE_SIZE, offset: 0 }).then(
      (page) => {
        if (cancelled) return;
        setItems(page.items);
        setTotal(page.total);
        setCounts(page.counts);
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
  }, [filters, reloadToken]);

  const reload = useCallback(() => setReloadToken((token) => token + 1), []);

  const loadMore = useCallback(async () => {
    setLoadingMore(true);
    try {
      const page = await fetchJobs({ ...filters, limit: PAGE_SIZE, offset: items.length });
      setItems((current) => {
        const known = new Set(current.map((job) => job.id));
        return [...current, ...page.items.filter((job) => !known.has(job.id))];
      });
      setTotal(page.total);
      setCounts(page.counts);
    } catch (failure) {
      setError(toApiError(failure));
    } finally {
      setLoadingMore(false);
    }
  }, [filters, items.length]);

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

  return { items, total, counts, status, error, loadingMore, reload, loadMore, applyStatusChange };
}
