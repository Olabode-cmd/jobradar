import { parseConfigResponse } from '../lib/parse-config';
import type { ConfigSnapshot, EditableConfig } from '../types/config';
import { toApiError } from './api-error';
import { http } from './http-client';

export async function fetchConfig(): Promise<ConfigSnapshot> {
  try {
    const response = await http.get<unknown>('/config');
    return parseConfigResponse(response.parsedBody);
  } catch (error) {
    throw toApiError(error);
  }
}

export async function saveConfig(update: EditableConfig): Promise<ConfigSnapshot> {
  try {
    const response = await http.put<unknown>('/config', update);
    return parseConfigResponse(response.parsedBody);
  } catch (error) {
    throw toApiError(error);
  }
}
