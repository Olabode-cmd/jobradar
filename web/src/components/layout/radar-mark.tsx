import { cn } from '../../lib/class-names';

interface RadarMarkProps {
  scanning?: boolean;
  className?: string;
}

export function RadarMark({ scanning = false, className }: RadarMarkProps) {
  return (
    <svg viewBox="0 0 32 32" aria-hidden="true" className={cn('size-8', className)}>
      <circle cx="16" cy="16" r="14" fill="none" stroke="currentColor" strokeWidth="1.6" />
      <circle
        cx="16"
        cy="16"
        r="7.5"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.6"
        opacity="0.5"
      />
      <g
        className={cn(
          'origin-center',
          scanning && 'motion-safe:animate-spin [animation-duration:2.4s]',
        )}
      >
        <path d="M16 16 L16 2" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
        <circle cx="23" cy="9" r="2.4" fill="currentColor" />
      </g>
    </svg>
  );
}
