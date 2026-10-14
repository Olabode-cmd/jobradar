import { parseCompanies, parseCompany, parseImportResult } from '../lib/parse-companies';
import type { CompaniesResponse, Company, ImportResult } from '../types/company';
import { ApiError, toApiError } from './api-error';
import { http } from './http-client';

function requireCompany(body: unknown): Company {
  const company = parseCompany(body);
  if (!company)
    throw new ApiError('unexpected', 'The API returned a company in an unexpected shape.');
  return company;
}

const path = (provider: string, slug: string) =>
  `/companies/${encodeURIComponent(provider)}/${encodeURIComponent(slug)}`;

export async function fetchCompanies(): Promise<CompaniesResponse> {
  try {
    const response = await http.get<unknown>('/companies');
    return parseCompanies(response.parsedBody);
  } catch (error) {
    throw toApiError(error);
  }
}

// Adding checks the board exists by fetching it, which can take a few seconds.
export async function addCompany(url: string): Promise<Company> {
  try {
    const response = await http.post<unknown>(
      '/companies',
      { url },
      { timeout: 40_000, retries: 0 },
    );
    return requireCompany(response.parsedBody);
  } catch (error) {
    throw toApiError(error);
  }
}

export async function importCompanies(urls: string[]): Promise<ImportResult> {
  try {
    const response = await http.post<unknown>('/companies/import', { urls });
    return parseImportResult(response.parsedBody);
  } catch (error) {
    throw toApiError(error);
  }
}

export async function addSeedCompanies(): Promise<number> {
  try {
    const response = await http.post<unknown>('/companies/seed');
    return parseImportResult(response.parsedBody).added;
  } catch (error) {
    throw toApiError(error);
  }
}

export async function setCompanyEnabled(
  provider: string,
  slug: string,
  enabled: boolean,
): Promise<Company> {
  try {
    const response = await http.patch<unknown>(path(provider, slug), { enabled });
    return requireCompany(response.parsedBody);
  } catch (error) {
    throw toApiError(error);
  }
}

export async function removeCompany(provider: string, slug: string): Promise<void> {
  try {
    await http.delete(path(provider, slug));
  } catch (error) {
    throw toApiError(error);
  }
}
