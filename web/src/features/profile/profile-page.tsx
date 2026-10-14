import { Loading03Icon } from '@hugeicons/core-free-icons';
import { HugeiconsIcon } from '@hugeicons/react';

import { Banner } from '../../components/ui/banner';
import { Button } from '../../components/ui/button';
import { useConfig } from '../../hooks/use-config';
import { ProfileEditor } from './profile-editor';

export function ProfilePage() {
  const { state, reload, save } = useConfig();

  return (
    <div>
      <h1 className="text-4xl font-extrabold tracking-tight">Search profile</h1>
      <p className="mt-2 mb-10 max-w-2xl text-muted">
        Tell JobRadar what to look for. Changes are written to your config file, and the command
        line reads the same file.
      </p>

      {state.status === 'loading' ? (
        <p role="status" className="flex items-center gap-3 text-muted">
          <HugeiconsIcon
            icon={Loading03Icon}
            size={20}
            strokeWidth={2.2}
            className="text-accent motion-safe:animate-spin"
          />
          Loading your profile…
        </p>
      ) : null}

      {state.status === 'error' ? (
        <Banner
          tone="error"
          title={
            state.error.kind === 'conflict'
              ? "Your config file can't be read"
              : "Couldn't load your profile"
          }
          action={
            <Button variant="ghost" onClick={reload} className="h-9 px-4">
              Try again
            </Button>
          }
        >
          {state.error.message}
          {state.error.kind === 'conflict'
            ? ' Fix the file by hand, or delete it to start fresh, then try again.'
            : null}
        </Banner>
      ) : null}

      {state.status === 'ready' ? <ProfileEditor snapshot={state.snapshot} save={save} /> : null}
    </div>
  );
}
