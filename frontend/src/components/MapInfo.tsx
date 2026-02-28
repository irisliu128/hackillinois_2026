import React from 'react';

export const MapInfo: React.FC = () => {
  return (
    <div className="map-info">
      <h3>Risk Analysis Summary</h3>
      <div className="metric">
        <div className="metric-label">Overall Risk Score</div>
        <div className="metric-value high">0.71</div>
      </div>
      <div className="metric">
        <div className="metric-label">High Risk Area</div>
        <div className="metric-value high">20.5 ha</div>
      </div>
      <div className="metric">
        <div className="metric-label">Medium Risk Area</div>
        <div className="metric-value medium">41.0 ha</div>
      </div>
      <div className="metric">
        <div className="metric-label">Low Risk Area</div>
        <div className="metric-value green">31.5 ha</div>
      </div>
    </div>
  );
};
