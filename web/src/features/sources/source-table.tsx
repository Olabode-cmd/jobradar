import { Fragment } from 'react';

import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Switch } from '../../components/ui/switch';
import { formatAge } from '../../lib/format-age';
import type { Source } from '../../types/source';
import { SourceTestPanel } from './source-test-panel';
import type { TestState } from './use-sources';

interface SourceTableProps {
  sources: Source[];
  tests: Record<string, TestState>;
  onToggle: (id: string, enabled: boolean) => void;
  onTest: (id: string) => void;
  onDismissTest: (id: string) => void;
}

const TYPE_LABELS: Record<string, string> = {
  api: 'JSON feed',
  rss: 'RSS feed',
  ats: 'Company boards',
  hn: 'Hacker News',
  selector: 'Web page',
};

function LastRun({ source }: { source: Source }) {
  if (!source.lastRunAt) return <span className="text-forest-300">Never run</span>;
  if (source.lastStatus === 'error') {
    return (
      <div>
        <Badge tone="danger">Failed {formatAge(source.lastRunAt)}</Badge>
        {source.lastError ? (
          <p className="mt-1 max-w-xs text-xs font-medium break-words text-danger">
            {source.lastError}
          </p>
        ) : null}
      </div>
    );
  }
  return <span className="text-forest-300">OK {formatAge(source.lastRunAt)}</span>;
}

export function SourceTable({ sources, tests, onToggle, onTest, onDismissTest }: SourceTableProps) {
  return (
    <div className="overflow-x-auto rounded-xl border border-forest-700 bg-forest-900">
      <table className="w-full text-left text-sm">
        <thead className="text-forest-300">
          <tr className="border-b border-forest-700">
            <th className="px-5 py-3 font-bold">Source</th>
            <th className="px-3 py-3 font-bold">Type</th>
            <th className="px-3 py-3 font-bold">Last run</th>
            <th className="px-3 py-3 font-bold">On</th>
            <th className="px-5 py-3 text-right font-bold">
              <span className="sr-only">Test</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {sources.map((source) => {
            const test = tests[source.id];
            return (
              <Fragment key={source.id}>
                <tr className="border-b border-forest-700/60 align-top">
                  <td className="px-5 py-3.5">
                    <span className="flex items-center gap-2">
                      <span className="font-bold">{source.name}</span>
                      <Badge tone={source.tier === 'C' ? 'danger' : 'muted'}>
                        Tier {source.tier}
                      </Badge>
                    </span>
                    {source.trackedCompanies !== null ? (
                      <p className="mt-0.5 text-xs text-forest-300">
                        {source.trackedCompanies} tracked{' '}
                        {source.trackedCompanies === 1 ? 'company' : 'companies'}
                      </p>
                    ) : null}
                    {source.warning ? (
                      <p className="mt-1 max-w-md text-xs font-medium text-danger">
                        {source.warning}
                      </p>
                    ) : null}
                  </td>
                  <td className="px-3 py-3.5 text-forest-300">
                    {TYPE_LABELS[source.type] ?? source.type}
                  </td>
                  <td className="px-3 py-3.5">
                    <LastRun source={source} />
                  </td>
                  <td className="px-3 py-3.5">
                    <Switch
                      checked={source.enabled}
                      onChange={(enabled) => onToggle(source.id, enabled)}
                      aria-label={`${source.enabled ? 'Disable' : 'Enable'} ${source.name}`}
                    />
                  </td>
                  <td className="px-5 py-3.5 text-right">
                    <Button
                      variant="ghost"
                      className="h-9 px-4"
                      onClick={() => onTest(source.id)}
                      disabled={test?.status === 'running'}
                    >
                      {test?.status === 'running' ? 'Testing…' : 'Test'}
                    </Button>
                  </td>
                </tr>
                {test ? (
                  <tr className="border-b border-forest-700/60 bg-forest-800/50">
                    <td colSpan={5} className="px-5 py-4">
                      <SourceTestPanel state={test} onDismiss={() => onDismissTest(source.id)} />
                    </td>
                  </tr>
                ) : null}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
