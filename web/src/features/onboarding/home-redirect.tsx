import { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';

import { fetchConfig } from '../../api/config-api';

/** First visit goes to the setup questions; once a config file exists it goes to the inbox. */
export function HomeRedirect() {
  const [target, setTarget] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchConfig().then(
      (snapshot) => !cancelled && setTarget(snapshot.exists ? '/inbox' : '/welcome'),
      // If the API is unreachable the inbox shows the real error, which is more useful than a blank page.
      () => !cancelled && setTarget('/inbox'),
    );
    return () => {
      cancelled = true;
    };
  }, []);

  return target ? <Navigate to={target} replace /> : null;
}
