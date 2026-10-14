import { Badge } from '../../components/ui/badge';
import { cn } from '../../lib/class-names';
import { formatAge } from '../../lib/format-age';
import type { JobSummary } from '../../types/job';
import { ScoreCell } from './score-cell';

interface JobRowProps {
  job: JobSummary;
  active: boolean;
  checked: boolean;
  onSelect: () => void;
  onToggleChecked: () => void;
}

export function JobRow({ job, active, checked, onSelect, onToggleChecked }: JobRowProps) {
  const age = formatAge(job.postedAt);

  return (
    <li
      className={cn(
        'flex items-start gap-3 border-b border-l-2 border-border px-4 py-3 transition-colors',
        active ? 'border-l-lemon-400 bg-input' : 'border-l-transparent hover:bg-surface',
      )}
    >
      <input
        type="checkbox"
        checked={checked}
        onChange={onToggleChecked}
        aria-label={`Select ${job.title} at ${job.company}`}
        className="mt-1.5 size-4 shrink-0 accent-accent"
      />
      <button
        type="button"
        onClick={onSelect}
        aria-current={active ? 'true' : undefined}
        className="min-w-0 flex-1 text-left"
      >
        <span className="flex items-center gap-2">
          <span className="truncate font-bold">{job.title}</span>
          {job.reposted ? <Badge tone="lemon">Reposted</Badge> : null}
        </span>
        <span className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-muted">
          <span className="font-semibold text-body/85">{job.company}</span>
          {job.locationText ? <span className="truncate">{job.locationText}</span> : null}
          <span>
            {job.postedEstimated ? '~' : ''}
            {age}
          </span>
          {job.remote ? <Badge tone="muted">Remote</Badge> : null}
          {job.sources.map((source) => (
            <Badge key={source} tone="neutral">
              {source}
            </Badge>
          ))}
        </span>
      </button>
      <ScoreCell score={job.score} eligibility={job.eligibility} />
    </li>
  );
}
