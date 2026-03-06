import { useState, useEffect } from 'react';
import { checkDrugInteractionsBatch } from '../../services/interactionsApi';
import './FoodInteractionAlerts.css';

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

interface FoodInteractionAlertsProps {
  medications: Medication[];
  isProviderView?: boolean; // If true, shows provider-appropriate messaging
}

interface FoodInteraction {
  medication: string;
  food: string;
  interaction: string;
  checked: boolean;
}

// Common foods that interact with medications
const COMMON_FOODS = [
  'Grapefruit',
  'Caffeine',
  'Tyramine',
  'Alcohol',
  'Soybean oil',
];

export function FoodInteractionAlerts({ medications, isProviderView = false }: FoodInteractionAlertsProps) {
  const [interactions, setInteractions] = useState<FoodInteraction[]>([]);
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
    if (medications.length === 0) {
      setInteractions([]);
      return;
    }

    const checkInteractions = async () => {
      setChecking(true);
      setError(null);

      // Build all medication-food pairs to check
      const pairs: Array<{ drug1: string; drug2: string }> = [];
      for (const medication of medications) {
        const medName = extractMedicationName(medication);
        for (const food of COMMON_FOODS) {
          pairs.push({ drug1: medName, drug2: food });
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
          const foundInteractions: FoodInteraction[] = response.data.results
            .filter(result => result.interaction !== null)
            .map(result => ({
              medication: result.drug1,
              food: result.drug2,
              interaction: result.interaction!,
              checked: true,
            }));
          setInteractions(foundInteractions);
        } else {
          setError(response.error || 'Failed to check interactions');
          setInteractions([]);
        }
      } catch (err) {
        console.error('Error checking food interactions:', err);
        setError('Error checking food interactions');
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

  if (medications.length === 0) {
    return null;
  }

  if (checking) {
    return (
      <div className="food-interaction-alerts-container">
        <div className="food-interaction-alerts-header">
          <h4>🔍 Checking for Food Interactions...</h4>
        </div>
        <div className="food-interaction-checking">
          <div className="loading-spinner-small" />
          <span>Analyzing your medications for food interactions...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="food-interaction-alerts-container">
        <div className="food-interaction-error">
          <span className="error-icon">⚠️</span>
          <span>{error}</span>
        </div>
      </div>
    );
  }

  if (interactions.length === 0) {
    return (
      <div className="food-interaction-alerts-container">
        <div className="food-interaction-alerts-header">
          <h4>✅ Food Interaction Check</h4>
        </div>
        <div className="no-food-interactions">
          <span className="success-icon">✓</span>
          <span>
            {isProviderView 
              ? "No known food interactions found for this patient's medications."
              : "No known food interactions found with your medications. You can safely consume common foods."}
          </span>
        </div>
        <div className="food-interaction-data-source">
          <small>Interaction data powered by DrugBank database</small>
        </div>
      </div>
    );
  }

  // Group interactions by food
  const interactionsByFood = interactions.reduce((acc, interaction) => {
    if (!acc[interaction.food]) {
      acc[interaction.food] = [];
    }
    acc[interaction.food].push(interaction);
    return acc;
  }, {} as Record<string, FoodInteraction[]>);

  return (
    <div className="food-interaction-alerts-container">
      <div className="food-interaction-alerts-header">
        <h4>⚠️ Food Interaction Alerts</h4>
        <span className="interaction-count">{interactions.length} interaction(s) found</span>
      </div>
      
      {Object.entries(interactionsByFood).map(([food, foodInteractions]) => (
        <div key={food} className="food-interaction-group">
          <div className="food-interaction-food-header">
            <span className="food-icon">🍽️</span>
            <h5>Avoid: {food}</h5>
          </div>
          <div className="food-interaction-alerts-list">
            {foodInteractions.map((interaction, index) => (
              <div key={index} className="food-interaction-alert-item">
                <div className="food-interaction-alert-header">
                  <span className="alert-icon">⚠️</span>
                  <div className="food-interaction-medication">
                    <strong>{interaction.medication}</strong>
                  </div>
                </div>
                <div className="food-interaction-description">
                  <p>{interaction.interaction}</p>
                </div>
                <div className="food-interaction-warning">
                  <strong>
                    {isProviderView 
                      ? `⚠️ Patient should avoid ${food} while taking ${interaction.medication}. Please inform the patient of this interaction.`
                      : `⚠️ Avoid consuming ${food} while taking ${interaction.medication}.`}
                  </strong>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
      
      <div className="food-interaction-data-source">
        <small>Interaction data powered by DrugBank database</small>
      </div>
    </div>
  );
}

