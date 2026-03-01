import React from 'react';
import type { AnalysisResponse } from '../types';

interface MapInfoProps {
  currentAnalysis?: AnalysisResponse | null;
}

export const MapInfo: React.FC<MapInfoProps> = ({ currentAnalysis }) => {
  const riskForecast = currentAnalysis?.risk_forecast;
  const liveScore = currentAnalysis?.risk_score;
  const futureScore = riskForecast && riskForecast.length > 2 ? riskForecast[2] : null;

  const displayLiveScore = liveScore !== undefined && liveScore !== null ? liveScore.toFixed(4) : "--";
  const displayFutureScore = futureScore !== undefined && futureScore !== null ? futureScore.toFixed(4) : "--";

  // Decide color based on live score
  let liveScoreClass = "high";
  if (liveScore && liveScore < 0.3) liveScoreClass = "green";
  else if (liveScore && liveScore < 0.7) liveScoreClass = "medium";

  // Decide color based on future score
  let futureScoreClass = "high";
  if (futureScore && futureScore < 0.3) futureScoreClass = "green";
  else if (futureScore && futureScore < 0.7) futureScoreClass = "medium";
  else if (!futureScore) futureScoreClass = ""; // default when null

  return (
    <div className="map-info">
      <h3>Risk Analysis Summary</h3>

      <div className="metric" style={{ borderBottom: "1px solid var(--border)", paddingBottom: "10px", marginBottom: "10px" }}>
        <div>
          <div className="metric-label" style={{ fontWeight: 600, color: "var(--text-primary)" }}>Live Risk Score</div>
          <div className="metric-label" style={{ fontSize: "0.75em", opacity: 0.8 }}>Current conditions</div>
        </div>
        <div className={`metric-value ${liveScoreClass}`} style={{ fontSize: "1.4em", fontWeight: "bold" }}>{displayLiveScore}</div>
      </div>

      <div className="metric" style={{ borderBottom: "1px solid var(--border)", paddingBottom: "15px", marginBottom: "15px" }}>
        <div>
          <div className="metric-label" style={{ fontWeight: 600, color: "var(--text-primary)" }}>48-Hour Forecast ⚠️</div>
          <div className="metric-label" style={{ fontSize: "0.75em", opacity: 0.8 }}>Based on incoming weather</div>
        </div>
        <div className={`metric-value ${futureScoreClass}`} style={{ fontSize: "1.4em", fontWeight: "bold" }}>{displayFutureScore}</div>
      </div>

    </div>
  );
};
