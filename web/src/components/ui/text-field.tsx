import { useId, type InputHTMLAttributes } from 'react';

import { cn } from '../../lib/class-names';
import { FIELD_BOX_CLASSES, FieldShell, describedBy, fieldBorder } from './field-shell';

interface TextFieldProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'id' | 'onChange'> {
  label: string;
  value: string;
  onChange: (value: string) => void;
  hint?: string;
  error?: string;
  suffix?: string;
}

export function TextField({
  label,
  value,
  onChange,
  hint,
  error,
  suffix,
  className,
  ...inputProps
}: TextFieldProps) {
  const id = useId();

  return (
    <FieldShell id={id} label={label} hint={hint} error={error}>
      <div
        className={cn(
          FIELD_BOX_CLASSES,
          fieldBorder(Boolean(error)),
          'flex items-center focus-within:border-accent',
        )}
      >
        <input
          id={id}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy(id, hint, error)}
          className={cn(
            'h-11 min-w-0 flex-1 bg-transparent px-3.5 text-base font-medium outline-none',
            'placeholder:text-muted/60',
            className,
          )}
          {...inputProps}
        />
        {suffix ? <span className="pr-3.5 text-sm font-semibold text-muted">{suffix}</span> : null}
      </div>
    </FieldShell>
  );
}
