import { Link } from 'react-router-dom';

export function NotFoundPage() {
  return (
    <div className="max-w-xl">
      <h1 className="text-4xl font-extrabold tracking-tight">Page not found</h1>
      <p className="mt-3 text-muted">That address doesn't match anything in JobRadar.</p>
      <Link
        to="/inbox"
        className="mt-6 inline-flex h-11 items-center rounded-lg bg-accent px-5 text-sm font-bold text-ink transition-colors hover:bg-accent-hover"
      >
        Go to your inbox
      </Link>
    </div>
  );
}
