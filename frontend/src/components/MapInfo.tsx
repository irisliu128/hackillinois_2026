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
      <div className="metric">
        <div className="metric-label">High Risk Area</div>
        <div className="metric-value high">{currentAnalysis ? "--" : "20.5"} ha</div>
      </div>
      <div className="metric">
        <div className="metric-label">Medium Risk Area</div>
        <div className="metric-value medium">{currentAnalysis ? "--" : "41.0"} ha</div>
      </div>
      <div className="metric">
        <div className="metric-label">Low Risk Area</div>
        <div className="metric-value green">{currentAnalysis ? "--" : "31.5"} ha</div>
      </div>
    </div>
  );
};
