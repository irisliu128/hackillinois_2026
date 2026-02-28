import React from 'react';
import type { AnalysisResponse } from '../types';

interface MapInfoProps {
  result: AnalysisResponse | null;
}

export const MapInfo: React.FC<MapInfoProps> = ({ result }) => {
  if (!result) {
    return (
      <div className="map-info">
        <h3>Risk Analysis Summary</h3>
        <p style={{ color: '#6b7a96', fontSize: '0.9rem' }}>Run an analysis to see insights...</p>
      </div>
    );
  }

  const score = result.risk_score || 0;
  const env = result.environment || {};

  const getRiskClass = (s: number) => {
    if (s > 0.7) return 'high';
    if (s > 0.4) return 'medium';
    return 'green';
  };

  return (
    <div className="map-info">
      <h3>Risk Analysis Summary</h3>

      <div className="metric">
        <div className="metric-label">Overall Risk Score</div>
        <div className={`metric-value ${getRiskClass(score)}`}>{score.toFixed(2)}</div>
      </div>

      <div className="metric">
        <div className="metric-label">Detected Soil</div>
        <div className="metric-value blue" style={{ fontSize: '0.9rem' }}>
          {(env.auto_soil_type || 'Unknown').toUpperCase()}
        </div>
      </div>

      <div className="metric">
        <div className="metric-label">Live Rainfall</div>
        <div className="metric-value blue" style={{ fontSize: '0.9rem' }}>
          {env.auto_rainfall_mm || 0} mm
        </div>
      </div>

      <div className="metric">
        <div className="metric-label">Vegetation (NDVI)</div>
        <div className="metric-value" style={{ fontSize: '0.9rem', color: '#00FF41' }}>
          {(env.ndvi * 100).toFixed(1)}%
        </div>
      </div>

      <div className="metric">
        <div className="metric-label">Ground Saturation</div>
        <div className="metric-value" style={{ fontSize: '0.9rem', color: '#00F2FF' }}>
          {(env.soil_moisture * 100).toFixed(1)}%
        </div>
      </div>

      {env.is_burn_zone && (
        <div className="metric" style={{ border: '1px solid #FF4B2B', padding: '4px', borderRadius: '4px', marginTop: '8px' }}>
          <div className="metric-label" style={{ color: '#FF4B2B', fontWeight: 'bold' }}>🔥 BURN ZONE</div>
          <div className="metric-value" style={{ color: '#FF4B2B' }}>ACTIVE</div>
        </div>
      )}
    </div>
  );
};
