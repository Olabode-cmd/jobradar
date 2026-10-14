import { Search01Icon } from '@hugeicons/core-free-icons';
import { HugeiconsIcon } from '@hugeicons/react';

import { cn } from '../../lib/class-names';
import type { JobSort } from '../../types/job';

interface InboxFilterBarProps {
  searchText: string;
  onSearchText: (value: string) => void;
  remoteOnly: boolean;
  onRemoteOnly: (value: boolean) => void;
  includeRestricted: boolean;
  onIncludeRestricted: (value: boolean) => void;
  sort: JobSort;
  onSort: (value: JobSort) => void;
}

function Chip({
  pressed,
  onToggle,
  children,
}: {
  pressed: boolean;
  onToggle: () => void;
  children: string;
}) {
  return (
    <button
      type="button"
      aria-pressed={pressed}
      onClick={onToggle}
      className={cn(
        'h-10 rounded-lg border px-3.5 text-sm font-bold transition-colors',
        pressed
          ? 'border-lemon-400 bg-lemon-400 text-ink'
          : 'border-forest-600 text-white hover:border-forest-300',
      )}
    >
      {children}
    </button>
  );
}

export function InboxFilterBar(props: InboxFilterBarProps) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      <label className="relative min-w-56 flex-1">
        <span className="sr-only">Search jobs</span>
        <HugeiconsIcon
          icon={Search01Icon}
          size={18}
          strokeWidth={2}
          className="pointer-events-none absolute top-1/2 left-3.5 -translate-y-1/2 text-forest-300"
        />
        <input
          type="search"
          value={props.searchText}
          onChange={(event) => props.onSearchText(event.target.value)}
          placeholder="Search title or company"
          className="h-10 w-full rounded-lg border border-forest-700 bg-forest-800 pr-3 pl-10 text-sm font-medium outline-none placeholder:text-forest-300/60 hover:border-forest-600 focus:border-lemon-400"
        />
      </label>
      <Chip pressed={props.remoteOnly} onToggle={() => props.onRemoteOnly(!props.remoteOnly)}>
        Remote only
      </Chip>
      <Chip
        pressed={props.includeRestricted}
        onToggle={() => props.onIncludeRestricted(!props.includeRestricted)}
      >
        Show restricted
      </Chip>
      <label className="flex items-center gap-2 text-sm font-bold">
        <span className="text-forest-300">Sort</span>
        <select
          value={props.sort}
          onChange={(event) => props.onSort(event.target.value === 'recent' ? 'recent' : 'score')}
          className="h-10 rounded-lg border border-forest-700 bg-forest-800 px-3 text-sm font-bold outline-none hover:border-forest-600 focus:border-lemon-400"
        >
          <option value="score">Best fit</option>
          <option value="recent">Newest</option>
        </select>
      </label>
    </div>
  );
}
