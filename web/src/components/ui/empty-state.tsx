import type { ReactNode } from 'react';

interface EmptyStateProps {
  title: string;
  children?: ReactNode;
  action?: ReactNode;
}

export function EmptyState({ title, children, action }: EmptyStateProps) {
  return (
    <div className="rounded-xl border border-dashed border-forest-600 px-6 py-12 text-center">
      <p className="text-lg font-extrabold">{title}</p>
      {children ? (
        <div className="mx-auto mt-2 max-w-md text-sm text-forest-300">{children}</div>
      ) : null}
      {action ? <div className="mt-6 flex justify-center">{action}</div> : null}
    </div>
  );
}
