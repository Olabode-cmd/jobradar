import { toApiError } from './api-error';
import { http } from './http-client';

export interface ApiHealth {
  databaseOk: boolean;
}

export async function fetchHealth(): Promise<ApiHealth> {
  try {
    const response = await http.get<unknown>('/health');
    const body = response.parsedBody;
    const db = typeof body === 'object' && body !== null && 'db' in body ? body.db : null;
    return { databaseOk: db === 'ok' };
  } catch (error) {
    throw toApiError(error);
  }
}
