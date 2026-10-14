import { ApiError } from '../api/api-error';
import type {
  RunHistoryItem,
  RunProgress,
  RunState,
  SourceRunState,
  SourceRunStats,
} from '../types/run';
import { asNumberOrNull, asString, asStringOrNull, isRecord } from './guards';

const RUN_STATES: readonly RunState[] = ['idle', 'running', 'finished', 'failed'];
const SOURCE_STATES: readonly SourceRunState[] = ['running', 'ok', 'error'];

function parseSource(raw: unknown): SourceRunStats | null {
  if (!isRecord(raw) || typeof raw.id !== 'string') return null;
  const error = asStringOrNull(raw.error);
  const state = SOURCE_STATES.find((item) => item === raw.state) ?? (error ? 'error' : 'ok');
  return {
    id: raw.id,
    state,
    fetched: asNumberOrNull(raw.fetched) ?? 0,
    newJobs: asNumberOrNull(raw.new) ?? 0,
    known: asNumberOrNull(raw.known) ?? 0,
    skipped: asNumberOrNull(raw.skipped) ?? 0,
    error,
    durationMs: asNumberOrNull(raw.duration_ms),
  };
}

function parseSources(raw: unknown): SourceRunStats[] {
  if (!Array.isArray(raw)) return [];
  return raw.flatMap((item) => {
    const source = parseSource(item);
    return source ? [source] : [];
  });
}

export function parseRunProgress(body: unknown): RunProgress {
  if (!isRecord(body))
    throw new ApiError('unexpected', 'The API returned a run in an unexpected shape.');
  return {
    state: RUN_STATES.find((state) => state === body.state) ?? 'idle',
    runId: asNumberOrNull(body.run_id),
    startedAt: asStringOrNull(body.started_at),
    finishedAt: asStringOrNull(body.finished_at),
    dryRun: body.dry_run === true,
    error: asStringOrNull(body.error),
    sources: parseSources(body.sources),
  };
}

export function parseRunHistory(body: unknown): RunHistoryItem[] {
  if (!isRecord(body) || !Array.isArray(body.items)) {
    throw new ApiError('unexpected', 'The API returned run history in an unexpected shape.');
  }
  return body.items.flatMap((item) => {
    const id = isRecord(item) ? asNumberOrNull(item.id) : null;
    if (!isRecord(item) || id === null) return [];
    return [
      {
        id,
        startedAt: asStringOrNull(item.started_at),
        finishedAt: asStringOrNull(item.finished_at),
        trigger: asString(item.trigger, 'cli'),
        error: asStringOrNull(item.error),
        newJobs: asNumberOrNull(item.new) ?? 0,
        sources: parseSources(item.sources),
      },
    ];
  });
}
