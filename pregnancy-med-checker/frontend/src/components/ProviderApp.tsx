import { useState, useEffect } from 'react';
import { DrugSearch } from './medications/DrugSearch';
import { PatientSearch } from './provider/PatientSearch';
import { PatientList } from './provider/PatientList';
import { PatientDetail } from './provider/PatientDetail';
import { getPatientSummary, getIngestedPatientIds } from '../services/fhirApi';
import type { Patient } from '../types/api';

export function ProviderApp() {
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [searchResults, setSearchResults] = useState<Patient[]>([]);
  const [assignedPatients, setAssignedPatients] = useState<Patient[]>([]);
  const [loadingAssigned, setLoadingAssigned] = useState(true);

  // Load assigned patients from ingested-patients API (dynamic; no hardcoded IDs)
  useEffect(() => {
    let cancelled = false;
    let retryCount = 0;
    const maxRetries = 6;
    const retryDelayMs = 5000;

    const loadAssignedPatients = async () => {
      setLoadingAssigned(true);
      try {
        const idsResponse = await getIngestedPatientIds();
        const patientIds: string[] =
          idsResponse.status === 'success' && idsResponse.data?.patient_ids
            ? idsResponse.data.patient_ids
            : [];

        if (cancelled) return;

        if (patientIds.length === 0) {
          if (retryCount < maxRetries) {
            retryCount += 1;
            setTimeout(loadAssignedPatients, retryDelayMs);
          } else {
            setAssignedPatients([]);
            setLoadingAssigned(false);
          }
          return;
        }

        const patients: Patient[] = [];
        for (const patientId of patientIds) {
          if (cancelled) break;
          try {
            const summaryResponse = await getPatientSummary(patientId);
            if (
              summaryResponse.status === 'success' &&
              summaryResponse.data.patient
            ) {
              patients.push(summaryResponse.data.patient);
            }
          } catch (error) {
            console.warn(`Failed to load patient ${patientId}:`, error);
          }
        }
        if (!cancelled) setAssignedPatients(patients);
      } catch (error) {
        console.error('Failed to load assigned patients:', error);
        if (!cancelled && retryCount < maxRetries) {
          retryCount += 1;
          setTimeout(loadAssignedPatients, retryDelayMs);
        }
      } finally {
        if (!cancelled) setLoadingAssigned(false);
      }
    };

    loadAssignedPatients();
    return () => {
      cancelled = true;
    };
  }, []);

  const handlePatientSelect = (patient: Patient) => {
    setSelectedPatient(patient);
  };

  const handleClosePatientDetail = () => {
    setSelectedPatient(null);
  };

  const handleSearchResults = (patients: Patient[]) => {
    setSearchResults(patients);
  };

  return (
    <div className="main-app">
      <div className="main-content">
        <h2>Provider Dashboard</h2>
        <p>
          Welcome to the Provider Dashboard. You can search for patients and
          check medication interactions.
        </p>

        {/* Patient Detail - Show prominently at the top when selected */}
        {selectedPatient && (
          <div className="feature-section" style={{ marginBottom: '2rem' }}>
            <PatientDetail
              patientId={selectedPatient.id}
              patient={selectedPatient}
              onClose={handleClosePatientDetail}
            />
          </div>
        )}

        {/* Assigned Patients - Show when no patient is selected or below patient detail */}
        <div className="feature-section">
          <PatientList
            patients={assignedPatients}
            onPatientSelect={handlePatientSelect}
            title="My Assigned Patients"
            compact={true}
            emptyMessage="No assigned patients found."
            loading={loadingAssigned}
            loadingMessage="Loading patients from server… Demo data may take a moment on first load."
          />
        </div>

        {/* Patient Search - Show when no patient is selected */}
        {!selectedPatient && (
          <>
            <div className="feature-section">
              <PatientSearch onSearchResults={handleSearchResults} />
            </div>

            {searchResults.length > 0 && (
              <div className="feature-section">
                <PatientList
                  patients={searchResults}
                  onPatientSelect={handlePatientSelect}
                  title="Search Results"
                />
              </div>
            )}
          </>
        )}

        {/* Drug Safety Checker - Always show at the bottom */}
        <div className="feature-section">
          <h3>Drug Safety Checker</h3>
          <DrugSearch
            onDrugSelect={(drugName, rxcui) => {
              console.log('Provider selected drug:', drugName, 'RxCUI:', rxcui);
            }}
            showPubMedSearch={true}
          />
        </div>
      </div>
    </div>
  );
}
