import type { ReactNode } from 'react';

interface SectionPanelProps {
  title: string;
  description?: string;
  children: ReactNode;
}

export function SectionPanel({ title, description, children }: SectionPanelProps) {
  return (
    <section className="rounded-xl border border-forest-700 bg-forest-900 p-6">
      <h2 className="text-lg font-extrabold tracking-tight">{title}</h2>
      {description ? <p className="mt-1 text-sm text-forest-300">{description}</p> : null}
      <div className="mt-6 space-y-6">{children}</div>
    </section>
  );
}
