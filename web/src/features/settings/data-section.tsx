import { Download01Icon } from '@hugeicons/core-free-icons';
import { HugeiconsIcon } from '@hugeicons/react';

import { SectionPanel } from '../../components/ui/section-panel';
import type { Settings } from '../../types/settings';

const LINK_CLASSES =
  'inline-flex h-11 items-center gap-2 rounded-lg border border-forest-600 px-5 text-sm font-bold transition-colors hover:border-forest-300';

function PathRow({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-sm font-bold">{label}</dt>
      <dd className="mt-0.5 text-sm break-all text-forest-300">{value}</dd>
    </div>
  );
}

export function DataSection({ settings }: { settings: Settings }) {
  return (
    <SectionPanel
      title="Your data"
      description="Everything stays on this computer. Export your jobs, or back up by copying the two files below."
    >
      <div className="flex flex-wrap gap-3">
        <a href="/api/export?format=csv" download className={LINK_CLASSES}>
          <HugeiconsIcon icon={Download01Icon} size={18} strokeWidth={2} />
          Export all jobs (CSV)
        </a>
        <a href="/api/export?format=markdown" download className={LINK_CLASSES}>
          <HugeiconsIcon icon={Download01Icon} size={18} strokeWidth={2} />
          Export all jobs (Markdown)
        </a>
        <a
          href="/api/export?format=markdown&status=saved,applied,interviewing"
          download
          className={LINK_CLASSES}
        >
          <HugeiconsIcon icon={Download01Icon} size={18} strokeWidth={2} />
          Applications only (Markdown)
        </a>
      </div>
      <dl className="space-y-3">
        <PathRow label="Jobs and history" value={settings.dbPath} />
        <PathRow label="Search settings" value={settings.configPath} />
      </dl>
    </SectionPanel>
  );
}
