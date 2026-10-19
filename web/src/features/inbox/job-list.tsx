import { Loading03Icon } from '@hugeicons/core-free-icons';
import { HugeiconsIcon } from '@hugeicons/react';
import type { ReactNode } from 'react';

import type { ApiError } from '../../api/api-error';
import { Banner } from '../../components/ui/banner';
import { Button } from '../../components/ui/button';
import { EmptyState } from '../../components/ui/empty-state';
import type { JobSummary } from '../../types/job';
import { JobRow } from './job-row';
import { PaginationBar } from './pagination-bar';

interface JobListProps {
  items: JobSummary[];
  total: number;
  status: 'loading' | 'ready' | 'error';
  error: ApiError | null;
  activeId: number | null;
  checkedIds: ReadonlySet<number>;
  page: number;
  pageSize: number;
  emptyTitle: string;
  emptyHint: ReactNode;
  onSelect: (id: number) => void;
  onToggleChecked: (id: number) => void;
  onPageChange: (page: number) => void;
  onRetry: () => void;
}

export function JobList(props: JobListProps) {
  const { items, status } = props;

  if (status === 'error' && items.length === 0) {
    return (
      <Banner
        tone="error"
        title="Couldn't load jobs"
        action={
          <Button variant="ghost" onClick={props.onRetry} className="h-9 px-4">
            Try again
          </Button>
        }
      >
        {props.error?.message}
      </Banner>
    );
  }

  if (status === 'loading' && items.length === 0) {
    return (
      <p role="status" className="flex items-center gap-3 py-10 text-muted">
        <HugeiconsIcon
          icon={Loading03Icon}
          size={20}
          strokeWidth={2.2}
          className="text-accent motion-safe:animate-spin"
        />
        Loading jobs…
      </p>
    );
  }

  if (items.length === 0) {
    return <EmptyState title={props.emptyTitle}>{props.emptyHint}</EmptyState>;
  }

  return (
    <div>
      {status === 'error' ? (
        <div className="mb-4">
          <Banner
            tone="error"
            title="Couldn't load that page"
            action={
              <Button variant="ghost" onClick={props.onRetry} className="h-9 px-4">
                Try again
              </Button>
            }
          >
            {props.error?.message}
          </Banner>
        </div>
      ) : null}
      <ul className="overflow-hidden rounded-xl border border-border border-b-0 bg-surface">
        {items.map((job) => (
          <JobRow
            key={job.id}
            job={job}
            active={job.id === props.activeId}
            checked={props.checkedIds.has(job.id)}
            onSelect={() => props.onSelect(job.id)}
            onToggleChecked={() => props.onToggleChecked(job.id)}
          />
        ))}
      </ul>
      <PaginationBar
        page={props.page}
        pageSize={props.pageSize}
        total={props.total}
        shown={items.length}
        busy={status === 'loading'}
        onPageChange={props.onPageChange}
      />
    </div>
  );
}
