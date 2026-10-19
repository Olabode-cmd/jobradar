export type SourceRunState = 'running' | 'ok' | 'error';

export interface SourceRunStats {
  id: string;
  state: SourceRunState;
  fetched: number;
  newJobs: number;
  known: number;
  skipped: number;
  dropped: number;
  dropReasons: Array<{ reason: string; count: number }>;
  error: string | null;
  durationMs: number | null;
}

export type RunState = 'idle' | 'running' | 'finished' | 'failed';

export interface LlmSummary {
  assessed: number;
  failed: number;
  message: string | null;
}

export interface RunProgress {
  state: RunState;
  runId: number | null;
  startedAt: string | null;
  finishedAt: string | null;
  dryRun: boolean;
  error: string | null;
  stage: 'fetch' | 'ai';
  llm: LlmSummary | null;
  sources: SourceRunStats[];
}

export interface RunHistoryItem {
  id: number;
  startedAt: string | null;
  finishedAt: string | null;
  trigger: string;
  error: string | null;
  newJobs: number;
  llm: LlmSummary | null;
  sources: SourceRunStats[];
}
