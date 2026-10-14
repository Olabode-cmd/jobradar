import { cn } from '../../lib/class-names';

interface SwitchProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
  'aria-label'?: string;
  'aria-labelledby'?: string;
  'aria-describedby'?: string;
}

export function Switch({ checked, onChange, disabled, ...aria }: SwitchProps) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={cn(
        'relative h-7 w-12 shrink-0 rounded-full border transition-colors disabled:cursor-not-allowed disabled:opacity-50',
        checked ? 'border-lemon-400 bg-lemon-400' : 'border-forest-600 bg-forest-800',
      )}
      {...aria}
    >
      <span
        className={cn(
          'absolute top-0.5 left-0.5 size-[22px] rounded-full transition-transform motion-reduce:transition-none',
          checked ? 'translate-x-5 bg-ink' : 'bg-forest-300',
        )}
      />
    </button>
  );
}
