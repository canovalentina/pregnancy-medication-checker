import { useState } from 'react';
import { login } from '../utils/auth';
import type { User } from '../types/auth';

interface LoginFormProps {
  onLogin?: (user: User) => void;
}

export function LoginForm({ onLogin }: LoginFormProps) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const response = await login(username, password);
      onLogin?.(response.user);
      setError(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Login failed';
      const isNetworkError =
        err instanceof TypeError ||
        message.toLowerCase().includes('failed to fetch') ||
        message.toLowerCase().includes('network');
      setError(
        isNetworkError
          ? 'Server may be starting up. Please wait a moment and try again.'
          : message,
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className="login-form" onSubmit={handleSubmit}>
      <h2>Login</h2>
      <div className="form-group">
        <label htmlFor="username">Username</label>
        <input
          id="username"
          type="text"
          value={username}
          onChange={e => setUsername(e.target.value)}
          placeholder="Enter your username"
          required
          disabled={loading}
        />
      </div>
      <div className="form-group">
        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={e => setPassword(e.target.value)}
          placeholder="Enter your password"
          required
          disabled={loading}
        />
      </div>
      {error && <div className="error-message">{error}</div>}
      <button
        type="submit"
        className="login-button"
        disabled={loading || !username || !password}
      >
        {loading ? 'Logging in...' : 'Login'}
      </button>
    </form>
  );
}
