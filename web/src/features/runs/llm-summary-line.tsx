import type { LlmSummary } from '../../types/run';

export function LlmSummaryLine({ llm }: { llm: LlmSummary | null }) {
  if (!llm) return null;
  return (
    <p className="text-sm">
      <span className="font-bold">AI check: </span>
      <span className="text-muted">
        {llm.assessed} {llm.assessed === 1 ? 'job' : 'jobs'} assessed
        {llm.failed > 0 ? `, ${llm.failed} skipped` : ''}.
      </span>
      {llm.message ? <span className="font-semibold text-danger"> {llm.message}</span> : null}
    </p>
  );
}
