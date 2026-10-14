import type { ButtonHTMLAttributes } from 'react';
import { cn } from '../../lib/class-names';

type ButtonVariant = 'primary' | 'ghost';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
}

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  primary: 'bg-accent text-ink enabled:hover:bg-accent-hover',
  ghost: 'border border-border-dim text-body enabled:hover:border-muted',
};

export function Button({ variant = 'primary', className, type = 'button', ...rest }: ButtonProps) {
  return (
    <button
      type={type}
      className={cn(
        'inline-flex h-11 items-center justify-center gap-2 rounded-lg px-5 text-sm font-bold transition-colors',
        'disabled:cursor-not-allowed disabled:opacity-40',
        VARIANT_CLASSES[variant],
        className,
      )}
      {...rest}
    />
  );
}
