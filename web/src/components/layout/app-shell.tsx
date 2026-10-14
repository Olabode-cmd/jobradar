import { Outlet } from 'react-router-dom';

import { AppHeader } from './app-header';

export function AppShell() {
  return (
    <div className="min-h-screen">
      <AppHeader />
      <main className="mx-auto max-w-7xl px-6 py-10">
        <Outlet />
      </main>
    </div>
  );
}
