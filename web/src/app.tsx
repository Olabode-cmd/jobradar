import { BrowserRouter, Route, Routes } from 'react-router-dom';

import { AppShell } from './components/layout/app-shell';
import { CompaniesPage } from './features/companies/companies-page';
import { InboxPage } from './features/inbox/inbox-page';
import { NotFoundPage } from './features/not-found/not-found-page';
import { HomeRedirect } from './features/onboarding/home-redirect';
import { OnboardingPage } from './features/onboarding/onboarding-page';
import { ProfilePage } from './features/profile/profile-page';
import { RunsPage } from './features/runs/runs-page';
import { SettingsPage } from './features/settings/settings-page';
import { SourcesPage } from './features/sources/sources-page';

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<HomeRedirect />} />
          <Route path="welcome" element={<OnboardingPage />} />
          <Route path="inbox" element={<InboxPage />} />
          <Route path="runs" element={<RunsPage />} />
          <Route path="sources" element={<SourcesPage />} />
          <Route path="companies" element={<CompaniesPage />} />
          <Route path="profile" element={<ProfilePage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
