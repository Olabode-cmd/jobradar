import { cn } from '../../lib/class-names';
import type { Eligibility } from '../../types/job';

const ELIGIBILITY_STYLES: Record<Eligibility, { label: string; className: string }> = {
  eligible: { label: 'Eligible', className: 'text-success' },
  unclear: { label: 'Unclear', className: 'text-muted' },
  restricted: { label: 'Restricted', className: 'text-danger' },
};

export function ScoreCell({
  score,
  eligibility,
}: {
  score: number | null;
  eligibility: Eligibility | null;
}) {
  const style = eligibility ? ELIGIBILITY_STYLES[eligibility] : null;
  return (
    <div className="w-20 shrink-0 text-right">
      <p className="text-lg leading-tight font-extrabold tabular-nums">
        {score === null ? '–' : score.toFixed(1)}
      </p>
      {style ? <p className={cn('text-xs font-bold', style.className)}>{style.label}</p> : null}
    </div>
  );
}
