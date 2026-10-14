import { File01Icon } from '@hugeicons/core-free-icons';
import { HugeiconsIcon } from '@hugeicons/react';

import { cn } from '../../lib/class-names';
import type { EditableConfig } from '../../types/config';

interface ConfigFileSheetProps {
  config: EditableConfig;
  dirty: boolean;
  fileExists: boolean;
}

const KEY_LINE = /^(\s*)("[^"]+")(:\s?)(.*)$/;

function JsonLine({ line }: { line: string }) {
  const match = KEY_LINE.exec(line);
  if (!match) return <div className="whitespace-pre opacity-75">{line || ' '}</div>;

  const [, indent, key, separator, value] = match;
  return (
    <div className="whitespace-pre">
      {indent}
      <span className="font-extrabold">{key}</span>
      {separator}
      <span className="opacity-75">{value}</span>
    </div>
  );
}

function sheetBadge(dirty: boolean, fileExists: boolean): { text: string; filled: boolean } {
  if (dirty) return { text: 'Unsaved', filled: true };
  return { text: fileExists ? 'In sync' : 'Not created yet', filled: false };
}

export function ConfigFileSheet({ config, dirty, fileExists }: ConfigFileSheetProps) {
  const lines = JSON.stringify(config, null, 2).split('\n');
  const badge = sheetBadge(dirty, fileExists);

  return (
    <aside
      aria-label="Preview of jobradar.config.json"
      className="flex max-h-[calc(100vh-8rem)] flex-col rounded-xl bg-accent text-ink lg:sticky lg:top-6"
    >
      <div className="flex items-center justify-between gap-3 border-b border-ink/20 px-5 py-4">
        <h2 className="flex items-center gap-2 text-sm font-extrabold">
          <HugeiconsIcon icon={File01Icon} size={18} strokeWidth={2.2} />
          jobradar.config.json
        </h2>
        <span
          className={cn(
            'rounded-full border border-ink px-2.5 py-0.5 text-xs font-bold',
            badge.filled && 'bg-ink text-accent',
          )}
        >
          {badge.text}
        </span>
      </div>

      <div className="min-h-0 flex-1 overflow-auto px-5 py-4 text-[13px] leading-6 font-semibold">
        {lines.map((line, index) => (
          <JsonLine key={index} line={line} />
        ))}
      </div>

      <p className="border-t border-ink/20 px-5 py-3 text-xs font-semibold">
        Sources, companies and custom sources in the file are left as they are.
      </p>
    </aside>
  );
}
