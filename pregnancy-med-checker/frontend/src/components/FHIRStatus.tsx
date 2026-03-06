import { useEffect, useState } from 'react';

interface FHIRStatusData {
  status: 'connected' | 'disconnected' | 'error';
  server: string;
  fhir_version?: string;
  server_name?: string;
  timestamp?: string;
}

interface FHIRStatusProps {
  compact?: boolean;
}

// Use proxy in development, or full URL if VITE_API_BASE_URL is set
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export function FHIRStatus({ compact = false }: FHIRStatusProps) {
  const [status, setStatus] = useState<FHIRStatusData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const checkFHIRStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      const token = localStorage.getItem('pmc_access_token');
      const headers: HeadersInit = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      const response = await fetch(`${API_BASE_URL}/api/fhir/status`, { headers });
      if (!response.ok) {
        throw new Error(`Failed to fetch FHIR status: ${response.statusText}`);
      }
      const data = await response.json();
      setStatus(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      setStatus({
        status: 'error',
        server: API_BASE_URL || 'http://localhost:8000',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkFHIRStatus();
    // Refresh status every 30 seconds
    const interval = setInterval(checkFHIRStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = () => {
    if (loading) return '#666';
    switch (status?.status) {
      case 'connected':
        return '#22c55e';
      case 'disconnected':
        return '#ef4444';
      case 'error':
        return '#ef4444';
      default:
        return '#666';
    }
  };

  const getStatusText = () => {
    if (loading) return 'Checking...';
    switch (status?.status) {
      case 'connected':
        return 'Connected';
      case 'disconnected':
        return 'Disconnected';
      case 'error':
        return 'Error';
      default:
        return 'Unknown';
    }
  };

  if (compact) {
    return (
      <div className="fhir-status-compact">
        <button 
          onClick={checkFHIRStatus} 
          disabled={loading}
          className="refresh-btn-compact"
          aria-label="Refresh connection status"
          title="Refresh FHIR connection status"
        >
          {loading ? '⏳' : '🔄'}
        </button>
        <div className="status-indicator-compact">
          <span 
            className="status-dot-compact" 
            style={{ backgroundColor: getStatusColor() }}
            title={status?.server_name || 'FHIR Connection'}
          ></span>
          <span className="status-text-compact">{getStatusText()}</span>
        </div>
        {error && (
          <span className="error-indicator" title={error}>⚠️</span>
        )}
      </div>
    );
  }

  return (
    <div className="fhir-status">
      <div className="fhir-status-header">
        <h3>FHIR Database Connection</h3>
        <button 
          onClick={checkFHIRStatus} 
          disabled={loading}
          className="refresh-btn"
          aria-label="Refresh connection status"
        >
          {loading ? '⏳' : '🔄'}
        </button>
      </div>
      <div className="fhir-status-content">
        <div className="status-indicator">
          <span 
            className="status-dot" 
            style={{ backgroundColor: getStatusColor() }}
          ></span>
          <span className="status-text">{getStatusText()}</span>
        </div>
        {status && (
          <div className="status-details">
            {status.server_name && (
              <p><strong>Server:</strong> {status.server_name}</p>
            )}
            {status.fhir_version && (
              <p><strong>FHIR Version:</strong> {status.fhir_version}</p>
            )}
            <p><strong>URL:</strong> {status.server}</p>
            {error && (
              <p className="error-message">Error: {error}</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

