import { parseSource, parseSourceTest, parseSources } from '../lib/parse-sources';
import { ApiError, toApiError } from './api-error';
import { http } from './http-client';
import type { Source, SourceTestResult } from '../types/source';

export async function fetchSources(): Promise<Source[]> {
  try {
    const response = await http.get<unknown>('/sources');
    return parseSources(response.parsedBody);
  } catch (error) {
    throw toApiError(error);
  }
}

export async function setSourceEnabled(id: string, enabled: boolean): Promise<Source> {
  try {
    const response = await http.put<unknown>(`/sources/${encodeURIComponent(id)}`, { enabled });
    const source = parseSource(response.parsedBody);
    if (!source)
      throw new ApiError('unexpected', 'The API returned a source in an unexpected shape.');
    return source;
  } catch (error) {
    throw toApiError(error);
  }
}

// A test fetches the live source once, so allow longer than the default client timeout.
export async function testSource(id: string): Promise<SourceTestResult> {
  try {
    const response = await http.post<unknown>(
      `/sources/${encodeURIComponent(id)}/test`,
      undefined,
      { timeout: 60_000, retries: 0 },
    );
    return parseSourceTest(response.parsedBody);
  } catch (error) {
    throw toApiError(error);
  }
}
