import type { Publication } from '../../types/api';
import './MedicationSafetyCard.css';

export interface MedicationSafetyData {
  drugName: string;
  rxcui?: string[];
  properties?: Record<string, unknown>;
  pubmedResults?: Publication[];
}

interface MedicationSafetyCardProps {
  medication: MedicationSafetyData;
  compact?: boolean;
}

type SafetyLevel = 'safe' | 'caution' | 'unsafe' | 'unknown';

function determineSafetyLevel(
  medication: MedicationSafetyData
): { level: SafetyLevel; reason: string } {
  // Check PubMed results for safety indicators
  if (medication.pubmedResults && medication.pubmedResults.length > 0) {
    const abstracts = medication.pubmedResults
      .map((p) => p.Abstract?.toLowerCase() || '')
      .join(' ');
    const titles = medication.pubmedResults
      .map((p) => p.Title?.toLowerCase() || '')
      .join(' ');

    const combinedText = abstracts + ' ' + titles;

    // Look for safety indicators in research
    if (
      combinedText.includes('contraindicated') ||
      combinedText.includes('teratogenic') ||
      combinedText.includes('birth defect') ||
      combinedText.includes('not recommended') ||
      combinedText.includes('avoid')
    ) {
      return {
        level: 'unsafe',
        reason: 'Research indicates potential risks during pregnancy',
      };
    }

    if (
      combinedText.includes('safe') ||
      combinedText.includes('no adverse') ||
      combinedText.includes('recommended')
    ) {
      return {
        level: 'safe',
        reason: 'Research suggests relative safety',
      };
    }

    if (
      combinedText.includes('caution') ||
      combinedText.includes('monitor') ||
      combinedText.includes('risk')
    ) {
      return {
        level: 'caution',
        reason: 'Research indicates caution may be needed',
      };
    }
  }

  // Check RxNorm properties for pregnancy category if available
  if (medication.properties) {
    const propsStr = JSON.stringify(medication.properties).toLowerCase();
    if (propsStr.includes('pregnancy category')) {
      // Extract category if present
      const categoryMatch = propsStr.match(/pregnancy category[:\s]+([a-z])/i);
      if (categoryMatch) {
        const category = categoryMatch[1].toUpperCase();
        if (category === 'A' || category === 'B') {
          return { level: 'safe', reason: `Pregnancy Category ${category}` };
        }
        if (category === 'C') {
          return {
            level: 'caution',
            reason: `Pregnancy Category ${category} - Use with caution`,
          };
        }
        if (category === 'D' || category === 'X') {
          return {
            level: 'unsafe',
            reason: `Pregnancy Category ${category} - Not recommended`,
          };
        }
      }
    }
  }

  return {
    level: 'unknown',
    reason: 'Insufficient safety data available',
  };
}

export function MedicationSafetyCard({
  medication,
  compact = false,
}: MedicationSafetyCardProps) {
  const safety = determineSafetyLevel(medication);

  if (compact) {
    return (
      <div className={`medication-safety-card compact safety-${safety.level}`}>
        <div className="safety-header-compact">
          <span className="drug-name-compact">{medication.drugName}</span>
          <span className={`safety-badge safety-${safety.level}`}>
            {safety.level.toUpperCase()}
          </span>
        </div>
        <div className="safety-reason-compact">{safety.reason}</div>
      </div>
    );
  }

  return (
    <div className={`medication-safety-card safety-${safety.level}`}>
      <div className="safety-card-header">
        <div className="drug-info">
          <h3 className="drug-name">{medication.drugName}</h3>
          {medication.rxcui && medication.rxcui.length > 0 && (
            <div className="rxcui-info">
              RxCUI: {medication.rxcui.join(', ')}
            </div>
          )}
        </div>
        <div className={`safety-indicator safety-${safety.level}`}>
          <div className="safety-icon">
            {safety.level === 'safe' && '✓'}
            {safety.level === 'caution' && '⚠'}
            {safety.level === 'unsafe' && '✗'}
            {safety.level === 'unknown' && '?'}
          </div>
          <div className="safety-label">{safety.level.toUpperCase()}</div>
        </div>
      </div>

      <div className="safety-content">
        <div className="safety-summary">
          <div className="safety-reason">
            <strong>Safety Assessment:</strong> {safety.reason}
          </div>
        </div>

        {medication.properties && Object.keys(medication.properties).length > 0 && (
          <div className="safety-section">
            <h4>Drug Information</h4>
            <div className="properties-list">
              {Object.entries(medication.properties)
                .slice(0, 5)
                .map(([key, value]) => (
                  <div key={key} className="property-row">
                    <span className="property-label">{key}:</span>
                    <span className="property-value">
                      {typeof value === 'object'
                        ? JSON.stringify(value)
                        : String(value)}
                    </span>
                  </div>
                ))}
            </div>
          </div>
        )}

        {medication.pubmedResults && medication.pubmedResults.length > 0 && (
          <div className="safety-section">
            <h4>Research Evidence ({medication.pubmedResults.length} studies)</h4>
            <div className="research-summary">
              <p>
                Found {medication.pubmedResults.length} research publication
                {medication.pubmedResults.length !== 1 ? 's' : ''} related to
                pregnancy safety.
              </p>
              <div className="research-links">
                {medication.pubmedResults.slice(0, 3).map((pub, index) => (
                  <a
                    key={pub.PMID || index}
                    href={`https://pubmed.ncbi.nlm.nih.gov/${pub.PMID}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="research-link"
                  >
                    {pub.Title || `Publication ${index + 1}`}
                  </a>
                ))}
              </div>
            </div>
          </div>
        )}

        <div className="safety-disclaimer">
          <strong>Important:</strong> This information is for educational purposes
          only. Always consult with a healthcare provider before taking any
          medication during pregnancy.
        </div>
      </div>
    </div>
  );
}

