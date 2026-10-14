import type { ReactNode } from 'react';

interface FieldShellProps {
  id: string;
  label: string;
  hint?: string | undefined;
  error?: string | undefined;
  children: ReactNode;
}

export function describedBy(id: string, hint?: string, error?: string): string | undefined {
  if (error) return `${id}-error`;
  return hint ? `${id}-hint` : undefined;
}

export const FIELD_BOX_CLASSES =
  'rounded-lg border bg-forest-800 transition-colors hover:border-forest-600';

export function fieldBorder(hasError: boolean): string {
  return hasError ? 'border-danger' : 'border-forest-700';
}

export function FieldShell({ id, label, hint, error, children }: FieldShellProps) {
  return (
    <div>
      <label htmlFor={id} className="mb-2 block text-sm font-bold">
        {label}
      </label>
      {children}
      {error ? (
        <p id={`${id}-error`} className="mt-2 text-sm font-semibold text-danger">
          {error}
        </p>
      ) : hint ? (
        <p id={`${id}-hint`} className="mt-2 text-sm text-forest-300">
          {hint}
        </p>
      ) : null}
    </div>
  );
}
