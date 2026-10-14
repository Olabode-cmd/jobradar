import { useId } from 'react';

import { cn } from '../../lib/class-names';

interface ToggleFieldProps {
  label: string;
  description: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}

export function ToggleField({ label, description, checked, onChange }: ToggleFieldProps) {
  const id = useId();
  const labelId = `${id}-label`;
  const descriptionId = `${id}-description`;

  return (
    <div className="flex items-start justify-between gap-6">
      <div>
        <span id={labelId} className="block text-sm font-bold">
          {label}
        </span>
        <p id={descriptionId} className="mt-1 text-sm text-forest-300">
          {description}
        </p>
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        aria-labelledby={labelId}
        aria-describedby={descriptionId}
        onClick={() => onChange(!checked)}
        className={cn(
          'relative mt-0.5 h-7 w-12 shrink-0 rounded-full border transition-colors',
          checked ? 'border-lemon-400 bg-lemon-400' : 'border-forest-600 bg-forest-800',
        )}
      >
        <span
          className={cn(
            'absolute top-0.5 left-0.5 size-[22px] rounded-full transition-transform motion-reduce:transition-none',
            checked ? 'translate-x-5 bg-ink' : 'bg-forest-300',
          )}
        />
      </button>
    </div>
  );
}
