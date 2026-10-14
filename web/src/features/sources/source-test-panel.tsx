import { Button } from '../../components/ui/button';
import { formatAge } from '../../lib/format-age';
import { formatDuration } from '../../lib/format-date';
import type { TestState } from './use-sources';

interface SourceTestPanelProps {
  state: TestState;
  onDismiss: () => void;
}

export function SourceTestPanel({ state, onDismiss }: SourceTestPanelProps) {
  if (state.status === 'running') {
    return <p className="text-sm text-muted">Fetching the source once. Nothing is saved.</p>;
  }

  if (state.status === 'failed') {
    return <p className="text-sm font-semibold text-danger">{state.message}</p>;
  }

  const { result } = state;
  return (
    <div>
      <div className="flex items-center justify-between gap-4">
        <p
          className={`text-sm font-bold ${result.ok ? 'text-success' : 'text-danger'}`}
          role="status"
        >
          {result.ok
            ? `Works: ${result.count} postings in ${formatDuration(result.durationMs)}. Nothing was saved.`
            : `Failed: ${result.error ?? 'unknown error'}`}
        </p>
        <Button variant="ghost" onClick={onDismiss} className="h-8 px-3">
          Close
        </Button>
      </div>
      {result.ok && result.sample.length === 0 ? (
        <p className="mt-2 text-sm text-muted">
          The source answered but none of its postings had both a title and a link.
        </p>
      ) : null}
      {result.sample.length > 0 ? (
        <ul className="mt-3 space-y-2">
          {result.sample.map((job) => (
            <li key={`${job.title}-${job.url}`} className="text-sm">
              <span className="font-bold">{job.title}</span>
              <span className="text-muted">
                {' '}
                · {job.company}
                {job.locationText ? ` · ${job.locationText}` : ''} · {formatAge(job.postedAt)}
              </span>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
