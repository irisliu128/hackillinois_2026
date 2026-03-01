import React from 'react';
import type { AnalysisResponse } from '../types';

interface MapInfoProps {
  currentAnalysis?: AnalysisResponse | null;
}

export const MapInfo: React.FC<MapInfoProps> = ({ currentAnalysis }) => {
  const score = currentAnalysis?.risk_score;
  const displayScore = score !== undefined && score !== null ? score.toFixed(4) : "0.71";

  // Decide color based on score
  let scoreClass = "high";
  if (score && score < 0.3) scoreClass = "green";
  else if (score && score < 0.7) scoreClass = "medium";

  return (
    <div className="map-info">
      <h3>Risk Analysis Summary</h3>
      <div className="metric">
        <div className="metric-label">Overall Risk Score</div>
        <div className={`metric-value ${scoreClass}`}>{displayScore}</div>
      </div>

      <div style={{ marginTop: '20px' }}>
        <div style={{ fontSize: '0.9em', fontWeight: '600', color: '#8b9bb4', marginBottom: '10px' }}>Legend</div>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
          <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#FF4B2B', marginRight: '8px' }}></div>
          <span style={{ fontSize: '0.85em', color: '#d1dae6' }}>High Risk Zone (mudslide)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
          <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#FFA41B', marginRight: '8px' }}></div>
          <span style={{ fontSize: '0.85em', color: '#d1dae6' }}>Medium Risk Zone</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#00d4aa', marginRight: '8px' }}></div>
          <span style={{ fontSize: '0.85em', color: '#d1dae6' }}>Low Risk Zone</span>
        </div>
      </div>
    </div>
  );
};
