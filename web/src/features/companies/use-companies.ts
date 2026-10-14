import { useCallback, useEffect, useState } from 'react';

import { toApiError, type ApiError } from '../../api/api-error';
import {
  addCompany,
  addSeedCompanies,
  fetchCompanies,
  importCompanies,
  removeCompany,
  setCompanyEnabled,
} from '../../api/companies-api';
import type { Company } from '../../types/company';

export function useCompanies() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let cancelled = false;
    fetchCompanies().then(
      (response) => {
        if (cancelled) return;
        setCompanies(response.items);
        setError(null);
        setLoading(false);
      },
      (failure: unknown) => {
        if (cancelled) return;
        setError(toApiError(failure));
        setLoading(false);
      },
    );
    return () => {
      cancelled = true;
    };
  }, [attempt]);

  const reload = useCallback(() => setAttempt((count) => count + 1), []);

  // Runs a mutation with shared busy, error and notice handling, then refreshes the list.
  const perform = useCallback(
    async (action: () => Promise<string | null>): Promise<boolean> => {
      setBusy(true);
      setActionError(null);
      setNotice(null);
      try {
        setNotice(await action());
        reload();
        return true;
      } catch (failure) {
        setActionError(toApiError(failure).message);
        return false;
      } finally {
        setBusy(false);
      }
    },
    [reload],
  );

  const add = useCallback(
    (url: string) =>
      perform(async () => {
        const company = await addCompany(url);
        return `Added ${company.name} (${company.openRoles ?? 0} open roles).`;
      }),
    [perform],
  );

  const importMany = useCallback(
    (urls: string[]) =>
      perform(async () => {
        const result = await importCompanies(urls);
        const skipped = result.rejected.length;
        return (
          `Added ${result.added}, already tracked ${result.alreadyTracked}` +
          (skipped > 0 ? `, skipped ${skipped} unsupported link${skipped === 1 ? '' : 's'}.` : '.')
        );
      }),
    [perform],
  );

  const addSeed = useCallback(
    () =>
      perform(async () => {
        const added = await addSeedCompanies();
        return added > 0
          ? `Added ${added} suggested companies.`
          : 'All suggested companies are already tracked.';
      }),
    [perform],
  );

  const toggle = useCallback(
    (company: Company, enabled: boolean) =>
      perform(async () => {
        await setCompanyEnabled(company.provider, company.slug, enabled);
        return null;
      }),
    [perform],
  );

  const remove = useCallback(
    (company: Company) =>
      perform(async () => {
        await removeCompany(company.provider, company.slug);
        return `Removed ${company.name}.`;
      }),
    [perform],
  );

  return {
    companies,
    loading,
    error,
    busy,
    actionError,
    notice,
    reload,
    add,
    importMany,
    addSeed,
    toggle,
    remove,
  };
}
