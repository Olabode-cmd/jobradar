import { Banner } from '../../components/ui/banner';
import { Button } from '../../components/ui/button';
import { SourceTable } from './source-table';
import { useSources } from './use-sources';

export function SourcesPage() {
  const { sources, loading, error, actionError, tests, reload, toggle, runTest, dismissTest } =
    useSources();

  return (
    <div>
      <h1 className="text-4xl font-extrabold tracking-tight">Sources</h1>
      <p className="mt-2 mb-10 max-w-2xl text-muted">
        Where JobRadar looks for jobs. Switch a source off to skip it, or press Test to fetch it
        once and see what it returns without saving anything.
      </p>

      <div className="space-y-4">
        {actionError ? (
          <Banner tone="error" title="That change didn't save">
            {actionError}
          </Banner>
        ) : null}

        {error ? (
          <Banner
            tone="error"
            title="Couldn't load sources"
            action={
              <Button variant="ghost" onClick={reload} className="h-9 px-4">
                Try again
              </Button>
            }
          >
            {error.message}
          </Banner>
        ) : null}

        {loading && sources.length === 0 ? (
          <p role="status" className="text-muted">
            Loading sources…
          </p>
        ) : null}

        {sources.length > 0 ? (
          <SourceTable
            sources={sources}
            tests={tests}
            onToggle={(id, enabled) => void toggle(id, enabled)}
            onTest={(id) => void runTest(id)}
            onDismissTest={dismissTest}
          />
        ) : null}
      </div>
    </div>
  );
}
