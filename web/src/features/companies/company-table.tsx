import { Delete02Icon } from '@hugeicons/core-free-icons';
import { HugeiconsIcon } from '@hugeicons/react';

import { Badge } from '../../components/ui/badge';
import { Switch } from '../../components/ui/switch';
import { formatAge } from '../../lib/format-age';
import type { Company } from '../../types/company';

interface CompanyTableProps {
  companies: Company[];
  busy: boolean;
  onToggle: (company: Company, enabled: boolean) => void;
  onRemove: (company: Company) => void;
}

function Health({ company }: { company: Company }) {
  if (company.lastError) {
    return (
      <div>
        <Badge tone="danger">Last check failed</Badge>
        <p className="mt-1 max-w-xs text-xs font-medium break-words text-danger">
          {company.lastError}
        </p>
      </div>
    );
  }
  if (!company.lastCheckedAt) return <span className="text-muted">Not checked yet</span>;
  return <span className="text-muted">Checked {formatAge(company.lastCheckedAt)}</span>;
}

export function CompanyTable({ companies, busy, onToggle, onRemove }: CompanyTableProps) {
  return (
    <div className="overflow-x-auto rounded-xl border border-border bg-surface">
      <table className="w-full text-left text-sm">
        <thead className="text-muted">
          <tr className="border-b border-border">
            <th className="px-5 py-3 font-bold">Company</th>
            <th className="px-3 py-3 font-bold">Board</th>
            <th className="px-3 py-3 text-right font-bold">Open roles</th>
            <th className="px-3 py-3 font-bold">Health</th>
            <th className="px-3 py-3 font-bold">On</th>
            <th className="px-5 py-3 text-right font-bold">
              <span className="sr-only">Remove</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {companies.map((company) => (
            <tr
              key={`${company.provider}:${company.slug}`}
              className="border-b border-border/60 align-top"
            >
              <td className="px-5 py-3.5 font-bold">{company.name}</td>
              <td className="px-3 py-3.5 text-muted">
                {company.providerName} · {company.slug}
              </td>
              <td className="px-3 py-3.5 text-right tabular-nums">{company.openRoles ?? '–'}</td>
              <td className="px-3 py-3.5">
                <Health company={company} />
              </td>
              <td className="px-3 py-3.5">
                <Switch
                  checked={company.enabled}
                  onChange={(enabled) => onToggle(company, enabled)}
                  disabled={busy}
                  aria-label={`${company.enabled ? 'Stop tracking' : 'Track'} ${company.name}`}
                />
              </td>
              <td className="px-5 py-3.5 text-right">
                <button
                  type="button"
                  onClick={() => onRemove(company)}
                  disabled={busy}
                  aria-label={`Remove ${company.name}`}
                  className="rounded-md p-2 text-muted transition-colors hover:bg-raised hover:text-danger disabled:opacity-50"
                >
                  <HugeiconsIcon icon={Delete02Icon} size={18} strokeWidth={2} />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
