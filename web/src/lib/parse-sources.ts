import { ApiError } from '../api/api-error';
import type { Source, SourceSampleJob, SourceTestResult, SourceTier } from '../types/source';
import { asNumberOrNull, asString, asStringOrNull, isRecord } from './guards';

const TIERS: readonly SourceTier[] = ['A', 'B', 'C'];

function malformed(what: string): ApiError {
  return new ApiError('unexpected', `The API returned ${what} in an unexpected shape.`);
}

export function parseSource(raw: unknown): Source | null {
  if (!isRecord(raw) || typeof raw.id !== 'string') return null;
  return {
    id: raw.id,
    name: asString(raw.name, raw.id),
    tier: TIERS.find((tier) => tier === raw.tier) ?? 'B',
    kind: asString(raw.kind),
    type: asString(raw.type),
    enabled: raw.enabled === true,
    custom: raw.custom === true,
    trackedCompanies: asNumberOrNull(raw.tracked_companies),
    warning: asStringOrNull(raw.warning),
    lastRunAt: asStringOrNull(raw.last_run_at),
    lastStatus: raw.last_status === 'ok' || raw.last_status === 'error' ? raw.last_status : null,
    lastError: asStringOrNull(raw.last_error),
  };
}

export function parseSources(body: unknown): Source[] {
  if (!isRecord(body) || !Array.isArray(body.items)) throw malformed('the source list');
  return body.items.flatMap((item) => {
    const source = parseSource(item);
    return source ? [source] : [];
  });
}

function parseSample(raw: unknown): SourceSampleJob[] {
  if (!Array.isArray(raw)) return [];
  return raw.flatMap((item) =>
    isRecord(item) && typeof item.title === 'string'
      ? [
          {
            title: item.title,
            company: asString(item.company),
            locationText: asString(item.location_text),
            postedAt: asStringOrNull(item.posted_at),
            url: asStringOrNull(item.url),
          },
        ]
      : [],
  );
}

export function parseSourceTest(body: unknown): SourceTestResult {
  if (!isRecord(body)) throw malformed('a test result');
  return {
    ok: body.ok === true,
    error: asStringOrNull(body.error),
    count: asNumberOrNull(body.count) ?? 0,
    sample: parseSample(body.sample),
    durationMs: asNumberOrNull(body.duration_ms) ?? 0,
  };
}
