import { PlayIcon } from '@hugeicons/core-free-icons';
import { HugeiconsIcon } from '@hugeicons/react';
import { useState } from 'react';

import { Banner } from '../../components/ui/banner';
import { Button } from '../../components/ui/button';
import { SectionPanel } from '../../components/ui/section-panel';
import { LlmSummaryLine } from './llm-summary-line';
import { RunHistory } from './run-history';
import { SourceRunTable } from './source-run-table';
import { useRuns } from './use-runs';

export function RunsPage() {
  const { progress, history, error, starting, running, start } = useRuns();
  const [dryRun, setDryRun] = useState(false);

  const showProgress = progress !== null && progress.state !== 'idle';
  const doneCount = progress?.sources.filter((source) => source.state !== 'running').length ?? 0;

  return (
    <div>
      <h1 className="text-4xl font-extrabold tracking-tight">Runs</h1>
      <p className="mt-2 mb-10 max-w-2xl text-muted">
        A run fetches every enabled source, removes duplicates and stores what's new. It never
        applies to anything for you.
      </p>

      <div className="space-y-6">
        <div className="flex flex-wrap items-center gap-x-6 gap-y-3">
          <Button onClick={() => void start({ dryRun })} disabled={running || starting}>
            <HugeiconsIcon icon={PlayIcon} size={18} strokeWidth={2.5} />
            {running ? 'Running…' : 'Run now'}
          </Button>
          <label className="flex items-center gap-2.5 text-sm font-semibold">
            <input
              type="checkbox"
              checked={dryRun}
              onChange={(event) => setDryRun(event.target.checked)}
              disabled={running}
              className="size-4 accent-accent"
            />
            Dry run: fetch and count, but store nothing
          </label>
        </div>

        {error ? (
          <Banner tone="error" title="Couldn't start the run">
            {error.message}
          </Banner>
        ) : null}

        {showProgress ? (
          <SectionPanel
            title={
              progress.state === 'running'
                ? progress.stage === 'ai'
                  ? 'Fetching done. AI is checking the best matches…'
                  : `Fetching: ${doneCount} of ${progress.sources.length} sources done`
                : progress.state === 'failed'
                  ? 'Run failed'
                  : progress.dryRun
                    ? 'Dry run finished'
                    : 'Run finished'
            }
          >
            {progress.error ? (
              <p className="text-sm font-semibold text-danger">{progress.error}</p>
            ) : null}
            <SourceRunTable sources={progress.sources} />
            <LlmSummaryLine llm={progress.llm} />
          </SectionPanel>
        ) : null}

        <section>
          <h2 className="mb-3 text-lg font-extrabold tracking-tight">History</h2>
          <RunHistory items={history} />
        </section>
      </div>
    </div>
  );
}
