import { NavLink } from 'react-router-dom';

import { useApiStatus } from '../../hooks/use-api-status';
import { cn } from '../../lib/class-names';
import { ApiStatusPill } from './api-status-pill';
import { RadarMark } from './radar-mark';

const NAV_ITEMS = [
  { to: '/inbox', label: 'Inbox' },
  { to: '/runs', label: 'Runs' },
  { to: '/profile', label: 'Profile' },
] as const;

export function AppHeader() {
  const status = useApiStatus();

  return (
    <header className="border-b border-forest-700">
      <div className="mx-auto flex h-16 max-w-7xl items-center gap-8 px-6">
        <div className="flex items-center gap-2.5 text-lemon-400">
          <RadarMark scanning={status === 'checking'} />
          <span className="text-xl font-extrabold tracking-tight text-white">JobRadar</span>
        </div>

        <nav aria-label="Main" className="flex h-full flex-1 items-stretch gap-6">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  'flex items-center border-b-2 text-sm font-bold transition-colors',
                  isActive
                    ? 'border-lemon-400 text-white'
                    : 'border-transparent text-forest-300 hover:text-white',
                )
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <ApiStatusPill status={status} />
      </div>
    </header>
  );
}
