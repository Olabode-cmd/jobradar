import { Banner } from '../../components/ui/banner';
import { Button } from '../../components/ui/button';
import { EmptyState } from '../../components/ui/empty-state';
import { AddCompanyForm } from './add-company-form';
import { CompanyTable } from './company-table';
import { useCompanies } from './use-companies';

export function CompaniesPage() {
  const c = useCompanies();

  return (
    <div>
      <h1 className="text-4xl font-extrabold tracking-tight">Companies</h1>
      <p className="mt-2 mb-10 max-w-2xl text-forest-300">
        Company job boards JobRadar checks on every run. A board that fails is flagged here instead
        of being dropped.
      </p>

      <div className="space-y-6">
        <AddCompanyForm busy={c.busy} onAdd={c.add} onImport={c.importMany} onAddSeed={c.addSeed} />

        {c.notice ? <Banner tone="info" title={c.notice} /> : null}
        {c.actionError ? (
          <Banner tone="error" title="That didn't work">
            {c.actionError}
          </Banner>
        ) : null}
        {c.error ? (
          <Banner
            tone="error"
            title="Couldn't load companies"
            action={
              <Button variant="ghost" onClick={c.reload} className="h-9 px-4">
                Try again
              </Button>
            }
          >
            {c.error.message}
          </Banner>
        ) : null}

        {c.loading ? (
          <p role="status" className="text-forest-300">
            Loading companies…
          </p>
        ) : c.companies.length === 0 && !c.error ? (
          <EmptyState title="No companies tracked yet">
            Paste a careers page link above, or add the suggested list to start with 46 companies
            that hire remotely.
          </EmptyState>
        ) : (
          <CompanyTable
            companies={c.companies}
            busy={c.busy}
            onToggle={(company, enabled) => void c.toggle(company, enabled)}
            onRemove={(company) => void c.remove(company)}
          />
        )}
      </div>
    </div>
  );
}
