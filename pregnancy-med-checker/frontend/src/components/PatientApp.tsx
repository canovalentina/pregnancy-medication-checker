import { useState, useEffect } from 'react';
import { getUser } from '../utils/auth';
import { searchPatients, getPatientSummary } from '../services/fhirApi';
import { MedicationList } from './medications/MedicationList';
import { MedicationReminders } from './medications/MedicationReminders';
import { MedicationInteractionAlerts } from './medications/MedicationInteractionAlerts';
import { FoodInteractionAlerts } from './diet/FoodInteractionAlerts';
import { PregnancyVisualization } from './pregnancy/PregnancyVisualization';
import { PatientNotes } from './patient/PatientNotes';
import { PatientMessaging } from './patient/PatientMessaging';
import { getPatientUnreadCount } from '../services/messagesApi';
import type { Patient, PatientSummary } from '../types/api';
import './PatientApp.css';

export function PatientApp() {
  const [patient, setPatient] = useState<Patient | null>(null);
  const [summary, setSummary] = useState<PatientSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'medications' | 'observations' | 'conditions' | 'diet' | 'notes' | 'messages'>('overview');
  const [unreadMessageCount, setUnreadMessageCount] = useState(0);

  // Try to find patient record on mount using their name
  useEffect(() => {
    loadPatientRecord();
  }, []);

  // Load unread message count
  useEffect(() => {
    if (patient?.id) {
      loadUnreadCount();
      const interval = setInterval(loadUnreadCount, 30000); // Poll every 30 seconds
      return () => clearInterval(interval);
    }
  }, [patient?.id]);

  const loadUnreadCount = async () => {
    if (!patient?.id) return;
    try {
      const response = await getPatientUnreadCount(patient.id);
      if (response.status === 'success') {
        setUnreadMessageCount(response.data.unread_count);
      }
    } catch (err) {
      // Silently fail for unread count
      console.error('Failed to load unread count:', err);
    }
  };

  const loadPatientRecord = async () => {
    const user = getUser();
    if (!user) return;

    setLoading(true);
    setError(null);

    try {
      // Helper function to check if a patient has pregnancy data
      const patientHasPregnancyData = (summary: PatientSummary): boolean => {
        return (
          (summary.pregnancyHistory?.pregnancies && summary.pregnancyHistory.pregnancies.length > 0) ||
          (summary.observations && summary.observations.length > 0) ||
          (summary.medications && summary.medications.length > 0) ||
          (summary.conditions && summary.conditions.length > 0)
        );
      };

      // Helper function to find exact name match
      const findExactNameMatch = (patients: Patient[], fullName: string): Patient | null => {
        const normalizedFullName = fullName.toLowerCase().trim();
        return patients.find(p => {
          const patientName = (p.name || '').toLowerCase().trim();
          return patientName === normalizedFullName;
        }) || null;
      };

      // Search for patient by exact name match first (only ingested patients)
      let searchResponse = await searchPatients({ 
        name: user.full_name,
        only_ingested_patients: true 
      });
      
      console.log('Search results (only_ingested_patients=true):', searchResponse);
      
      let foundPatient: Patient | null = null;
      
      // If we have results, prioritize patients with pregnancy data
      if (searchResponse.status === 'success' && searchResponse.data.length > 0) {
        console.log(`Found ${searchResponse.data.length} patient(s) with name "${user.full_name}" (ingested only):`, 
          searchResponse.data.map(p => ({ id: p.id, name: p.name, birth_date: p.birth_date })));
        
        // First, try to find exact name match with pregnancy data
        const exactMatch = findExactNameMatch(searchResponse.data, user.full_name);
        if (exactMatch) {
          // Check if exact match has pregnancy data
          const summaryResponse = await getPatientSummary(exactMatch.id);
          if (summaryResponse.status === 'success' && patientHasPregnancyData(summaryResponse.data)) {
            foundPatient = exactMatch;
            console.log('Selected exact match with pregnancy data:', { id: exactMatch.id, name: exactMatch.name, birth_date: exactMatch.birth_date });
          } else {
            console.log('Exact match found but no pregnancy data, checking other patients...');
          }
        }
        
        // If exact match doesn't have data, try all patients to find one with pregnancy data
        if (!foundPatient) {
          for (const candidate of searchResponse.data) {
            // Skip if this is the exact match we already checked
            if (exactMatch && candidate.id === exactMatch.id) continue;
            
            const summaryResponse = await getPatientSummary(candidate.id);
            if (summaryResponse.status === 'success' && patientHasPregnancyData(summaryResponse.data)) {
              foundPatient = candidate;
              console.log('Selected patient with pregnancy data:', { id: candidate.id, name: candidate.name, birth_date: candidate.birth_date });
              break;
            }
          }
        }
        
        // If still no patient with data, use exact match or first patient
        if (!foundPatient) {
          if (exactMatch) {
            foundPatient = exactMatch;
            console.log('Selected exact match (no pregnancy data found in any patient):', { id: exactMatch.id, name: exactMatch.name, birth_date: exactMatch.birth_date });
          } else {
            foundPatient = searchResponse.data[0];
            console.log('Selected first match (no exact match, no pregnancy data):', { id: foundPatient.id, name: foundPatient.name, birth_date: foundPatient.birth_date });
          }
        }
      }
      
      // If still no results, try searching with just the first name (still only ingested patients)
      if (!foundPatient) {
        const nameParts = user.full_name.trim().split(/\s+/);
        if (nameParts.length > 0) {
          searchResponse = await searchPatients({ 
            name: nameParts[0],  // First name
            gender: 'female',     // More likely to have pregnancy data
            only_ingested_patients: true 
          });
          if (searchResponse.status === 'success' && searchResponse.data.length > 0) {
            // Try to find exact match first
            const exactMatch = findExactNameMatch(searchResponse.data, user.full_name);
            if (exactMatch) {
              // Check if exact match has pregnancy data
              const summaryResponse = await getPatientSummary(exactMatch.id);
              if (summaryResponse.status === 'success' && patientHasPregnancyData(summaryResponse.data)) {
                foundPatient = exactMatch;
              } else {
                // Try other patients
                for (const candidate of searchResponse.data) {
                  if (candidate.id === exactMatch.id) continue;
                  const candidateSummary = await getPatientSummary(candidate.id);
                  if (candidateSummary.status === 'success' && patientHasPregnancyData(candidateSummary.data)) {
                    foundPatient = candidate;
                    break;
                  }
                }
                // If no patient with data found, use exact match
                if (!foundPatient) {
                  foundPatient = exactMatch;
                }
              }
            } else {
              // No exact match, try to find any patient with pregnancy data
              for (const candidate of searchResponse.data) {
                const candidateSummary = await getPatientSummary(candidate.id);
                if (candidateSummary.status === 'success' && patientHasPregnancyData(candidateSummary.data)) {
                  foundPatient = candidate;
                  break;
                }
              }
              // If no patient with data found, use first patient
              if (!foundPatient) {
                foundPatient = searchResponse.data[0];
              }
            }
          }
        }
      }
      
      // If still no results, try with just the last name
      if (!foundPatient) {
        const nameParts = user.full_name.trim().split(/\s+/);
        if (nameParts.length > 1) {
          searchResponse = await searchPatients({ 
            name: nameParts[nameParts.length - 1],  // Last name
            gender: 'female',
            only_ingested_patients: true 
          });
          if (searchResponse.status === 'success' && searchResponse.data.length > 0) {
            // Try to find exact match first
            const exactMatch = findExactNameMatch(searchResponse.data, user.full_name);
            if (exactMatch) {
              foundPatient = exactMatch;
            } else {
              // If multiple patients match, try to find one with pregnancy data
              for (const candidate of searchResponse.data) {
                const summaryResponse = await getPatientSummary(candidate.id);
                if (summaryResponse.status === 'success' && patientHasPregnancyData(summaryResponse.data)) {
                  foundPatient = candidate;
                  setPatient(candidate);
                  setSummary(summaryResponse.data);
                  setLoading(false);
                  return;
                }
              }
              // If none have pregnancy data, use first match
              foundPatient = searchResponse.data[0];
            }
          }
        }
      }
      
      if (foundPatient) {
        console.log('Found patient:', {
          id: foundPatient.id,
          name: foundPatient.name,
          birth_date: foundPatient.birth_date,
          gender: foundPatient.gender
        });
        
        // Verify this is a reasonable patient (not a child)
        if (foundPatient.birth_date) {
          try {
            const birth = new Date(foundPatient.birth_date);
            const today = new Date();
            let age = today.getFullYear() - birth.getFullYear();
            const monthDiff = today.getMonth() - birth.getMonth();
            if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
              age--;
            }
            if (age < 13) {
              console.warn(`Patient ${foundPatient.id} has unrealistic age ${age} years. Skipping.`);
              // Try to find another patient with pregnancy data
              if (searchResponse.status === 'success' && searchResponse.data.length > 1) {
                for (const candidate of searchResponse.data.slice(1)) {
                  if (candidate.birth_date) {
                    try {
                      const candidateBirth = new Date(candidate.birth_date);
                      let candidateAge = today.getFullYear() - candidateBirth.getFullYear();
                      const candidateMonthDiff = today.getMonth() - candidateBirth.getMonth();
                      if (candidateMonthDiff < 0 || (candidateMonthDiff === 0 && today.getDate() < candidateBirth.getDate())) {
                        candidateAge--;
                      }
                      if (candidateAge >= 13) {
                        console.log(`Trying alternative patient: ${candidate.id} (age ${candidateAge})`);
                        foundPatient = candidate;
                        break;
                      }
                    } catch {
                      // Skip if date parsing fails
                    }
                  }
                }
              }
              // If still no good patient, show error
              if (foundPatient && foundPatient.birth_date) {
                const finalBirth = new Date(foundPatient.birth_date);
                let finalAge = today.getFullYear() - finalBirth.getFullYear();
                const finalMonthDiff = today.getMonth() - finalBirth.getMonth();
                if (finalMonthDiff < 0 || (finalMonthDiff === 0 && today.getDate() < finalBirth.getDate())) {
                  finalAge--;
                }
                if (finalAge < 13) {
                  setError(`Found patient record but age appears incorrect. Please contact your provider.`);
                  setLoading(false);
                  return;
                }
              }
            }
          } catch {
            // If date parsing fails, continue anyway
          }
        }
        
        setPatient(foundPatient);
        
        // Load patient summary
        const summaryResponse = await getPatientSummary(foundPatient.id);
        if (summaryResponse.status === 'success') {
          setSummary(summaryResponse.data);
          
          // Verify patient has data - if not, show helpful message
          if (!patientHasPregnancyData(summaryResponse.data)) {
            setError(
              `Found patient record for ${foundPatient.name}, ` +
              `but no pregnancy observations, medications, or conditions are available. ` +
              `Please contact your provider to ensure your records are up to date.`
            );
          }
        }
      } else {
        setError('Could not find your patient record. Please contact your provider.');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load patient record');
    } finally {
      setLoading(false);
    }
  };

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

  if (loading) {
    return (
      <div className="main-app">
        <div className="main-content">
          <div className="patient-loading">
            <div className="loading-spinner-large" />
            <p>Loading your patient information...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error && !patient) {
    return (
      <div className="main-app">
        <div className="main-content">
          <h2>Patient Portal</h2>
          <div className="error-container">
            <h3>Unable to Load Your Record</h3>
            <p>{error}</p>
            <button className="retry-button" onClick={loadPatientRecord}>
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  const user = getUser();
  const age = patient ? calculateAge(patient.birth_date) : null;

  return (
    <div className="main-app">
      <div className="main-content">
        <div className="patient-portal-header">
          <div>
            <h2>Welcome, {user?.full_name || 'Patient'}</h2>
            {patient && (
              <p className="patient-subtitle">
                {patient.birth_date && age !== null && `Age: ${age} years`}
                {patient.gender && ` • ${patient.gender.charAt(0).toUpperCase() + patient.gender.slice(1)}`}
              </p>
            )}
          </div>
        </div>

        {patient && (
          <>
            {/* Summary Cards */}
            <div className="patient-summary-cards">
              <div className="summary-card">
                <div className="summary-card-icon">💊</div>
                <div className="summary-card-content">
                  <h4>My Medications</h4>
                  <p className="summary-count">{summary?.medications.length || 0}</p>
                  <p className="summary-label">Active medications</p>
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
              <div className="summary-card">
                <div className="summary-card-icon">🏥</div>
                <div className="summary-card-content">
                  <h4>Conditions</h4>
                  <p className="summary-count">{summary?.conditions.length || 0}</p>
                  <p className="summary-label">Diagnosed conditions</p>
                </div>
              </div>
            </div>

            {/* Tabs */}
            <div className="patient-portal-tabs">
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
                My Medications ({summary?.medications.length || 0})
              </button>
              <button
                className={`tab-button ${activeTab === 'observations' ? 'active' : ''}`}
                onClick={() => setActiveTab('observations')}
              >
                Pregnancy Observations ({summary?.observations.length || 0})
              </button>
              <button
                className={`tab-button ${activeTab === 'conditions' ? 'active' : ''}`}
                onClick={() => setActiveTab('conditions')}
              >
                My Conditions ({summary?.conditions.length || 0})
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
                Provider Notes
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

            {/* Tab Content */}
            <div className="patient-portal-content">
              {activeTab === 'overview' && (
                <div className="overview-tab">
                  <div className="info-section">
                    <h3>My Information</h3>
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
                        <div>
                          {patient.gender
                            ? patient.gender.charAt(0).toUpperCase() + patient.gender.slice(1)
                            : 'N/A'}
                        </div>
                      </div>
                      <div className="info-item">
                        <label>Patient ID</label>
                        <div className="patient-id">{patient.id}</div>
                      </div>
                    </div>
                  </div>

                  <div className="feature-section">
                    <h3>Quick Actions</h3>
                    <div className="quick-actions">
                      <div
                        className="quick-action-card"
                        onClick={() => setActiveTab('medications')}
                      >
                        <div className="quick-action-icon">📋</div>
                        <h4>View Medications</h4>
                        <p>See your current medications and safety information</p>
                      </div>
                      <div
                        className="quick-action-card"
                        onClick={() => setActiveTab('observations')}
                      >
                        <div className="quick-action-icon">📊</div>
                        <h4>Pregnancy Data</h4>
                        <p>Review your pregnancy-related observations</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'medications' && (
                <div className="medications-tab">
                  {summary?.medications && summary.medications.length > 0 && (
                    <>
                      <MedicationInteractionAlerts medications={summary.medications} />
                      <MedicationReminders medications={summary.medications} />
                    </>
                  )}
                  <MedicationList
                    medications={summary?.medications || []}
                    title="My Medications"
                    emptyMessage="You don't have any medications on record."
                    showSafetyInfo={true}
                  />
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
                        const observationName =
                          obs.code?.text ||
                          obs.code?.coding?.[0]?.display ||
                          `Observation ${index + 1}`;
                        const value =
                          obs.valueQuantity?.value ||
                          obs.valueString ||
                          obs.valueCodeableConcept?.text ||
                          'N/A';
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
                                <div>
                                  <strong>Date:</strong> {formatDate(obs.effectiveDateTime)}
                                </div>
                              )}
                              {obs.status && (
                                <div>
                                  <strong>Status:</strong> {obs.status}
                                </div>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="empty-state">
                      No pregnancy observations found in your record.
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'conditions' && (
                <div className="conditions-tab">
                  <h3>My Conditions</h3>
                  {summary?.conditions && summary.conditions.length > 0 ? (
                    <div className="conditions-list">
                      {summary.conditions.map((condition, index) => {
                        const conditionName =
                          condition.code?.text ||
                          condition.code?.coding?.[0]?.display ||
                          `Condition ${index + 1}`;
                        const status =
                          condition.clinicalStatus?.coding?.[0]?.code || 'unknown';

                        return (
                          <div key={condition.id || index} className="condition-item">
                            <div className="condition-header">
                              <h4>{conditionName}</h4>
                              <span className={`status-badge status-${status}`}>{status}</span>
                            </div>
                            <div className="condition-details">
                              {condition.onsetDateTime && (
                                <div>
                                  <strong>Onset:</strong> {formatDate(condition.onsetDateTime)}
                                </div>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="empty-state">No conditions found in your record.</div>
                  )}
                </div>
              )}

              {activeTab === 'diet' && (
                <div className="diet-tab">
                  <h3>Diet & Food Interactions</h3>
                  <p style={{ marginBottom: '1.5rem', color: '#666' }}>
                    This section shows foods that may interact with your medications. 
                    Please avoid consuming these foods while taking the listed medications.
                  </p>
                  {summary?.medications && summary.medications.length > 0 ? (
                    <FoodInteractionAlerts medications={summary.medications} />
                  ) : (
                    <div className="empty-state">
                      No medications found. Food interactions will be displayed here when you have medications.
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'notes' && patient && (
                <div className="notes-tab">
                  <PatientNotes patientId={patient.id} />
                </div>
              )}

              {activeTab === 'messages' && patient && (
                <div className="messages-tab">
                  <PatientMessaging patientId={patient.id} />
                </div>
              )}
            </div>
          </>
        )}

      </div>
    </div>
  );
}
