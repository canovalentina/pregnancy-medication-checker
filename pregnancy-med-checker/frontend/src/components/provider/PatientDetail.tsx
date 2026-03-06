import { useState, useEffect } from 'react';
import { getPatientSummary } from '../../services/fhirApi';
import { getPatientUnreadCount } from '../../services/messagesApi';
import type { PatientSummary, Patient } from '../../types/api';
import { MedicationList } from '../medications/MedicationList';
import { MedicationInteractionAlerts } from '../medications/MedicationInteractionAlerts';
import { FoodInteractionAlerts } from '../diet/FoodInteractionAlerts';
import { PregnancyVisualization } from '../pregnancy/PregnancyVisualization';
import { ProviderNotes } from './ProviderNotes';
import { ProviderMessaging } from './ProviderMessaging';
import './PatientDetail.css';

interface PatientDetailProps {
  patientId: string;
  patient?: Patient;
  onClose?: () => void;
}

export function PatientDetail({ patientId, patient: initialPatient, onClose }: PatientDetailProps) {
  const [summary, setSummary] = useState<PatientSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'medications' | 'conditions' | 'observations' | 'diet' | 'notes' | 'messages'>('overview');
  const [unreadMessageCount, setUnreadMessageCount] = useState(0);

  useEffect(() => {
    loadPatientSummary();
  }, [patientId]);

  useEffect(() => {
    if (patientId) {
      loadUnreadCount();
      const interval = setInterval(loadUnreadCount, 30000); // Poll every 30 seconds
      return () => clearInterval(interval);
    }
  }, [patientId]);

  const loadUnreadCount = async () => {
    try {
      const response = await getPatientUnreadCount(patientId);
      if (response.status === 'success') {
        setUnreadMessageCount(response.data.unread_count);
      }
    } catch (err) {
      // Silently fail for unread count
      console.error('Failed to load unread count:', err);
    }
  };

  const loadPatientSummary = async () => {
    setLoading(true);
    setError(null);
    const response = await getPatientSummary(patientId);
    
    if (response.status === 'success') {
      setSummary(response.data);
    } else {
      setError(response.error || 'Failed to load patient details');
    }
    setLoading(false);
  };

  const patient = summary?.patient || initialPatient;

  if (loading) {
    return (
      <div className="patient-detail">
        <div className="loading-container">
          <div className="loading-spinner-large" />
          <p>Loading patient details...</p>
        </div>
      </div>
    );
  }

  if (error || !patient) {
    return (
      <div className="patient-detail">
        <div className="error-container">
          <h3>Error Loading Patient</h3>
          <p>{error || 'Patient not found'}</p>
          {onClose && (
            <button className="close-button" onClick={onClose}>
              Close
            </button>
          )}
        </div>
      </div>
    );
  }

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return 'N/A';
    try {
      return new Date(dateStr).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      });
    } catch {
      return dateStr;
    }
  };

  const calculateAge = (birthDate?: string) => {
    if (!birthDate) return null;
    try {
      const birth = new Date(birthDate);
      const today = new Date();
      let age = today.getFullYear() - birth.getFullYear();
      const monthDiff = today.getMonth() - birth.getMonth();
      if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
        age--;
      }
      return age;
    } catch {
      return null;
    }
  };

  const age = calculateAge(patient.birth_date);

  return (
    <div className="patient-detail">
      <div className="patient-detail-header">
        <div className="patient-header-info">
          <h2>{patient.name}</h2>
          <div className="patient-meta">
            {patient.birth_date && (
              <span className="meta-item">
                <strong>DOB:</strong> {formatDate(patient.birth_date)}
                {age !== null && ` (Age: ${age})`}
              </span>
            )}
            {patient.gender && (
              <span className="meta-item">
                <strong>Gender:</strong> {patient.gender.charAt(0).toUpperCase() + patient.gender.slice(1)}
              </span>
            )}
            <span className="meta-item">
              <strong>Patient ID:</strong> {patient.id}
            </span>
          </div>
        </div>
        {onClose && (
          <button className="close-button" onClick={onClose}>
            ×
          </button>
        )}
      </div>

      <div className="patient-detail-tabs">
        <button
          className={`tab-button ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button
          className={`tab-button ${activeTab === 'medications' ? 'active' : ''}`}
          onClick={() => setActiveTab('medications')}
        >
          Medications ({summary?.medications.length || 0})
        </button>
        <button
          className={`tab-button ${activeTab === 'conditions' ? 'active' : ''}`}
          onClick={() => setActiveTab('conditions')}
        >
          Conditions ({summary?.conditions.length || 0})
        </button>
        <button
          className={`tab-button ${activeTab === 'observations' ? 'active' : ''}`}
          onClick={() => setActiveTab('observations')}
        >
          Pregnancy Observations ({summary?.observations.length || 0})
        </button>
        <button
          className={`tab-button ${activeTab === 'diet' ? 'active' : ''}`}
          onClick={() => setActiveTab('diet')}
        >
          Diet & Food Interactions
        </button>
        <button
          className={`tab-button ${activeTab === 'notes' ? 'active' : ''}`}
          onClick={() => setActiveTab('notes')}
        >
          Notes
        </button>
        <button
          className={`tab-button ${activeTab === 'messages' ? 'active' : ''}`}
          onClick={() => setActiveTab('messages')}
        >
          Messages
          {unreadMessageCount > 0 && (
            <span className="unread-count-badge">{unreadMessageCount}</span>
          )}
        </button>
      </div>

      <div className="patient-detail-content">
        {activeTab === 'overview' && (
          <div className="overview-tab">
            <div className="info-section">
              <h3>Patient Information</h3>
              <div className="info-grid">
                <div className="info-item">
                  <label>Full Name</label>
                  <div>{patient.name}</div>
                </div>
                <div className="info-item">
                  <label>Date of Birth</label>
                  <div>{formatDate(patient.birth_date)}</div>
                </div>
                <div className="info-item">
                  <label>Age</label>
                  <div>{age !== null ? `${age} years` : 'N/A'}</div>
                </div>
                <div className="info-item">
                  <label>Gender</label>
                  <div>{patient.gender ? patient.gender.charAt(0).toUpperCase() + patient.gender.slice(1) : 'N/A'}</div>
                </div>
                <div className="info-item">
                  <label>Patient ID</label>
                  <div className="patient-id">{patient.id}</div>
                </div>
              </div>
            </div>

            <div className="summary-cards">
              <div className="summary-card">
                <div className="summary-card-icon">💊</div>
                <div className="summary-card-content">
                  <h4>Medications</h4>
                  <p className="summary-count">{summary?.medications.length || 0}</p>
                  <p className="summary-label">Active medications</p>
                </div>
              </div>
              <div className="summary-card">
                <div className="summary-card-icon">🏥</div>
                <div className="summary-card-content">
                  <h4>Conditions</h4>
                  <p className="summary-count">{summary?.conditions.length || 0}</p>
                  <p className="summary-label">Diagnosed conditions</p>
                </div>
              </div>
              <div className="summary-card">
                <div className="summary-card-icon">🤰</div>
                <div className="summary-card-content">
                  <h4>Pregnancy Data</h4>
                  <p className="summary-count">{summary?.observations.length || 0}</p>
                  <p className="summary-label">Observations</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'medications' && (
          <div className="medications-tab">
            <MedicationList
              medications={summary?.medications || []}
              title="Patient Medications"
              emptyMessage="No medications found for this patient."
              showSafetyInfo={true}
            />
            {summary?.medications && summary.medications.length > 0 && (
              <div style={{ marginTop: '2rem' }}>
                <MedicationInteractionAlerts medications={summary.medications} isProviderView={true} />
              </div>
            )}
          </div>
        )}

        {activeTab === 'conditions' && (
          <div className="conditions-tab">
            <h3>Patient Conditions</h3>
            {summary?.conditions && summary.conditions.length > 0 ? (
              <div className="conditions-list">
                {summary.conditions.map((condition, index) => {
                  const conditionName = condition.code?.text || condition.code?.coding?.[0]?.display || `Condition ${index + 1}`;
                  const status = condition.clinicalStatus?.coding?.[0]?.code || 'unknown';
                  const severity = condition.severity?.coding?.[0]?.display;
                  
                  return (
                    <div key={condition.id || index} className="condition-item">
                      <div className="condition-header">
                        <h4>{conditionName}</h4>
                        <span className={`status-badge status-${status}`}>{status}</span>
                      </div>
                      <div className="condition-details">
                        {condition.onsetDateTime && (
                          <div><strong>Onset:</strong> {formatDate(condition.onsetDateTime)}</div>
                        )}
                        {severity && <div><strong>Severity:</strong> {severity}</div>}
                        {condition.category && condition.category.length > 0 && (
                          <div>
                            <strong>Category:</strong>{' '}
                            {condition.category.map((cat: any) => cat.coding?.[0]?.display || cat.text).join(', ')}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="empty-state">No conditions found for this patient.</div>
            )}
          </div>
        )}

        {activeTab === 'observations' && (
          <div className="observations-tab">
            <h3>Pregnancy-Related Observations</h3>
            
            {/* Pregnancy Visualization Component */}
            {summary && (
              <div style={{ marginBottom: '2rem' }}>
                <PregnancyVisualization summary={summary} />
              </div>
            )}
            
            {/* Detailed Observations List */}
            {summary?.observations && summary.observations.length > 0 ? (
              <div className="observations-list">
                <h4 style={{ marginBottom: '1rem', color: '#666' }}>Detailed Observations</h4>
                {summary.observations.map((obs, index) => {
                  const observationName = obs.code?.text || obs.code?.coding?.[0]?.display || `Observation ${index + 1}`;
                  const value = obs.valueQuantity?.value || obs.valueString || obs.valueCodeableConcept?.text || 'N/A';
                  const unit = obs.valueQuantity?.unit || '';
                  
                  return (
                    <div key={obs.id || index} className="observation-item">
                      <div className="observation-header">
                        <h4>{observationName}</h4>
                        <span className="observation-value">
                          {value} {unit}
                        </span>
                      </div>
                      <div className="observation-details">
                        {obs.effectiveDateTime && (
                          <div><strong>Date:</strong> {formatDate(obs.effectiveDateTime)}</div>
                        )}
                        {obs.status && <div><strong>Status:</strong> {obs.status}</div>}
                        {obs.category && obs.category.length > 0 && (
                          <div>
                            <strong>Category:</strong>{' '}
                            {obs.category.map((cat: any) => cat.coding?.[0]?.display || cat.text).join(', ')}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="empty-state">No pregnancy observations found for this patient.</div>
            )}
          </div>
        )}

        {activeTab === 'diet' && (
          <div className="diet-tab">
            <h3>Diet & Food Interactions</h3>
            <p style={{ marginBottom: '1.5rem', color: '#666' }}>
              Review food interactions for this patient's medications. 
              Please inform the patient about any foods they should avoid.
            </p>
            {summary?.medications && summary.medications.length > 0 ? (
              <FoodInteractionAlerts medications={summary.medications} isProviderView={true} />
            ) : (
              <div className="empty-state">
                No medications found. Food interactions will be displayed here when the patient has medications.
              </div>
            )}
          </div>
        )}

        {activeTab === 'notes' && (
          <div className="notes-tab">
            <ProviderNotes patientId={patientId} />
          </div>
        )}

        {activeTab === 'messages' && (
          <div className="messages-tab">
            <ProviderMessaging patientId={patientId} patientName={patient?.name} />
          </div>
        )}
      </div>
    </div>
  );
}

