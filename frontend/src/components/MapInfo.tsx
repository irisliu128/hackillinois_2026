import React, { useState } from 'react';
import type { AnalysisResponse } from '../types';

interface MapInfoProps {
  currentAnalysis?: AnalysisResponse | null;
}

export const MapInfo: React.FC<MapInfoProps> = ({ currentAnalysis }) => {
  const [forecastDay, setForecastDay] = useState<number>(0);

  const riskForecast = currentAnalysis?.risk_forecast;
  let score = currentAnalysis?.risk_score;

  if (riskForecast && forecastDay > 0 && forecastDay < riskForecast.length) {
    score = riskForecast[forecastDay];
  }

  const displayScore = score !== undefined && score !== null ? score.toFixed(4) : "0.71";

  // Decide color based on score
  let scoreClass = "high";
  if (score && score < 0.3) scoreClass = "green";
  else if (score && score < 0.7) scoreClass = "medium";

  return (
    <div className="map-info">
      <h3>Risk Analysis Summary</h3>

      {riskForecast && riskForecast.length > 0 && (
        <div className="forecast-slider" style={{ marginBottom: "20px", paddingBottom: "15px", borderBottom: "1px solid var(--border)" }}>
          <label style={{ display: "block", fontSize: "0.85em", color: "var(--text-muted)", marginBottom: "8px", fontWeight: 600 }}>
            Timeline: {forecastDay === 0 ? "Live (Today)" : `+${forecastDay} Day${forecastDay > 1 ? 's' : ''} Forecast`}
          </label>
          <input
            type="range"
            min="0"
            max={riskForecast.length - 1}
            value={forecastDay}
            onChange={(e) => setForecastDay(parseInt(e.target.value))}
            style={{ width: "100%", cursor: "pointer", accentColor: "var(--accent-teal)" }}
          />
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.7em", color: "var(--text-muted)", marginTop: "4px" }}>
            <span>Today</span>
            <span>+6 Days</span>
          </div>
        </div>
      )}

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
