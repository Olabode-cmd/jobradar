import { isRecord, asNumberOrNull } from '../lib/guards';
import { ApiError, toApiError } from './api-error';
import { http } from './http-client';

export interface ClearDataResult {
  deleted: number;
  kept: number;
}

// Compacting the database file can take a moment on a large inbox, and a clear must never be retried.
export async function clearData(keepTriaged: boolean): Promise<ClearDataResult> {
  try {
    const response = await http.post<unknown>(
      '/data/clear',
      { keep_triaged: keepTriaged },
      { timeout: 30_000, retries: 0 },
    );
    const body = response.parsedBody;
    if (!isRecord(body)) {
      throw new ApiError('unexpected', 'The API returned the clear result in an unexpected shape.');
    }
    return { deleted: asNumberOrNull(body.deleted) ?? 0, kept: asNumberOrNull(body.kept) ?? 0 };
  } catch (error) {
    throw toApiError(error);
  }
}
