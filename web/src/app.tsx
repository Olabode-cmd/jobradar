import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';

import { AppShell } from './components/layout/app-shell';
import { InboxPage } from './features/inbox/inbox-page';
import { NotFoundPage } from './features/not-found/not-found-page';
import { ProfilePage } from './features/profile/profile-page';
import { RunsPage } from './features/runs/runs-page';

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<Navigate to="/inbox" replace />} />
          <Route path="inbox" element={<InboxPage />} />
          <Route path="runs" element={<RunsPage />} />
          <Route path="profile" element={<ProfilePage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
