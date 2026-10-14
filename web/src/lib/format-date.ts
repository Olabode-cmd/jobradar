const dateTimeFormat = new Intl.DateTimeFormat(undefined, {
  dateStyle: 'medium',
  timeStyle: 'short',
});

export function formatDateTime(iso: string | null): string {
  if (!iso) return '–';
  const time = Date.parse(iso);
  return Number.isNaN(time) ? '–' : dateTimeFormat.format(time);
}

export function formatDuration(ms: number | null): string {
  if (ms === null) return '–';
  return ms < 1000 ? `${ms}ms` : `${(ms / 1000).toFixed(1)}s`;
}
