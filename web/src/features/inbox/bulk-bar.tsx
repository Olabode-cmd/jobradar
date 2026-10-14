import { Button } from '../../components/ui/button';
import type { JobStatus } from '../../types/job';

interface BulkBarProps {
  count: number;
  onStatus: (status: JobStatus) => void;
  onClear: () => void;
}

export function BulkBar({ count, onStatus, onClear }: BulkBarProps) {
  return (
    <div className="flex flex-wrap items-center gap-3 rounded-xl border border-lemon-400 px-4 py-2.5">
      <p className="mr-auto text-sm font-bold">{count} selected</p>
      <Button variant="ghost" className="h-9 px-4" onClick={() => onStatus('saved')}>
        Save
      </Button>
      <Button variant="ghost" className="h-9 px-4" onClick={() => onStatus('applied')}>
        Mark applied
      </Button>
      <Button variant="ghost" className="h-9 px-4" onClick={() => onStatus('ignored')}>
        Ignore
      </Button>
      <Button variant="ghost" className="h-9 px-4" onClick={onClear}>
        Clear
      </Button>
    </div>
  );
}
