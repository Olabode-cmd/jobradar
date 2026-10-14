import { cn } from '../../lib/class-names';

interface ChoiceOption<T extends string> {
  value: T;
  label: string;
  hint?: string;
}

interface ChoiceGroupProps<T extends string> {
  legend: string;
  value: T;
  options: ReadonlyArray<ChoiceOption<T>>;
  onChange: (value: T) => void;
}

export function ChoiceGroup<T extends string>({
  legend,
  value,
  options,
  onChange,
}: ChoiceGroupProps<T>) {
  return (
    <div role="radiogroup" aria-label={legend} className="grid gap-3">
      {options.map((option) => {
        const selected = option.value === value;
        return (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={selected}
            onClick={() => onChange(option.value)}
            className={cn(
              'rounded-xl border p-4 text-left transition-colors',
              selected
                ? 'border-lemon-400 bg-forest-800'
                : 'border-forest-700 hover:border-forest-600',
            )}
          >
            <span className="flex items-center gap-3">
              <span
                aria-hidden="true"
                className={cn(
                  'size-4 shrink-0 rounded-full border-2',
                  selected ? 'border-lemon-400 bg-lemon-400' : 'border-forest-600',
                )}
              />
              <span className="font-bold">{option.label}</span>
            </span>
            {option.hint ? (
              <span className="mt-1 ml-7 block text-sm text-forest-300">{option.hint}</span>
            ) : null}
          </button>
        );
      })}
    </div>
  );
}
