import { useState } from 'react';
import { lookupRxCUI, getRxNormProperties } from '../../services/rxnormApi';
import { searchPublications, getPublicationDetails } from '../../services/pubmedApi';
import { MedicationSafetyCard, type MedicationSafetyData } from './MedicationSafetyCard';
import type { Publication } from '../../types/api';
import './MedicationList.css';

interface Medication {
  id?: string;
  medication?: {
    display?: string;
    reference?: string;
  };
  medicationCodeableConcept?: {
    text?: string;
    coding?: Array<{
      display?: string;
      code?: string;
    }>;
  };
  status?: string;
  intent?: string;
  authoredOn?: string;
  dosageInstruction?: Array<{
    text?: string;
    [key: string]: unknown;
  }>;
  [key: string]: unknown;
}

interface MedicationListProps {
  medications: Medication[];
  title?: string;
  emptyMessage?: string;
  loading?: boolean;
  showSafetyInfo?: boolean;
  compact?: boolean;
}

export function MedicationList({
  medications,
  title = 'Medications',
  emptyMessage = 'No medications found.',
  loading = false,
  showSafetyInfo = true,
  compact = false,
}: MedicationListProps) {
  const [expandedMedications, setExpandedMedications] = useState<Set<string>>(new Set());
  const [safetyData, setSafetyData] = useState<Map<string, MedicationSafetyData>>(new Map());
  const [loadingSafety, setLoadingSafety] = useState<Set<string>>(new Set());

  const extractMedicationName = (med: Medication): string => {
    // Backend returns medication as a string
    if (typeof med.medication === 'string' && med.medication) {
      return med.medication;
    }
    // Also check medicationDisplay (from backend coding info)
    if ((med as any).medicationDisplay) {
      return (med as any).medicationDisplay;
    }
    // Fallback to original FHIR structure (if medication is an object)
    return (
      (med.medication as any)?.display ||
      med.medicationCodeableConcept?.text ||
      med.medicationCodeableConcept?.coding?.[0]?.display ||
      `Medication ${med.id || 'Unknown'}`
    );
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

  const toggleExpanded = (medicationId: string) => {
    setExpandedMedications((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(medicationId)) {
        newSet.delete(medicationId);
      } else {
        newSet.add(medicationId);
      }
      return newSet;
    });
  };

  const loadSafetyInfo = async (medication: Medication, medicationName: string) => {
    const medId = medication.id || medicationName;
    if (safetyData.has(medId) || loadingSafety.has(medId)) {
      return;
    }

    setLoadingSafety((prev) => new Set(prev).add(medId));

    try {
      // Lookup RxCUI
      const lookupResponse = await lookupRxCUI(medicationName);
      let rxcui: string[] = [];
      let properties: Record<string, unknown> | undefined;
      let pubmedResults: Publication[] | undefined;

      if (lookupResponse.status === 'success' && lookupResponse.data.rxcui.length > 0) {
        rxcui = lookupResponse.data.rxcui;

        // Get properties for first RxCUI
        const rxcuiNum = parseInt(rxcui[0]);
        if (!isNaN(rxcuiNum)) {
          const propsResponse = await getRxNormProperties(rxcuiNum);
          if (propsResponse.status === 'success') {
            properties = propsResponse.data;
          }
        }

        // Search PubMed for pregnancy safety
        // Extract generic drug name for better PubMed search results
        // Remove dosage, form, and brand name info
        let normalizedName = medicationName;
        const bracketIndex = normalizedName.indexOf('[');
        if (bracketIndex > 0) {
          normalizedName = normalizedName.substring(0, bracketIndex).trim();
        }
        // Remove dosage and form info, keep first word (generic name)
        const words = normalizedName.split(/\s+/);
        const genericName = words[0];
        
        const query = `${genericName} pregnancy safety`;
        const searchResponse = await searchPublications(query, 0, 5);
        if (searchResponse.status === 'success' && searchResponse.data.ids.length > 0) {
          const detailsResponse = await getPublicationDetails(searchResponse.data.ids, 'all');
          if (detailsResponse.status === 'success') {
            pubmedResults = detailsResponse.data.results;
          }
        }
      }

      const safety: MedicationSafetyData = {
        drugName: medicationName,
        rxcui,
        properties,
        pubmedResults,
      };

      setSafetyData((prev) => new Map(prev).set(medId, safety));
    } catch (error) {
      console.error('Error loading safety info:', error);
    } finally {
      setLoadingSafety((prev) => {
        const newSet = new Set(prev);
        newSet.delete(medId);
        return newSet;
      });
    }
  };

  const handleExpand = (medication: Medication) => {
    const medicationName = extractMedicationName(medication);
    const medId = medication.id || medicationName;
    
    toggleExpanded(medId);
    
    // Load safety info when expanded if not already loaded
    if (showSafetyInfo && !safetyData.has(medId) && !loadingSafety.has(medId)) {
      loadSafetyInfo(medication, medicationName);
    }
  };

  if (loading) {
    return (
      <div className="medication-list">
        {title && <h3 className="medication-list-title">{title}</h3>}
        <div className="medication-list-loading">
          <div className="loading-spinner" />
          <p>Loading medications...</p>
        </div>
      </div>
    );
  }

  if (medications.length === 0) {
    return (
      <div className="medication-list">
        {title && <h3 className="medication-list-title">{title}</h3>}
        <div className="medication-list-empty">
          <div className="empty-icon">💊</div>
          <p>{emptyMessage}</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`medication-list ${compact ? 'compact' : ''}`}>
      {title && (
        <div className="medication-list-header">
          <h3 className="medication-list-title">{title}</h3>
          <span className="medication-count">({medications.length})</span>
        </div>
      )}

      <div className="medication-list-items">
        {medications.map((medication, index) => {
          const medicationName = extractMedicationName(medication);
          const medId = medication.id || medicationName;
          const isExpanded = expandedMedications.has(medId);
          const safety = safetyData.get(medId);
          const isLoadingSafety = loadingSafety.has(medId);
          const status = medication.status || 'unknown';
          const formattedDate = formatDate(medication.authoredOn);

          return (
            <div key={medication.id || index} className="medication-list-item">
              <div className="medication-item-header">
                <div className="medication-item-main">
                  <div className="medication-item-name">{medicationName}</div>
                  <div className="medication-item-meta">
                    <span className={`status-badge status-${status}`}>{status}</span>
                    {formattedDate && (
                      <span className="meta-badge">
                        <span className="detail-icon">📅</span>
                        {formattedDate}
                      </span>
                    )}
                    {medication.intent && (
                      <span className="meta-badge">{medication.intent}</span>
                    )}
                  </div>
                </div>
                {showSafetyInfo && (
                  <button
                    className="expand-button"
                    onClick={() => handleExpand(medication)}
                    type="button"
                  >
                    {isExpanded ? '−' : '+'}
                  </button>
                )}
              </div>

              {!isExpanded && (
                <div className="medication-item-details-collapsed">
                  {medication.dosageInstruction && medication.dosageInstruction.length > 0 && (
                    <div className="dosage-preview">
                      <strong>Dosage:</strong>{' '}
                      {medication.dosageInstruction[0].text || 'See details'}
                    </div>
                  )}
                </div>
              )}

              {isExpanded && (
                <div className="medication-item-expanded">
                  <div className="medication-details-full">
                    {medication.intent && (
                      <div className="detail-row">
                        <strong>Intent:</strong> {medication.intent}
                      </div>
                    )}
                    {formattedDate && (
                      <div className="detail-row">
                        <strong>Prescribed:</strong> {formattedDate}
                      </div>
                    )}
                    {medication.dosageInstruction && medication.dosageInstruction.length > 0 && (
                      <div className="detail-row">
                        <strong>Dosage Instructions:</strong>
                        <div className="dosage-instructions">
                          {medication.dosageInstruction.map((dosage, idx) => (
                            <div key={idx} className="dosage-item">
                              {dosage.text || JSON.stringify(dosage)}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    {medication.id && (
                      <div className="detail-row">
                        <strong>Medication ID:</strong>
                        <span className="medication-id">{medication.id}</span>
                      </div>
                    )}
                  </div>

                  {showSafetyInfo && (
                    <div className="medication-safety-section">
                      {isLoadingSafety && (
                        <div className="safety-loading">
                          <div className="loading-spinner-small" />
                          <span>Loading safety information...</span>
                        </div>
                      )}
                      {safety && (
                        <MedicationSafetyCard medication={safety} compact={true} />
                      )}
                      {!isLoadingSafety && !safety && (
                        <div className="safety-unavailable">
                          Safety information not available for this medication.
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

