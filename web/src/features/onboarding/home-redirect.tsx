import { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';

import { fetchConfig } from '../../api/config-api';

/** Until a job title is saved, home goes to the setup questions; nothing is fetched before then. */
export function HomeRedirect() {
  const [target, setTarget] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchConfig().then(
      (snapshot) => {
        if (cancelled) return;
        const ready = snapshot.exists && snapshot.editable.profile.role.trim().length > 0;
        setTarget(ready ? '/inbox' : '/welcome');
      },
      // If the API is unreachable the inbox shows the real error, which is more useful than a blank page.
      () => !cancelled && setTarget('/inbox'),
    );
    return () => {
      cancelled = true;
    };
  }, []);

  return target ? <Navigate to={target} replace /> : null;
}
