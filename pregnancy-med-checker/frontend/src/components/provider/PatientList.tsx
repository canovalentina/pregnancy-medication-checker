import { useState, useEffect } from 'react';
import type { Patient } from '../../types/api';
import './PatientList.css';

interface PatientListProps {
  patients: Patient[];
  onPatientSelect?: (patient: Patient) => void;
  title?: string;
  emptyMessage?: string;
  loading?: boolean;
  loadingMessage?: string;
  compact?: boolean;
  itemsPerPage?: number;
}

export function PatientList({
  patients,
  onPatientSelect,
  title = 'Patients',
  emptyMessage = 'No patients found.',
  loading = false,
  loadingMessage = 'Loading patients...',
  compact = false,
  itemsPerPage = 5,
}: PatientListProps) {
  const [currentPage, setCurrentPage] = useState(1);

  // Reset to page 1 when patients list changes
  useEffect(() => {
    setCurrentPage(1);
  }, [patients.length]);

  // Calculate pagination
  const totalPages = Math.ceil(patients.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentPatients = patients.slice(startIndex, endIndex);

  const goToPage = (page: number) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page);
    }
  };

  const goToPrevious = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  };

  const goToNext = () => {
    if (currentPage < totalPages) {
      setCurrentPage(currentPage + 1);
    }
  };
  const formatDate = (dateStr?: string) => {
    if (!dateStr) return null;
    try {
      return new Date(dateStr).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
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
      if (
        monthDiff < 0 ||
        (monthDiff === 0 && today.getDate() < birth.getDate())
      ) {
        age--;
      }
      return age;
    } catch {
      return null;
    }
  };

  if (loading) {
    return (
      <div className="patient-list">
        {title && <h3 className="patient-list-title">{title}</h3>}
        <div className="patient-list-loading">
          <div className="loading-spinner" />
          <p>{loadingMessage}</p>
        </div>
      </div>
    );
  }

  if (patients.length === 0) {
    return (
      <div className="patient-list">
        {title && <h3 className="patient-list-title">{title}</h3>}
        <div className="patient-list-empty">
          <div className="empty-icon">👤</div>
          <p>{emptyMessage}</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`patient-list ${compact ? 'compact' : ''}`}>
      {title && (
        <div className="patient-list-header">
          <h3 className="patient-list-title">{title}</h3>
          <span className="patient-count">
            Showing {startIndex + 1}-{Math.min(endIndex, patients.length)} of{' '}
            {patients.length}
          </span>
        </div>
      )}

      <div className="patient-list-items">
        {currentPatients.map(patient => {
          const age = calculateAge(patient.birth_date);
          const formattedDate = formatDate(patient.birth_date);

          return (
            <div
              key={patient.id}
              className={`patient-list-item ${onPatientSelect ? 'clickable' : ''}`}
              onClick={() => onPatientSelect?.(patient)}
            >
              <div className="patient-item-main">
                <div className="patient-item-name">{patient.name}</div>
                <div className="patient-item-details">
                  {formattedDate && (
                    <span className="patient-detail-badge">
                      <span className="detail-icon">📅</span>
                      {formattedDate}
                      {age !== null && ` (${age} years)`}
                    </span>
                  )}
                  {patient.gender && (
                    <span className="patient-detail-badge">
                      <span className="detail-icon">⚧</span>
                      {patient.gender.charAt(0).toUpperCase() +
                        patient.gender.slice(1)}
                    </span>
                  )}
                </div>
              </div>
              <div className="patient-item-secondary">
                {!compact && (
                  <div className="patient-item-id">
                    <span className="id-label">ID:</span>
                    <span className="id-value">{patient.id}</span>
                  </div>
                )}
                {onPatientSelect && (
                  <div className="patient-item-arrow">
                    <span>→</span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {totalPages > 1 && (
        <div className="patient-list-pagination">
          <button
            className="pagination-button"
            onClick={goToPrevious}
            disabled={currentPage === 1}
            type="button"
          >
            ← Previous
          </button>

          <div className="pagination-pages">
            {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => {
              // Show first page, last page, current page, and pages around current
              const showPage =
                page === 1 ||
                page === totalPages ||
                (page >= currentPage - 1 && page <= currentPage + 1);

              if (!showPage) {
                // Show ellipsis
                if (page === currentPage - 2 || page === currentPage + 2) {
                  return (
                    <span key={page} className="pagination-ellipsis">
                      ...
                    </span>
                  );
                }
                return null;
              }

              return (
                <button
                  key={page}
                  className={`pagination-page ${currentPage === page ? 'active' : ''}`}
                  onClick={() => goToPage(page)}
                  type="button"
                >
                  {page}
                </button>
              );
            })}
          </div>

          <button
            className="pagination-button"
            onClick={goToNext}
            disabled={currentPage === totalPages}
            type="button"
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}
