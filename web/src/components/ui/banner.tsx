import { AlertCircleIcon, InformationCircleIcon } from '@hugeicons/core-free-icons';
import { HugeiconsIcon } from '@hugeicons/react';
import type { ReactNode } from 'react';

import { cn } from '../../lib/class-names';

type BannerTone = 'error' | 'info';

interface BannerProps {
  tone: BannerTone;
  title: string;
  children?: ReactNode;
  action?: ReactNode;
}

const TONE_CLASSES: Record<BannerTone, string> = {
  error: 'border-danger/60 text-danger',
  info: 'border-border-dim text-success',
};

export function Banner({ tone, title, children, action }: BannerProps) {
  return (
    <div
      role={tone === 'error' ? 'alert' : 'status'}
      className={cn('flex items-start gap-3 rounded-xl border p-4', TONE_CLASSES[tone])}
    >
      <HugeiconsIcon
        icon={tone === 'error' ? AlertCircleIcon : InformationCircleIcon}
        size={20}
        strokeWidth={2}
        className="mt-0.5 shrink-0"
      />
      <div className="min-w-0 flex-1">
        <p className="text-sm font-bold">{title}</p>
        {children ? <div className="mt-1 text-sm text-body/85">{children}</div> : null}
      </div>
      {action}
    </div>
  );
}
