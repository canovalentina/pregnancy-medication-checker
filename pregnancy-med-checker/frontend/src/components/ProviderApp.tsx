import { useState, useEffect } from 'react';
import { DrugSearch } from './medications/DrugSearch';
import { PatientSearch } from './provider/PatientSearch';
import { PatientList } from './provider/PatientList';
import { PatientDetail } from './provider/PatientDetail';
import { getPatientSummary } from '../services/fhirApi';
import type { Patient } from '../types/api';

// Assigned patient IDs for this provider
// These are the patients that are commonly accessed by this provider
const ASSIGNED_PATIENT_IDS = [
  '53418821', // Sarah Williams (test patient with pregnancy data and drug interactions)
  '53418889', // Maria Martinez (patient with pre-term birth history and previous pregnancies)
  '53418860', // Jennifer Chen (patient with multiple conditions: hypertension, diabetes, asthma, and pregnancy)
];

export function ProviderApp() {
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [searchResults, setSearchResults] = useState<Patient[]>([]);
  const [assignedPatients, setAssignedPatients] = useState<Patient[]>([]);
  const [loadingAssigned, setLoadingAssigned] = useState(true);

  // Load assigned patients on mount by fetching their summaries
  useEffect(() => {
    const loadAssignedPatients = async () => {
      setLoadingAssigned(true);
      try {
        const patients: Patient[] = [];
        
        // Fetch each assigned patient by getting their summary (which includes patient info)
        for (const patientId of ASSIGNED_PATIENT_IDS) {
          try {
            const summaryResponse = await getPatientSummary(patientId);
            if (summaryResponse.status === 'success' && summaryResponse.data.patient) {
              patients.push(summaryResponse.data.patient);
            }
          } catch (error) {
            console.warn(`Failed to load patient ${patientId}:`, error);
            // Continue loading other patients even if one fails
          }
        }
        
        setAssignedPatients(patients);
      } catch (error) {
        console.error('Failed to load assigned patients:', error);
      } finally {
        setLoadingAssigned(false);
      }
    };

    loadAssignedPatients();
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
        <p>Welcome to the Provider Dashboard. You can search for patients and check medication interactions.</p>
        
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
          />
        </div>
        
        {/* Patient Search - Show when no patient is selected */}
        {!selectedPatient && (
          <>
            <div className="feature-section">
              <PatientSearch 
                onSearchResults={handleSearchResults}
              />
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

