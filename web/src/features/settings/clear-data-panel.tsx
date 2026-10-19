import { useId } from 'react';

import { Banner } from '../../components/ui/banner';
import { Button } from '../../components/ui/button';
import { useClearData } from './use-clear-data';

function jobsLabel(count: number): string {
  return `${count} ${count === 1 ? 'job' : 'jobs'}`;
}

export function ClearDataPanel() {
  const clear = useClearData();
  const keepId = useId();

  return (
    <div className="space-y-4 border-t border-border pt-6">
      <div>
        <h3 className="text-sm font-bold">Clear jobs</h3>
        <p className="mt-1 text-sm text-muted">
          Deletes stored jobs and run history so the next fetch starts clean. Your profile, sources
          and API key stay as they are.
        </p>
      </div>

      {clear.result ? (
        <p role="status" className="text-sm font-bold text-success">
          Deleted {jobsLabel(clear.result.deleted)}
          {clear.result.kept > 0 ? `, kept ${jobsLabel(clear.result.kept)}` : ''}.
        </p>
      ) : null}

      {clear.open ? (
        <div
          role="group"
          aria-label="Confirm clearing jobs"
          className="space-y-4 rounded-xl border border-danger/60 p-4"
        >
          <p className="text-sm font-bold">
            {clear.toDelete === null
              ? 'Counting jobs…'
              : `This deletes ${jobsLabel(clear.toDelete)} and all run history. It can't be undone.`}
          </p>
          <label htmlFor={keepId} className="flex items-start gap-3 text-sm">
            <input
              id={keepId}
              type="checkbox"
              checked={clear.keepTriaged}
              onChange={(event) => clear.setKeepTriaged(event.target.checked)}
              className="mt-0.5 size-4 shrink-0 accent-accent"
            />
            <span>
              Keep jobs I've already triaged
              <span className="block text-muted">
                Saved, applied, interviewing, rejected and ignored. Ignored jobs stay so they don't
                come back as new.
              </span>
            </span>
          </label>
          {clear.error ? (
            <Banner tone="error" title="Couldn't clear your jobs">
              {clear.error}
            </Banner>
          ) : null}
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => void clear.confirm()}
              disabled={clear.toDelete === null || clear.clearing}
              className="inline-flex h-11 items-center justify-center rounded-lg bg-danger px-5 text-sm font-bold text-white transition-colors enabled:hover:bg-danger/90 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {clear.clearing ? 'Deleting…' : 'Delete jobs'}
            </button>
            <Button variant="ghost" onClick={clear.cancel} disabled={clear.clearing}>
              Cancel
            </Button>
          </div>
        </div>
      ) : (
        <Button variant="ghost" onClick={() => void clear.begin()}>
          Clear jobs…
        </Button>
      )}
    </div>
  );
}
