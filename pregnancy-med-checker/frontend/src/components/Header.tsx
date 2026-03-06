import { FHIRStatus } from './FHIRStatus';
import type { User } from '../types/auth';

interface HeaderProps {
  isLoggedIn: boolean;
  user?: User;
  onLogout?: () => void;
}

export function Header({ isLoggedIn, user, onLogout }: HeaderProps) {
  return (
    <header className="app-header">
      <div className="header-content">
        <div className="header-left">
          <h1 className="header-title">Pregnancy Medication Checker</h1>
          {user && (
            <div className="user-info">
              <span className="user-name">{user.full_name}</span>
              <span className="user-role">{user.role === 'provider' ? 'Provider' : 'Patient'}</span>
            </div>
          )}
        </div>
        <div className="header-right">
          <FHIRStatus compact={true} />
          {isLoggedIn && (
            <button onClick={onLogout} className="logout-button">
              Logout
            </button>
          )}
        </div>
      </div>
    </header>
  );
}

