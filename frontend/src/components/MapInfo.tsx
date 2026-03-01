import React from 'react';
import type { AnalysisResponse, Recommendation } from '../types';

interface MapInfoProps {
  currentAnalysis?: AnalysisResponse | null;
}

const InsuranceBadge: React.FC<{ score: number }> = ({ score }) => {
  if (score < 0.75) return null;
  return (
    <div style={{
      padding: '8px 10px',
      marginBottom: '12px',
      background: '#ff1a1a15',
      border: '1px solid #FF4B2B',
      borderRadius: '4px',
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
    }}>
      <span style={{ fontSize: '1.1em', animation: 'pulse 1.5s infinite' }}>🚨</span>
      <div>
        <div style={{ color: '#FF4B2B', fontWeight: 700, fontSize: '0.8em', fontFamily: "'Space Mono', monospace" }}>
          INSURANCE TRIGGER ARMED
        </div>
        <div style={{ color: '#8b9bb4', fontSize: '0.7em' }}>
          Risk exceeds threshold. Oracle monitoring for rainfall &gt;30mm.
        </div>
      </div>
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
      `}</style>
    </div>
  );
};

const RecommendationCard: React.FC<{ rec: Recommendation; index: number }> = ({ rec, index }) => (
  <div style={{
    marginBottom: '8px',
    padding: '10px',
    background: rec.critical_diversion_point ? '#ff4b2b0a' : '#4f8ef70a',
    border: `1px solid ${rec.critical_diversion_point ? '#FF4B2B44' : '#4f8ef733'}`,
    borderRadius: '4px',
    fontSize: '0.78em',
  }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
      <span style={{
        fontWeight: 700,
        color: rec.critical_diversion_point ? '#FF4B2B' : '#4f8ef7',
        fontFamily: "'Space Mono', monospace",
        fontSize: '0.9em',
      }}>
        {rec.critical_diversion_point ? '🔴 CRITICAL' : `📍 #${index + 1}`} — {rec.type}
      </span>
      <span style={{ color: '#8b9bb4', fontSize: '0.85em' }}>{rec.dimensions}</span>
    </div>
    <div style={{ color: '#00d4aa', marginBottom: '3px', fontWeight: 600 }}>{rec.impact}</div>
    <div style={{ color: '#8b9bb4', lineHeight: 1.4 }}>{rec.reasoning}</div>
    <div style={{ marginTop: '4px', color: '#445', fontFamily: "'Space Mono', monospace", fontSize: '0.85em' }}>
      [{rec.coords[0].toFixed(4)}, {rec.coords[1].toFixed(4)}] · slope: {rec.slope_degrees.toFixed(1)}°
    </div>
  </div>
);

export const MapInfo: React.FC<MapInfoProps> = ({ currentAnalysis }) => {
  const riskForecast = currentAnalysis?.risk_forecast;
  const liveScore = currentAnalysis?.risk_score;
  const futureScore = riskForecast && riskForecast.length > 2 ? riskForecast[2] : null;
  const recommendations = currentAnalysis?.recommendations ?? [];

  const displayLiveScore = liveScore !== undefined && liveScore !== null ? liveScore.toFixed(4) : '--';
  const displayFutureScore = futureScore !== undefined && futureScore !== null ? futureScore.toFixed(4) : '--';

  const scoreClass = (s: number | null) => {
    if (!s) return '';
    if (s < 0.3) return 'green';
    if (s < 0.7) return 'medium';
    return 'high';
  };

  return (
    <div className="map-info">
      <h3>Risk Analysis Summary</h3>

      {/* Insurance Oracle Badge */}
      {liveScore !== null && liveScore !== undefined && <InsuranceBadge score={liveScore} />}

      {/* Live Risk Score */}
      <div className="metric" style={{ borderBottom: '1px solid var(--border)', paddingBottom: '10px', marginBottom: '10px' }}>
        <div>
          <div className="metric-label" style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Live Risk Score</div>
          <div className="metric-label" style={{ fontSize: '0.75em', opacity: 0.8 }}>Current conditions</div>
        </div>
        <div className={`metric-value ${scoreClass(liveScore ?? null)}`} style={{ fontSize: '1.4em', fontWeight: 'bold' }}>
          {displayLiveScore}
        </div>
      </div>

      {/* 48-Hour Forecast */}
      <div className="metric" style={{ borderBottom: '1px solid var(--border)', paddingBottom: '15px', marginBottom: '15px' }}>
        <div>
          <div className="metric-label" style={{ fontWeight: 600, color: 'var(--text-primary)' }}>48-Hour Forecast ⚠️</div>
          <div className="metric-label" style={{ fontSize: '0.75em', opacity: 0.8 }}>Based on incoming weather</div>
        </div>
        <div className={`metric-value ${scoreClass(futureScore)}`} style={{ fontSize: '1.4em', fontWeight: 'bold' }}>
          {displayFutureScore}
        </div>
      </div>

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <div>
          <div style={{
            fontWeight: 600,
            color: 'var(--text-primary)',
            fontSize: '0.85em',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            marginBottom: '8px',
            fontFamily: "'Space Mono', monospace",
          }}>
            🔧 Drainage Recommendations ({recommendations.length})
          </div>
          {recommendations.map((rec, i) => (
            <RecommendationCard key={i} rec={rec} index={i} />
          ))}
        </div>
      )}

      {/* No analysis state */}
      {!currentAnalysis && (
        <div style={{ color: '#556', fontSize: '0.85em', textAlign: 'center', padding: '20px 0' }}>
          Run an analysis to see recommendations.
        </div>
      )}
    </div>
  );
};
