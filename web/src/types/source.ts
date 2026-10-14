export type SourceTier = 'A' | 'B' | 'C';

export interface Source {
  id: string;
  name: string;
  tier: SourceTier;
  kind: string;
  type: string;
  enabled: boolean;
  custom: boolean;
  trackedCompanies: number | null;
  warning: string | null;
  lastRunAt: string | null;
  lastStatus: 'ok' | 'error' | null;
  lastError: string | null;
}

export interface SourceSampleJob {
  title: string;
  company: string;
  locationText: string;
  postedAt: string | null;
  url: string | null;
}

export interface SourceTestResult {
  ok: boolean;
  error: string | null;
  count: number;
  sample: SourceSampleJob[];
  durationMs: number;
}
