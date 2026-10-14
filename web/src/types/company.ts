export interface Company {
  provider: string;
  providerName: string;
  slug: string;
  name: string;
  enabled: boolean;
  lastCheckedAt: string | null;
  lastError: string | null;
  openRoles: number | null;
}

export interface CompaniesResponse {
  items: Company[];
  providers: Array<{ id: string; name: string }>;
}

export interface ImportResult {
  added: number;
  alreadyTracked: number;
  rejected: Array<{ url: string; reason: string }>;
}
