import { ApiError } from '../api/api-error';
import type { CompaniesResponse, Company, ImportResult } from '../types/company';
import { asNumberOrNull, asString, asStringOrNull, isRecord } from './guards';

function malformed(what: string): ApiError {
  return new ApiError('unexpected', `The API returned ${what} in an unexpected shape.`);
}

export function parseCompany(raw: unknown): Company | null {
  if (!isRecord(raw) || typeof raw.provider !== 'string' || typeof raw.slug !== 'string')
    return null;
  return {
    provider: raw.provider,
    providerName: asString(raw.provider_name, raw.provider),
    slug: raw.slug,
    name: asString(raw.name, raw.slug),
    enabled: raw.enabled !== false,
    lastCheckedAt: asStringOrNull(raw.last_checked_at),
    lastError: asStringOrNull(raw.last_error),
    openRoles: asNumberOrNull(raw.open_roles),
  };
}

export function parseCompanies(body: unknown): CompaniesResponse {
  if (!isRecord(body) || !Array.isArray(body.items)) throw malformed('the company list');
  const items = body.items.flatMap((item) => {
    const company = parseCompany(item);
    return company ? [company] : [];
  });
  const providers = Array.isArray(body.providers)
    ? body.providers.flatMap((item) =>
        isRecord(item) && typeof item.id === 'string'
          ? [{ id: item.id, name: asString(item.name, item.id) }]
          : [],
      )
    : [];
  return { items, providers };
}

export function parseImportResult(body: unknown): ImportResult {
  if (!isRecord(body)) throw malformed('an import result');
  const rejected = Array.isArray(body.rejected)
    ? body.rejected.flatMap((item) =>
        isRecord(item) && typeof item.url === 'string'
          ? [{ url: item.url, reason: asString(item.reason, 'Not supported') }]
          : [],
      )
    : [];
  return {
    added: asNumberOrNull(body.added) ?? 0,
    alreadyTracked: asNumberOrNull(body.already_tracked) ?? 0,
    rejected,
  };
}
