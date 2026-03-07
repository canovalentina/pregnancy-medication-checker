import { useState, useEffect } from 'react';
import { Header } from './Header';
import { LoginForm } from './LoginForm';
import { ProviderApp } from './ProviderApp';
import { PatientApp } from './PatientApp';
import { getUser, logout as authLogout, isAuthenticated } from '../utils/auth';
import type { User } from '../types/auth';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

function useBackendReady() {
  const [ready, setReady] = useState<boolean | null>(null);
  const [gaveUp, setGaveUp] = useState(false);

  useEffect(() => {
    let cancelled = false;
    let attempts = 0;
    const maxAttempts = 18;
    const intervalMs = 5000;

    const check = async () => {
      if (cancelled) return;
      try {
        const res = await fetch(`${API_BASE_URL}/api/health`, {
          method: 'GET',
        });
        if (res.ok) {
          if (!cancelled) setReady(true);
          return;
        }
      } catch {
        // ignore
      }
      attempts += 1;
      if (attempts >= maxAttempts) {
        if (!cancelled) {
          setReady(true);
          setGaveUp(true);
        }
        return;
      }
      if (!cancelled) setTimeout(check, intervalMs);
    };

    check();
    return () => {
      cancelled = true;
    };
  }, []);

  return { ready, gaveUp };
}

export function HomePage() {
  const [user, setUser] = useState<User | null>(null);
  const { ready, gaveUp } = useBackendReady();

  useEffect(() => {
    // Check if user is already logged in
    if (isAuthenticated()) {
      const storedUser = getUser();
      if (storedUser) {
        setUser(storedUser);
      }
    }
  }, []);

  const handleLogin = (loggedInUser: User) => {
    setUser(loggedInUser);
  };

  const handleLogout = () => {
    authLogout();
    setUser(null);
  };

  if (user) {
    return (
      <div className="app-container">
        <Header isLoggedIn={true} user={user} onLogout={handleLogout} />
        {user.role === 'provider' ? <ProviderApp /> : <PatientApp />}
      </div>
    );
  }

  if (ready === null) {
    return (
      <div className="home-page">
        <header className="home-header">
          <h1 className="app-title">Pregnancy Medication Checker</h1>
          <p className="app-subtitle">
            Safely check medication interactions during pregnancy using FHIR
            standards
          </p>
        </header>
        <div className="home-content">
          <div className="main-section backend-wait">
            <div className="loading-spinner-large" />
            <p className="backend-wait-title">Connecting to server…</p>
            <p className="backend-wait-hint">
              The server may take up to a minute to start after periods of
              inactivity.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="home-page">
      <header className="home-header">
        <h1 className="app-title">Pregnancy Medication Checker</h1>
        <p className="app-subtitle">
          Safely check medication interactions during pregnancy using FHIR
          standards
        </p>
      </header>

      <div className="home-content">
        {gaveUp && (
          <p className="backend-slow-hint">
            Server is taking longer than usual. You can try logging in, it may
            respond in another minute.
          </p>
        )}
        <div className="main-section">
          <LoginForm onLogin={handleLogin} />
        </div>
      </div>
    </div>
  );
}
