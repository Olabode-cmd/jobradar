import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';

import { AppShell } from './components/layout/app-shell';
import { NotFoundPage } from './features/not-found/not-found-page';
import { ProfilePage } from './features/profile/profile-page';

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<Navigate to="/profile" replace />} />
          <Route path="profile" element={<ProfilePage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
