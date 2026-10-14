import type { ApiStatus } from '../../hooks/use-api-status';
import { cn } from '../../lib/class-names';

const STATUS_COPY: Record<ApiStatus, string> = {
  checking: 'Checking API',
  online: 'API connected',
  degraded: 'Database problem',
  offline: 'API offline',
};

const DOT_CLASSES: Record<ApiStatus, string> = {
  checking: 'bg-muted motion-safe:animate-pulse',
  online: 'bg-accent',
  degraded: 'bg-danger',
  offline: 'bg-danger',
};

export function ApiStatusPill({ status }: { status: ApiStatus }) {
  return (
    <p
      role="status"
      className="inline-flex items-center gap-2 rounded-full border border-border px-3 py-1.5 text-sm font-semibold"
    >
      <span className={cn('size-2 rounded-full', DOT_CLASSES[status])} aria-hidden="true" />
      {STATUS_COPY[status]}
    </p>
  );
}
