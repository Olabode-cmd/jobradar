import { useEffect, useMemo, useState } from 'react';

import { toApiError } from '../../api/api-error';
import { bulkUpdateJobs, ignoreCompany, updateJob } from '../../api/jobs-api';
import { Banner } from '../../components/ui/banner';
import { useDebouncedValue } from '../../hooks/use-debounced-value';
import type { JobSort, JobStatus } from '../../types/job';
import { BulkBar } from './bulk-bar';
import { InboxFilterBar } from './inbox-filter-bar';
import { JobDetailPanel } from './job-detail-panel';
import { JobList } from './job-list';
import { STATUS_LABELS, StatusTabs } from './status-tabs';
import { useInboxShortcuts } from './use-inbox-shortcuts';
import { useJobDetail } from './use-job-detail';
import { useJobsList, type InboxFilters } from './use-jobs-list';

const SEARCH_DEBOUNCE_MS = 250;

export function InboxPage() {
  const [status, setStatus] = useState<JobStatus>('new');
  const [searchText, setSearchText] = useState('');
  const [remoteOnly, setRemoteOnly] = useState(false);
  const [includeRestricted, setIncludeRestricted] = useState(false);
  const [sort, setSort] = useState<JobSort>('score');
  const query = useDebouncedValue(searchText.trim(), SEARCH_DEBOUNCE_MS);

  const filters = useMemo<InboxFilters>(
    () => ({ status, includeRestricted, query, remoteOnly, sort }),
    [status, includeRestricted, query, remoteOnly, sort],
  );
  const list = useJobsList(filters);
  const { items } = list;

  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [checkedIds, setCheckedIds] = useState<ReadonlySet<number>>(new Set());
  const [actionError, setActionError] = useState<string | null>(null);

  const activeId = items.some((job) => job.id === selectedId) ? selectedId : (items[0]?.id ?? null);
  const activeJob = items.find((job) => job.id === activeId) ?? null;
  const { detail, loading, error: detailError } = useJobDetail(activeId);

  useEffect(() => {
    document.querySelector('[aria-current="true"]')?.scrollIntoView({ block: 'nearest' });
  }, [activeId]);

  const changeStatusTab = (next: JobStatus) => {
    setStatus(next);
    setSelectedId(null);
    setCheckedIds(new Set());
  };

  const triage = async (ids: number[], to: JobStatus) => {
    const targets = items.filter((job) => ids.includes(job.id) && job.status !== to);
    if (targets.length === 0) return;
    const targetIds = targets.map((job) => job.id);

    setActionError(null);
    if (activeId !== null && targetIds.includes(activeId) && to !== status) {
      const index = items.findIndex((job) => job.id === activeId);
      const remaining = (job: { id: number }) => !targetIds.includes(job.id);
      const next =
        items.slice(index + 1).find(remaining) ?? items.slice(0, index).reverse().find(remaining);
      setSelectedId(next?.id ?? null);
    }
    list.applyStatusChange(targetIds, to);
    setCheckedIds((current) => new Set([...current].filter((id) => !targetIds.includes(id))));

    try {
      if (targetIds.length === 1) await updateJob(targetIds[0]!, { status: to });
      else await bulkUpdateJobs(targetIds, to);
    } catch (failure) {
      setActionError(toApiError(failure).message);
      list.reload();
    }
  };

  const handleIgnoreCompany = async () => {
    if (!detail) return;
    setActionError(null);
    try {
      await ignoreCompany(detail.id);
    } catch (failure) {
      setActionError(toApiError(failure).message);
    }
    list.reload();
  };

  const handleSaveNotes = async (jobId: number, notes: string) => {
    try {
      await updateJob(jobId, { notes });
    } catch (failure) {
      setActionError(toApiError(failure).message);
    }
  };

  const toggleChecked = (id: number) =>
    setCheckedIds((current) => {
      const next = new Set(current);
      if (!next.delete(id)) next.add(id);
      return next;
    });

  useInboxShortcuts({
    onMove: (delta) => {
      if (items.length === 0) return;
      const index = items.findIndex((job) => job.id === activeId);
      const target = items[Math.min(items.length - 1, Math.max(0, index + delta))];
      if (target) setSelectedId(target.id);
    },
    onStatus: (next) => {
      if (activeId !== null) void triage([activeId], next);
    },
    onOpenApply: () => {
      if (activeJob?.applyUrl) window.open(activeJob.applyUrl, '_blank', 'noopener,noreferrer');
    },
  });

  const emptyTitle =
    status === 'new' ? 'Nothing new to triage' : `No ${STATUS_LABELS[status].toLowerCase()} jobs`;
  const emptyHint =
    status === 'new' || query || remoteOnly
      ? 'Change the filters, or run a fetch to pull the latest postings.'
      : 'Jobs you move here will show up in this list.';

  return (
    <div>
      <h1 className="text-4xl font-extrabold tracking-tight">Inbox</h1>
      <p className="mt-2 mb-8 max-w-2xl text-forest-300">
        Jobs you haven't triaged, best fit first. Use J and K to move, O to open the apply page, and
        S, A or I to save, mark applied or ignore.
      </p>

      <div className="space-y-4">
        <StatusTabs value={status} counts={list.counts} onChange={changeStatusTab} />
        <InboxFilterBar
          searchText={searchText}
          onSearchText={setSearchText}
          remoteOnly={remoteOnly}
          onRemoteOnly={setRemoteOnly}
          includeRestricted={includeRestricted}
          onIncludeRestricted={setIncludeRestricted}
          sort={sort}
          onSort={setSort}
        />
        {checkedIds.size > 0 ? (
          <BulkBar
            count={checkedIds.size}
            onStatus={(next) => void triage([...checkedIds], next)}
            onClear={() => setCheckedIds(new Set())}
          />
        ) : null}
        {actionError ? (
          <Banner tone="error" title="That change didn't save">
            {actionError}
          </Banner>
        ) : null}
      </div>

      <div className="mt-6 grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_28rem]">
        <JobList
          items={items}
          total={list.total}
          status={list.status}
          error={list.error}
          activeId={activeId}
          checkedIds={checkedIds}
          loadingMore={list.loadingMore}
          emptyTitle={emptyTitle}
          emptyHint={emptyHint}
          onSelect={setSelectedId}
          onToggleChecked={toggleChecked}
          onLoadMore={() => void list.loadMore()}
          onRetry={list.reload}
        />
        <JobDetailPanel
          detail={detail}
          loading={loading}
          error={detailError}
          onStatus={(next) => detail && void triage([detail.id], next)}
          onIgnoreCompany={() => void handleIgnoreCompany()}
          onSaveNotes={(notes) => detail && void handleSaveNotes(detail.id, notes)}
        />
      </div>
    </div>
  );
}
