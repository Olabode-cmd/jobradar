import { useId, useState, type FormEvent } from 'react';

import { Button } from '../../components/ui/button';

interface AddCompanyFormProps {
  busy: boolean;
  onAdd: (url: string) => Promise<boolean>;
  onImport: (urls: string[]) => Promise<boolean>;
  onAddSeed: () => Promise<boolean>;
}

const INPUT_CLASSES =
  'w-full rounded-lg border border-border bg-input px-3.5 text-base font-medium outline-none placeholder:text-muted/60 hover:border-border-dim focus:border-accent';

export function AddCompanyForm({ busy, onAdd, onImport, onAddSeed }: AddCompanyFormProps) {
  const urlId = useId();
  const bulkId = useId();
  const [url, setUrl] = useState('');
  const [bulkOpen, setBulkOpen] = useState(false);
  const [bulkText, setBulkText] = useState('');

  const submitOne = async (event: FormEvent) => {
    event.preventDefault();
    if (!url.trim()) return;
    if (await onAdd(url.trim())) setUrl('');
  };

  const submitBulk = async (event: FormEvent) => {
    event.preventDefault();
    const urls = bulkText
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean);
    if (urls.length === 0) return;
    if (await onImport(urls)) {
      setBulkText('');
      setBulkOpen(false);
    }
  };

  return (
    <div className="space-y-4 rounded-xl border border-border bg-surface p-6">
      <form onSubmit={submitOne}>
        <label htmlFor={urlId} className="mb-2 block text-sm font-bold">
          Add a company by its careers page
        </label>
        <div className="flex flex-wrap gap-3">
          <input
            id={urlId}
            value={url}
            onChange={(event) => setUrl(event.target.value)}
            placeholder="https://boards.greenhouse.io/stripe"
            autoComplete="off"
            className={`${INPUT_CLASSES} h-11 min-w-64 flex-1`}
          />
          <Button type="submit" disabled={busy || !url.trim()}>
            {busy ? 'Checking…' : 'Add company'}
          </Button>
        </div>
        <p className="mt-2 text-sm text-muted">
          Works with Greenhouse, Lever, Ashby, Workable, Recruitee, SmartRecruiters, Teamtailor,
          Personio, BambooHR and Breezy links. JobRadar checks the board exists before adding it.
        </p>
      </form>

      <div className="flex flex-wrap gap-3">
        <Button variant="ghost" onClick={() => void onAddSeed()} disabled={busy}>
          Add suggested companies
        </Button>
        <Button
          variant="ghost"
          onClick={() => setBulkOpen((open) => !open)}
          aria-expanded={bulkOpen}
        >
          Import many links
        </Button>
      </div>

      {bulkOpen ? (
        <form onSubmit={submitBulk}>
          <label htmlFor={bulkId} className="mb-2 block text-sm font-bold">
            One careers page link per line
          </label>
          <textarea
            id={bulkId}
            value={bulkText}
            onChange={(event) => setBulkText(event.target.value)}
            rows={6}
            className={`${INPUT_CLASSES} py-2.5`}
            placeholder={'https://jobs.lever.co/palantir\nhttps://jobs.ashbyhq.com/ramp'}
          />
          <Button type="submit" className="mt-3" disabled={busy || !bulkText.trim()}>
            Import links
          </Button>
        </form>
      ) : null}
    </div>
  );
}
