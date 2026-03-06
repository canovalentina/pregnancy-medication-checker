import { useState } from 'react';
import { searchPatients } from '../../services/fhirApi';
import type { Patient } from '../../types/api';
import './PatientSearch.css';

interface PatientSearchProps {
  onSearchResults?: (patients: Patient[]) => void;
}

export function PatientSearch({ onSearchResults }: PatientSearchProps) {
  const [name, setName] = useState('');
  const [birthDate, setBirthDate] = useState('');
  const [gender, setGender] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<Patient[]>([]);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    setHasSearched(true);

    try {
      const baseParams: {
        name?: string;
        birth_date?: string;
        gender?: string;
      } = {};

      if (name.trim()) baseParams.name = name.trim();
      if (birthDate) baseParams.birth_date = birthDate;
      if (gender) baseParams.gender = gender;

      // At least one search parameter is required
      if (Object.keys(baseParams).length === 0) {
        setError('Please provide at least one search criteria');
        setLoading(false);
        return;
      }

      // Search multiple ways to find all relevant patients:
      // 1. Ingested patients (production tag)
      // 2. All patients (including test-tagged and non-ingested)
      // 3. If name provided, also try searching by last name only
      const searchPromises = [
        searchPatients({ ...baseParams, only_ingested_patients: true }),
        searchPatients({ ...baseParams, only_ingested_patients: false }),
      ];

      // If searching by name, also try variations for better matching
      if (name.trim()) {
        const nameParts = name.trim().split(/\s+/);
        if (nameParts.length > 1) {
          // Try last name only
          searchPromises.push(
            searchPatients({ 
              name: nameParts[nameParts.length - 1], 
              only_ingested_patients: false 
            })
          );
          // Try first name only
          searchPromises.push(
            searchPatients({ 
              name: nameParts[0], 
              gender: gender || 'female', // Add gender filter to narrow results
              only_ingested_patients: false 
            })
          );
        }
      }

      const responses = await Promise.all(searchPromises);
      const [ingestedResponse, allResponse, ...additionalResponses] = responses;

      console.log('Provider search results:', {
        ingested: ingestedResponse.status === 'success' ? ingestedResponse.data.length : 0,
        all: allResponse.status === 'success' ? allResponse.data.length : 0,
        ingestedIds: ingestedResponse.status === 'success' ? ingestedResponse.data.map(p => p.id) : [],
        allIds: allResponse.status === 'success' ? allResponse.data.map(p => p.id).slice(0, 10) : [],
      });

      // Combine results and deduplicate by patient ID
      const allPatients: Patient[] = [];
      const seenIds = new Set<string>();

      // Add ingested patients first (they're more relevant)
      if (ingestedResponse.status === 'success') {
        for (const patient of ingestedResponse.data) {
          if (!seenIds.has(patient.id)) {
            allPatients.push(patient);
            seenIds.add(patient.id);
          }
        }
      }

      // Then add non-ingested patients (avoiding duplicates)
      if (allResponse.status === 'success') {
        for (const patient of allResponse.data) {
          if (!seenIds.has(patient.id)) {
            allPatients.push(patient);
            seenIds.add(patient.id);
          }
        }
      }

      // Add any additional search results (e.g., last name only searches)
      for (const response of additionalResponses) {
        if (response.status === 'success') {
          for (const patient of response.data) {
            if (!seenIds.has(patient.id)) {
              allPatients.push(patient);
              seenIds.add(patient.id);
            }
          }
        }
      }

      console.log('Combined results:', {
        total: allPatients.length,
        ids: allPatients.map(p => p.id),
        has53418821: allPatients.some(p => p.id === '53418821'),
      });

      // Check for errors
      if (ingestedResponse.status === 'error' && allResponse.status === 'error') {
        setError(ingestedResponse.error || allResponse.error || 'Failed to search patients');
        setResults([]);
      } else {
        setResults(allPatients);
        onSearchResults?.(allPatients);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred while searching');
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setName('');
    setBirthDate('');
    setGender('');
    setResults([]);
    setError(null);
    setHasSearched(false);
    onSearchResults?.([]);
  };


  return (
    <div className="patient-search">
      <div className="patient-search-header">
        <h3>Search Patients</h3>
        {hasSearched && (
          <button className="clear-button" onClick={handleClear} type="button">
            Clear
          </button>
        )}
      </div>

      <form className="patient-search-form" onSubmit={handleSubmit}>
        <div className="search-fields">
          <div className="form-group">
            <label htmlFor="patient-name">Patient Name</label>
            <input
              id="patient-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter patient name"
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="birth-date">Date of Birth</label>
            <input
              id="birth-date"
              type="date"
              value={birthDate}
              onChange={(e) => setBirthDate(e.target.value)}
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="gender">Gender</label>
            <select
              id="gender"
              value={gender}
              onChange={(e) => setGender(e.target.value)}
              disabled={loading}
            >
              <option value="">All</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="other">Other</option>
            </select>
          </div>
        </div>

        {error && <div className="error-message">{error}</div>}

        <div className="form-actions">
          <button
            type="submit"
            className="search-button"
            disabled={loading || (!name.trim() && !birthDate && !gender)}
          >
            {loading ? (
              <>
                <span className="button-spinner" />
                Searching...
              </>
            ) : (
              'Search Patients'
            )}
          </button>
        </div>
      </form>

      {hasSearched && !loading && (
        <div className="search-results-summary">
          <p>
            Found <strong>{results.length}</strong> patient{results.length !== 1 ? 's' : ''}
            {results.length > 0 && ' - See results below'}
          </p>
        </div>
      )}

      {hasSearched && !loading && results.length === 0 && !error && (
        <div className="no-results">
          <p>No patients found matching your search criteria.</p>
          <p className="no-results-hint">Try adjusting your search parameters.</p>
        </div>
      )}
    </div>
  );
}

