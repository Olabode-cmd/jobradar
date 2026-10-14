import { parseRunHistory, parseRunProgress } from '../lib/parse-runs';
import type { RunHistoryItem, RunProgress } from '../types/run';
import { toApiError } from './api-error';
import { http } from './http-client';

export async function startRun(
  options: { sources?: string[]; dryRun?: boolean } = {},
): Promise<void> {
  try {
    await http.post('/runs', { sources: options.sources, dry_run: options.dryRun ?? false });
  } catch (error) {
    throw toApiError(error);
  }
}

export async function fetchCurrentRun(): Promise<RunProgress> {
  try {
    const response = await http.get<unknown>('/runs/current');
    return parseRunProgress(response.parsedBody);
  } catch (error) {
    throw toApiError(error);
  }
}

export async function fetchRunHistory(): Promise<RunHistoryItem[]> {
  try {
    const response = await http.get<unknown>('/runs');
    return parseRunHistory(response.parsedBody);
  } catch (error) {
    throw toApiError(error);
  }
}
