import { Loading03Icon } from '@hugeicons/core-free-icons';
import { HugeiconsIcon } from '@hugeicons/react';

import { Badge } from '../../components/ui/badge';
import { formatDuration } from '../../lib/format-date';
import type { SourceRunStats } from '../../types/run';

function StateCell({ source }: { source: SourceRunStats }) {
  if (source.state === 'running') {
    return (
      <span className="inline-flex items-center gap-1.5 text-forest-300">
        <HugeiconsIcon
          icon={Loading03Icon}
          size={14}
          strokeWidth={2.5}
          className="motion-safe:animate-spin"
        />
        Fetching
      </span>
    );
  }
  return source.state === 'error' ? (
    <Badge tone="danger">Failed</Badge>
  ) : (
    <Badge tone="neutral">Done</Badge>
  );
}

export function SourceRunTable({ sources }: { sources: SourceRunStats[] }) {
  if (sources.length === 0)
    return <p className="text-sm text-forest-300">No source details recorded.</p>;

  return (
    <table className="w-full text-left text-sm">
      <thead className="text-forest-300">
        <tr className="border-b border-forest-700">
          <th className="py-2 pr-4 font-bold">Source</th>
          <th className="py-2 pr-4 font-bold">Status</th>
          <th className="py-2 pr-4 text-right font-bold">Fetched</th>
          <th className="py-2 pr-4 text-right font-bold">New</th>
          <th className="py-2 pr-4 text-right font-bold">Known</th>
          <th className="py-2 text-right font-bold">Time</th>
        </tr>
      </thead>
      <tbody className="tabular-nums">
        {sources.map((source) => (
          <tr key={source.id} className="border-b border-forest-700/60 align-top">
            <td className="py-2.5 pr-4 font-semibold">
              {source.id}
              {source.error ? (
                <p className="mt-1 text-xs font-medium text-danger">{source.error}</p>
              ) : null}
            </td>
            <td className="py-2.5 pr-4">
              <StateCell source={source} />
            </td>
            <td className="py-2.5 pr-4 text-right">{source.fetched}</td>
            <td className="py-2.5 pr-4 text-right font-bold text-lemon-400">{source.newJobs}</td>
            <td className="py-2.5 pr-4 text-right text-forest-300">{source.known}</td>
            <td className="py-2.5 text-right text-forest-300">
              {formatDuration(source.durationMs)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
