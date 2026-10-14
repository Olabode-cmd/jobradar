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
      className="flex flex-wrap gap-x-6 border-b border-forest-700"
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
              active
                ? 'border-lemon-400 text-white'
                : 'border-transparent text-forest-300 hover:text-white',
            )}
          >
            {STATUS_LABELS[status]}
            {counts ? (
              <span className={cn('tabular-nums', active ? 'text-lemon-400' : 'text-forest-300')}>
                {counts[status]}
              </span>
            ) : null}
          </button>
        );
      })}
    </div>
  );
}
