import type { ReactNode } from 'react';

import { cn } from '../../lib/class-names';

type BadgeTone = 'neutral' | 'lemon' | 'danger' | 'muted';

const TONE_CLASSES: Record<BadgeTone, string> = {
  neutral: 'bg-forest-700 text-white',
  lemon: 'bg-lemon-400 text-ink',
  danger: 'border border-danger/60 text-danger',
  muted: 'border border-forest-700 text-forest-300',
};

export function Badge({ tone = 'neutral', children }: { tone?: BadgeTone; children: ReactNode }) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-md px-2 py-0.5 text-xs font-bold whitespace-nowrap',
        TONE_CLASSES[tone],
      )}
    >
      {children}
    </span>
  );
}
