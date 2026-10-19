import { Button } from '../../components/ui/button';

interface PaginationBarProps {
  page: number;
  pageSize: number;
  total: number;
  shown: number;
  busy: boolean;
  onPageChange: (page: number) => void;
}

export function PaginationBar({
  page,
  pageSize,
  total,
  shown,
  busy,
  onPageChange,
}: PaginationBarProps) {
  const pageCount = Math.max(1, Math.ceil(total / pageSize));
  const first = page * pageSize + 1;

  return (
    <nav
      aria-label="Job pages"
      className="mt-4 flex items-center justify-between gap-4 text-sm text-muted"
    >
      <p aria-live="polite">
        {shown === 0 ? 'No jobs on this page' : `${first}–${first + shown - 1} of ${total}`}
      </p>
      {pageCount > 1 ? (
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            className="h-9 px-4"
            onClick={() => onPageChange(page - 1)}
            disabled={busy || page === 0}
          >
            Previous
          </Button>
          <span className="tabular-nums">
            Page {page + 1} of {pageCount}
          </span>
          <Button
            variant="ghost"
            className="h-9 px-4"
            onClick={() => onPageChange(page + 1)}
            disabled={busy || page >= pageCount - 1}
          >
            Next
          </Button>
        </div>
      ) : null}
    </nav>
  );
}
