import { Add01Icon, Cancel01Icon } from '@hugeicons/core-free-icons';
import { HugeiconsIcon } from '@hugeicons/react';
import { useId, useState, type KeyboardEvent } from 'react';

import { cn } from '../../lib/class-names';
import { addTerms, removeTerm } from '../../lib/term-list';
import { FIELD_BOX_CLASSES, FieldShell, describedBy, fieldBorder } from './field-shell';

interface TagInputProps {
  label: string;
  value: string[];
  onChange: (value: string[]) => void;
  placeholder?: string;
  hint?: string;
  error?: string;
  suggestions?: readonly string[];
}

export function TagInput({
  label,
  value,
  onChange,
  placeholder,
  hint,
  error,
  suggestions = [],
}: TagInputProps) {
  const id = useId();
  const [pending, setPending] = useState('');

  const commitPending = () => {
    if (!pending.trim()) return;
    onChange(addTerms(value, pending));
    setPending('');
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter' || event.key === ',') {
      event.preventDefault();
      commitPending();
    } else if (event.key === 'Backspace' && !pending) {
      const last = value.at(-1);
      if (last !== undefined) onChange(removeTerm(value, last));
    }
  };

  const unusedSuggestions = suggestions.filter(
    (suggestion) => !value.some((term) => term.toLowerCase() === suggestion.toLowerCase()),
  );

  return (
    <FieldShell id={id} label={label} hint={hint} error={error}>
      <div
        className={cn(
          FIELD_BOX_CLASSES,
          fieldBorder(Boolean(error)),
          'flex flex-wrap items-center gap-2 p-2 focus-within:border-lemon-400',
        )}
      >
        {value.map((term) => (
          <span
            key={term}
            className="inline-flex items-center gap-1 rounded-md bg-forest-700 py-1 pr-1.5 pl-2.5 text-sm font-semibold"
          >
            {term}
            <button
              type="button"
              aria-label={`Remove ${term}`}
              onClick={() => onChange(removeTerm(value, term))}
              className="rounded p-0.5 text-forest-300 transition-colors hover:bg-forest-600 hover:text-white"
            >
              <HugeiconsIcon icon={Cancel01Icon} size={14} strokeWidth={2} />
            </button>
          </span>
        ))}
        <input
          id={id}
          value={pending}
          onChange={(event) => setPending(event.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={commitPending}
          placeholder={value.length === 0 ? placeholder : undefined}
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy(id, hint, error)}
          className="min-w-32 flex-1 bg-transparent px-1.5 py-1 text-base font-medium outline-none placeholder:text-forest-300/60"
        />
      </div>
      {unusedSuggestions.length > 0 ? (
        <div className="mt-2 flex flex-wrap gap-2">
          {unusedSuggestions.map((suggestion) => (
            <button
              key={suggestion}
              type="button"
              onClick={() => onChange(addTerms(value, suggestion))}
              className="inline-flex items-center gap-1 rounded-md border border-dashed border-forest-600 py-1 pr-2.5 pl-1.5 text-sm font-semibold text-forest-300 transition-colors hover:border-forest-300 hover:text-white"
            >
              <HugeiconsIcon icon={Add01Icon} size={14} strokeWidth={2} />
              {suggestion}
            </button>
          ))}
        </div>
      ) : null}
    </FieldShell>
  );
}
