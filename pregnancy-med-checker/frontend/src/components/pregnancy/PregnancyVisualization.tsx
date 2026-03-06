import { useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
} from 'recharts';
import type { PatientSummary } from '../../types/api';
import './PregnancyVisualization.css';

interface PregnancyVisualizationProps {
  summary: PatientSummary;
}

// Helper function to determine trimester from gestational weeks
function getTrimester(weeks: number): 1 | 2 | 3 {
  if (weeks <= 13) return 1;
  if (weeks <= 27) return 2;
  return 3;
}

// Helper function to format date
function formatDate(dateStr: string): string {
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  } catch {
    return dateStr;
  }
}

export function PregnancyVisualization({ summary }: PregnancyVisualizationProps) {
  // Process observations to extract gestational age data
  const chartData = useMemo(() => {
    const gestationalObservations = summary.observations
      .filter((obs) => {
        const codings = obs.code?.coding || [];
        const code = codings[0]?.code || obs.code?.text || '';
        const system = codings[0]?.system || '';
        const display = codings[0]?.display || obs.code?.text || '';
        
        // Check for LOINC code 11778-8 (Gestational age)
        // Check for SNOMED code 57036006 (Gestational age)
        // Or check display text
        return (
          (system.includes('loinc.org') && code === '11778-8') ||
          code === '57036006' ||
          display.toLowerCase().includes('gestational') ||
          display.toLowerCase().includes('pregnancy')
        );
      })
      .map((obs) => {
        const value = obs.valueQuantity?.value;
        const date = obs.effectiveDateTime || obs.issued || '';
        const weeks = typeof value === 'number' ? value : parseFloat(String(value)) || 0;
        
        return {
          date,
          weeks,
          trimester: getTrimester(weeks),
          formattedDate: formatDate(date),
          observationId: obs.id,
        };
      })
      .filter((item) => item.weeks > 0 && item.date)
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

    return gestationalObservations;
  }, [summary.observations]);

  // Group observations by pregnancy (if multiple pregnancies exist)
  const pregnanciesData = useMemo(() => {
    if (!summary.pregnancyHistory?.pregnancies) {
      return [];
    }

    return summary.pregnancyHistory.pregnancies.map((pregnancy, index) => {
      const observations = pregnancy.observations
        .filter((obs) => obs.type === 'gestational_age')
        .map((obs) => ({
          date: obs.date,
          weeks: typeof obs.value === 'number' ? obs.value : parseFloat(String(obs.value)) || 0,
          formattedDate: formatDate(obs.date),
        }))
        .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

      // Create a more user-friendly label
      let label = '';
      if (pregnancy.outcome === 'ongoing') {
        label = 'Current Pregnancy';
      } else if (pregnancy.startDate) {
        try {
          const startYear = new Date(pregnancy.startDate).getFullYear();
          if (pregnancy.isPreterm) {
            label = `Pregnancy ${startYear} (Pre-term)`;
          } else {
            label = `Pregnancy ${startYear}`;
          }
        } catch {
          label = pregnancy.isPreterm 
            ? `Previous Pregnancy (Pre-term)` 
            : `Previous Pregnancy ${index + 1}`;
        }
      } else {
        label = pregnancy.isPreterm 
          ? `Pregnancy ${index + 1} (Pre-term)` 
          : `Pregnancy ${index + 1}`;
      }

      return {
        ...pregnancy,
        observations,
        label,
      };
    });
  }, [summary.pregnancyHistory]);

  // Trimester distribution data
  const trimesterData = useMemo(() => {
    const trimesterCounts = { '1st': 0, '2nd': 0, '3rd': 0 };
    
    chartData.forEach((item) => {
      if (item.trimester === 1) trimesterCounts['1st']++;
      else if (item.trimester === 2) trimesterCounts['2nd']++;
      else if (item.trimester === 3) trimesterCounts['3rd']++;
    });

    return [
      { trimester: '1st Trimester', count: trimesterCounts['1st'], color: '#FF6B6B' },
      { trimester: '2nd Trimester', count: trimesterCounts['2nd'], color: '#4ECDC4' },
      { trimester: '3rd Trimester', count: trimesterCounts['3rd'], color: '#45B7D1' },
    ];
  }, [chartData]);

  if (chartData.length === 0 && pregnanciesData.length === 0) {
    return (
      <div className="pregnancy-visualization-empty">
        <p>No pregnancy observation data available for visualization.</p>
      </div>
    );
  }

  return (
    <div className="pregnancy-visualization">
      <h3 className="visualization-title">Pregnancy Data Visualization</h3>

      {/* Pregnancy History Summary */}
      {summary.pregnancyHistory && (
        <div className="pregnancy-history-summary">
          <div className="history-card">
            <div className="history-icon">👶</div>
            <div className="history-content">
              <h4>Total Births</h4>
              <p className="history-value">{summary.pregnancyHistory.totalBirths}</p>
            </div>
          </div>
          <div className="history-card">
            <div className="history-icon">⚠️</div>
            <div className="history-content">
              <h4>Pre-term Births</h4>
              <p className="history-value">{summary.pregnancyHistory.pretermBirths}</p>
            </div>
          </div>
          {summary.pregnancyHistory.totalBirths > 0 && (
            <div className="history-card">
              <div className="history-icon">📊</div>
              <div className="history-content">
                <h4>Pre-term Rate</h4>
                <p className="history-value">
                  {Math.round(
                    (summary.pregnancyHistory.pretermBirths /
                      summary.pregnancyHistory.totalBirths) *
                      100
                  )}
                  %
                </p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Gestational Age Over Time Chart */}
      {chartData.length > 0 && (
        <div className="chart-container">
          <h4>Gestational Age Over Time</h4>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="formattedDate"
                angle={-45}
                textAnchor="end"
                height={80}
                interval={Math.floor(chartData.length / 10)}
              />
              <YAxis
                label={{ value: 'Gestational Weeks', angle: -90, position: 'insideLeft' }}
                domain={[0, 42]}
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload;
                    return (
                      <div className="custom-tooltip">
                        <p>{`Date: ${data.formattedDate}`}</p>
                        <p>{`Weeks: ${data.weeks}`}</p>
                        <p>{`Trimester: ${data.trimester}${data.trimester === 1 ? 'st' : data.trimester === 2 ? 'nd' : 'rd'}`}</p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="weeks"
                stroke="#667eea"
                strokeWidth={2}
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
                name="Gestational Weeks"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Multiple Pregnancies Comparison */}
      {pregnanciesData.length > 1 && (
        <div className="chart-container">
          <h4>Pregnancy Comparison</h4>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="formattedDate"
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis
                label={{ value: 'Gestational Weeks', angle: -90, position: 'insideLeft' }}
                domain={[0, 42]}
              />
              <Tooltip />
              <Legend />
              {pregnanciesData.map((pregnancy, index) => (
                <Line
                  key={pregnancy.id}
                  type="monotone"
                  dataKey="weeks"
                  data={pregnancy.observations}
                  stroke={index === 0 ? '#667eea' : index === 1 ? '#f093fb' : '#4facfe'}
                  strokeWidth={2}
                  dot={{ r: 4 }}
                  name={pregnancy.label}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Trimester Distribution */}
      {trimesterData.some((item) => item.count > 0) && (
        <div className="chart-container">
          <h4>Observations by Trimester</h4>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={trimesterData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="trimester" />
              <YAxis label={{ value: 'Number of Observations', angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Bar dataKey="count" name="Observations">
                {trimesterData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Risk Assessment Note */}
      {summary.pregnancyHistory && summary.pregnancyHistory.pretermBirths > 0 && (
        <div className="risk-assessment-note">
          <h4>⚠️ Pregnancy Risk Assessment</h4>
          <p>
            This patient has a history of {summary.pregnancyHistory.pretermBirths} pre-term
            {summary.pregnancyHistory.pretermBirths === 1 ? ' birth' : ' births'}. This information
            should be considered when evaluating medication safety and pregnancy risk factors.
          </p>
        </div>
      )}
    </div>
  );
}

