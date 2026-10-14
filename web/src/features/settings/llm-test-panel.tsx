import { formatDuration } from '../../lib/format-date';
import type { TestState } from './use-settings';

const HINTS: Record<string, string> = {
  auth: 'Check that the key is correct and still active.',
  not_found: 'Set the Model field to a model your provider offers, and check the Base URL.',
  rate_limit: 'Wait a minute, then test again.',
  network: 'Check the Base URL and that the service is running.',
};

export function LlmTestPanel({ state }: { state: TestState }) {
  if (state.status === 'idle') return null;

  if (state.status === 'running') {
    return (
      <p role="status" className="text-sm text-forest-300">
        Sending one small request to your provider…
      </p>
    );
  }

  if (state.status === 'failed') {
    return (
      <p role="alert" className="text-sm font-semibold text-danger">
        {state.message}
      </p>
    );
  }

  const { result } = state;
  if (result.ok) {
    return (
      <p role="status" className="text-sm font-bold text-lemon-400">
        Connected. {result.provider} answered "{result.reply}"
        {result.model ? ` using ${result.model}` : ''} in {formatDuration(result.durationMs)}.
      </p>
    );
  }

  return (
    <div role="alert" className="text-sm">
      <p className="font-bold text-danger">{result.message}</p>
      {HINTS[result.kind] ? <p className="mt-1 text-forest-300">{HINTS[result.kind]}</p> : null}
    </div>
  );
}
