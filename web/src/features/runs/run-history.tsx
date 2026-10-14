import { EmptyState } from '../../components/ui/empty-state';
import { formatDateTime } from '../../lib/format-date';
import type { RunHistoryItem } from '../../types/run';
import { LlmSummaryLine } from './llm-summary-line';
import { SourceRunTable } from './source-run-table';

function RunSummary({ run }: { run: RunHistoryItem }) {
  const failedSources = run.sources.filter((source) => source.state === 'error').length;
  const unfinished = run.finishedAt === null;

  return (
    <summary className="flex cursor-pointer flex-wrap items-center gap-x-4 gap-y-1 px-5 py-3.5 text-sm">
      <span className="font-extrabold">Run #{run.id}</span>
      <span className="text-forest-300">{formatDateTime(run.startedAt)}</span>
      <span className="text-forest-300">
        {run.trigger === 'dashboard' ? 'From dashboard' : 'From command line'}
      </span>
      <span className="ml-auto flex items-center gap-4 font-bold tabular-nums">
        {run.error ? <span className="text-danger">Failed</span> : null}
        {unfinished && !run.error ? <span className="text-forest-300">Did not finish</span> : null}
        {failedSources > 0 ? <span className="text-danger">{failedSources} failed</span> : null}
        <span className="text-lemon-400">+{run.newJobs} new</span>
      </span>
    </summary>
  );
}

export function RunHistory({ items }: { items: RunHistoryItem[] }) {
  if (items.length === 0) {
    return (
      <EmptyState title="No runs yet">
        Press Run now to fetch jobs from every enabled source.
      </EmptyState>
    );
  }

  return (
    <div className="space-y-2">
      {items.map((run) => (
        <details key={run.id} className="rounded-xl border border-forest-700 bg-forest-900">
          <RunSummary run={run} />
          <div className="border-t border-forest-700 px-5 py-3">
            {run.error ? (
              <p className="mb-3 text-sm font-semibold text-danger">{run.error}</p>
            ) : null}
            <SourceRunTable sources={run.sources} />
            {run.llm ? (
              <div className="mt-3">
                <LlmSummaryLine llm={run.llm} />
              </div>
            ) : null}
          </div>
        </details>
      ))}
    </div>
  );
}
