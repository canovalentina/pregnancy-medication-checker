import { useState, useEffect } from 'react';
import { Header } from './Header';
import { LoginForm } from './LoginForm';
import { ProviderApp } from './ProviderApp';
import { PatientApp } from './PatientApp';
import { getUser, logout as authLogout, isAuthenticated } from '../utils/auth';
import type { User } from '../types/auth';

export function HomePage() {
  const [user, setUser] = useState<User | null>(null);

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
        {user.role === 'provider' ? (
          <ProviderApp />
        ) : (
          <PatientApp />
        )}
      </div>
    );
  }

  return (
    <div className="home-page">
      <header className="home-header">
        <h1 className="app-title">Pregnancy Medication Checker</h1>
        <p className="app-subtitle">
          Safely check medication interactions during pregnancy using FHIR standards
        </p>
      </header>

      <div className="home-content">
        <div className="main-section">
          <LoginForm onLogin={handleLogin} />
        </div>
      </div>
    </div>
  );
}

