import { useState, useEffect } from 'react';
import { checkDrugInteractionsBatch } from '../../services/interactionsApi';
import './MedicationInteractionAlerts.css';

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
  [key: string]: unknown;
}

interface MedicationInteractionAlertsProps {
  medications: Medication[];
  isProviderView?: boolean; // If true, shows provider-appropriate messaging
}

interface InteractionAlert {
  drug1: string;
  drug2: string;
  interaction: string;
  checked: boolean;
}

export function MedicationInteractionAlerts({ medications, isProviderView = false }: MedicationInteractionAlertsProps) {
  const [interactions, setInteractions] = useState<InteractionAlert[]>([]);
  const [checking, setChecking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const extractMedicationName = (med: Medication): string => {
    if (typeof med.medication === 'string' && med.medication) {
      return med.medication;
    }
    if ((med as any).medicationDisplay) {
      return (med as any).medicationDisplay;
    }
    return (
      (med.medication as any)?.display ||
      med.medicationCodeableConcept?.text ||
      med.medicationCodeableConcept?.coding?.[0]?.display ||
      `Medication ${med.id || 'Unknown'}`
    );
  };

  useEffect(() => {
    if (medications.length < 2) {
      setInteractions([]);
      return;
    }

    const checkInteractions = async () => {
      setChecking(true);
      setError(null);

      // Build all pairs of medications to check
      const pairs: Array<{ drug1: string; drug2: string }> = [];
      for (let i = 0; i < medications.length; i++) {
        for (let j = i + 1; j < medications.length; j++) {
          pairs.push({
            drug1: extractMedicationName(medications[i]),
            drug2: extractMedicationName(medications[j]),
          });
        }
      }

      // If no pairs, nothing to check
      if (pairs.length === 0) {
        setInteractions([]);
        setChecking(false);
        return;
      }

      try {
        // Use batch endpoint for efficient checking
        const response = await checkDrugInteractionsBatch(pairs);
        
        if (response.status === 'success' && response.data.results) {
          const foundInteractions: InteractionAlert[] = response.data.results
            .filter(result => result.interaction !== null)
            .map(result => ({
              drug1: result.drug1,
              drug2: result.drug2,
              interaction: result.interaction!,
              checked: true,
            }));
          setInteractions(foundInteractions);
        } else {
          setError(response.error || 'Failed to check interactions');
          setInteractions([]);
        }
      } catch (err) {
        console.error('Error checking interactions:', err);
        setError('Error checking drug interactions');
        setInteractions([]);
      } finally {
        setChecking(false);
      }
    };

    // Debounce the check to avoid too many API calls
    const timeoutId = setTimeout(() => {
      checkInteractions();
    }, 500);

    return () => clearTimeout(timeoutId);
  }, [medications]);

  if (medications.length < 2) {
    return null;
  }

  if (checking) {
    return (
      <div className="interaction-alerts-container">
        <div className="interaction-alerts-header">
          <h4>🔍 Checking for Drug Interactions...</h4>
        </div>
        <div className="interaction-checking">
          <div className="loading-spinner-small" />
          <span>Analyzing your medications...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="interaction-alerts-container">
        <div className="interaction-error">
          <span className="error-icon">⚠️</span>
          <span>{error}</span>
        </div>
      </div>
    );
  }

  if (interactions.length === 0) {
    return (
      <div className="interaction-alerts-container">
        <div className="interaction-alerts-header">
          <h4>✅ Drug Interaction Check</h4>
        </div>
        <div className="no-interactions">
          <span className="success-icon">✓</span>
          <span>No known interactions found between your medications.</span>
        </div>
        <div className="interaction-data-source">
          <small>Interaction data powered by DrugBank database</small>
        </div>
      </div>
    );
  }

  return (
    <div className="interaction-alerts-container">
      <div className="interaction-alerts-header">
        <h4>⚠️ Drug Interaction Alerts</h4>
        <span className="interaction-count">{interactions.length} interaction(s) found</span>
      </div>
      <div className="interaction-alerts-list">
        {interactions.map((interaction, index) => (
          <div key={index} className="interaction-alert-item">
            <div className="interaction-alert-header">
              <span className="alert-icon">⚠️</span>
              <div className="interaction-drugs">
                <strong>{interaction.drug1}</strong>
                <span className="interaction-separator">+</span>
                <strong>{interaction.drug2}</strong>
              </div>
            </div>
            <div className="interaction-description">
              <p>{interaction.interaction}</p>
            </div>
            <div className="interaction-warning">
              <strong>
                {isProviderView 
                  ? "Review this interaction and consider adjusting the medication regimen if necessary."
                  : "Please consult your healthcare provider before taking these medications together."}
              </strong>
            </div>
          </div>
        ))}
      </div>
      <div className="interaction-data-source">
        <small>Interaction data powered by DrugBank database</small>
      </div>
    </div>
  );
}

