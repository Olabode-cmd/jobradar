import { ArrowUpRight01Icon } from '@hugeicons/core-free-icons';
import { HugeiconsIcon } from '@hugeicons/react';
import type { ReactNode } from 'react';

import type { ApiError } from '../../api/api-error';
import { Badge } from '../../components/ui/badge';
import { Banner } from '../../components/ui/banner';
import { Button } from '../../components/ui/button';
import { CopyButton } from '../../components/ui/copy-button';
import { cn } from '../../lib/class-names';
import { formatAge } from '../../lib/format-age';
import { JOB_STATUSES, type JobDetail, type JobStatus } from '../../types/job';
import { JobNotesField } from './job-notes-field';
import { STATUS_LABELS } from './status-tabs';

interface JobDetailPanelProps {
  detail: JobDetail | null;
  loading: boolean;
  error: ApiError | null;
  onStatus: (status: JobStatus) => void;
  onIgnoreCompany: () => void;
  onSaveNotes: (notes: string) => void;
}

const SHORTCUT_HINTS: Partial<Record<JobStatus, string>> = {
  saved: 'S',
  applied: 'A',
  ignored: 'I',
};

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section>
      <h3 className="mb-2 text-sm font-bold">{title}</h3>
      {children}
    </section>
  );
}

export function JobDetailPanel({
  detail,
  loading,
  error,
  onStatus,
  onIgnoreCompany,
  onSaveNotes,
}: JobDetailPanelProps) {
  const shell =
    'rounded-xl border border-forest-700 bg-forest-900 lg:sticky lg:top-6 lg:max-h-[calc(100vh-3rem)] lg:overflow-auto';

  if (error) {
    return (
      <div className={shell}>
        <div className="p-4">
          <Banner tone="error" title="Couldn't load this job">
            {error.message}
          </Banner>
        </div>
      </div>
    );
  }

  if (!detail) {
    return (
      <div className={cn(shell, 'p-6 text-sm text-forest-300')}>
        {loading ? 'Loading job…' : 'Select a job to read it here.'}
      </div>
    );
  }

  return (
    <article className={cn(shell, 'space-y-6 p-6')} aria-busy={loading}>
      <header>
        <h2 className="text-xl leading-snug font-extrabold tracking-tight">{detail.title}</h2>
        <p className="mt-1 text-sm text-forest-300">
          <span className="font-semibold text-white/85">{detail.company}</span>
          {detail.locationText ? ` · ${detail.locationText}` : ''} ·{' '}
          {detail.postedEstimated ? '~' : ''}
          {formatAge(detail.postedAt)}
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          {detail.remote ? <Badge tone="muted">Remote</Badge> : null}
          {detail.reposted ? <Badge tone="lemon">Reposted</Badge> : null}
          {detail.lowConfidence ? <Badge tone="muted">Low confidence</Badge> : null}
          {detail.salaryText ? <Badge tone="neutral">{detail.salaryText}</Badge> : null}
        </div>
      </header>

      <div className="flex flex-wrap items-center gap-3">
        {detail.applyUrl ? (
          <a
            href={detail.applyUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex h-11 items-center gap-2 rounded-lg bg-lemon-400 px-5 text-sm font-bold text-ink transition-colors hover:bg-lemon-300"
          >
            Open apply page
            <HugeiconsIcon icon={ArrowUpRight01Icon} size={18} strokeWidth={2.5} />
            <kbd className="rounded border border-ink/40 px-1.5 text-xs">O</kbd>
          </a>
        ) : null}
        {detail.applyUrl ? <CopyButton value={detail.applyUrl} label="apply link" /> : null}
      </div>

      <div role="group" aria-label="Move to" className="flex flex-wrap gap-2">
        {JOB_STATUSES.map((status) => (
          <button
            key={status}
            type="button"
            aria-pressed={detail.status === status}
            onClick={() => onStatus(status)}
            className={cn(
              'inline-flex h-9 items-center gap-1.5 rounded-lg border px-3 text-sm font-bold transition-colors',
              detail.status === status
                ? 'border-white bg-white text-ink'
                : 'border-forest-600 hover:border-forest-300',
            )}
          >
            {STATUS_LABELS[status]}
            {SHORTCUT_HINTS[status] ? (
              <kbd className="text-xs text-forest-300">{SHORTCUT_HINTS[status]}</kbd>
            ) : null}
          </button>
        ))}
      </div>

      {detail.scoreReasons.length > 0 ? (
        <Section title={`Why it scored ${detail.score?.toFixed(1) ?? ''}`.trim()}>
          <ul className="space-y-1 text-sm text-white/85">
            {detail.scoreReasons.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
        </Section>
      ) : null}

      {detail.emails.length > 0 ? (
        <Section title="Contact emails">
          <ul className="space-y-1">
            {detail.emails.map((email) => (
              <li key={email} className="flex items-center justify-between gap-2 text-sm">
                <span className="truncate">{email}</span>
                <CopyButton value={email} label={email} />
              </li>
            ))}
          </ul>
        </Section>
      ) : null}

      {detail.sourceLinks.length > 0 ? (
        <Section title="Found on">
          <ul className="space-y-1 text-sm">
            {detail.sourceLinks.map((link) => (
              <li key={`${link.sourceId}-${link.url}`}>
                <a
                  href={link.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-semibold underline decoration-forest-600 underline-offset-4 hover:decoration-lemon-400"
                >
                  {link.sourceId}
                </a>
              </li>
            ))}
          </ul>
        </Section>
      ) : null}

      {detail.description ? (
        <Section title="Description">
          <p className="max-h-80 overflow-auto text-sm leading-relaxed whitespace-pre-line text-white/85">
            {detail.description}
          </p>
        </Section>
      ) : null}

      <JobNotesField key={detail.id} initialValue={detail.notes} onSave={onSaveNotes} />

      <Button variant="ghost" onClick={onIgnoreCompany} className="h-9 px-4 text-danger">
        Ignore everything from {detail.company}
      </Button>
    </article>
  );
}
