import { cn } from '../../lib/class-names';
import { JOB_STATUSES, type JobStatus, type StatusCounts } from '../../types/job';

export const STATUS_LABELS: Record<JobStatus, string> = {
  new: 'New',
  saved: 'Saved',
  applied: 'Applied',
  interviewing: 'Interviewing',
  rejected: 'Rejected',
  ignored: 'Ignored',
};

interface StatusTabsProps {
  value: JobStatus;
  counts: StatusCounts | null;
  onChange: (status: JobStatus) => void;
}

export function StatusTabs({ value, counts, onChange }: StatusTabsProps) {
  return (
    <div
      role="tablist"
      aria-label="Job status"
      className="flex flex-wrap gap-x-6 border-b border-border"
    >
      {JOB_STATUSES.map((status) => {
        const active = status === value;
        return (
          <button
            key={status}
            role="tab"
            type="button"
            aria-selected={active}
            onClick={() => onChange(status)}
            className={cn(
              '-mb-px flex items-center gap-2 border-b-2 pb-3 text-sm font-bold transition-colors',
              active ? 'border-accent text-body' : 'border-transparent text-muted hover:text-body',
            )}
          >
            {STATUS_LABELS[status]}
            {counts ? (
              <span className={cn('tabular-nums', active ? 'text-success' : 'text-muted')}>
                {counts[status]}
              </span>
            ) : null}
          </button>
        );
      })}
    </div>
  );
}
