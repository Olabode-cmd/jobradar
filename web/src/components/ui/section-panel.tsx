import type { ReactNode } from 'react';

interface SectionPanelProps {
  title: string;
  description?: string;
  children: ReactNode;
}

export function SectionPanel({ title, description, children }: SectionPanelProps) {
  return (
    <section className="rounded-xl border border-border bg-surface p-6">
      <h2 className="text-lg font-extrabold tracking-tight">{title}</h2>
      {description ? <p className="mt-1 text-sm text-muted">{description}</p> : null}
      <div className="mt-6 space-y-6">{children}</div>
    </section>
  );
}
