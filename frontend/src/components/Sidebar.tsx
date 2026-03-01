import React, { useState } from 'react';
import type { AnalysisParams } from '../types';

interface SidebarProps {
  onAnalyze: (params: AnalysisParams) => void;
  jsonOutput: string;
  isAnalyzing: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({ onAnalyze, jsonOutput, isAnalyzing }) => {
  const [lat, setLat] = useState(-13.1631);
  const [lon, setLon] = useState(-72.5450);
  const [radius, setRadius] = useState(5);

  const handleAnalyze = () => {
    onAnalyze({ lat, lon, radius });
  };

  return (
    <div className="sidebar">
      <div className="logo">Terra<span>Sight</span></div>
      <div className="tagline">Decision Support for Agricultural NGOs</div>
      <span className="status-badge">● LIVE MODE</span>

      <div className="section-header">Target Region</div>
      <div className="input-group">
        <label className="input-label">Latitude</label>
        <input
          type="number"
          value={lat}
          onChange={(e) => setLat(parseFloat(e.target.value))}
          step="0.001"
        />
      </div>
      <div className="input-group">
        <label className="input-label">Longitude</label>
        <input
          type="number"
          value={lon}
          onChange={(e) => setLon(parseFloat(e.target.value))}
          step="0.001"
        />
      </div>
      <div className="input-group">
        <label className="input-label">Analysis Radius</label>
        <select value={radius} onChange={(e) => setRadius(parseInt(e.target.value))}>
          <option value={2}>2 km</option>
          <option value={5}>5 km</option>
          <option value={10}>10 km</option>
          <option value={25}>25 km</option>
        </select>
      </div>

      <div className="section-header">🌍 V4.1 Autonomous Engine</div>
      <div style={{ padding: '0 15px 15px 15px', color: '#8b9bb4', fontSize: '0.85em', lineHeight: '1.4' }}>
        TerraSight automatically detects dynamic environmental variables for any coordinate:
        <ul style={{ paddingLeft: '15px', marginTop: '5px' }}>
          <li><b>7-Day Rainfall</b> via Open-Meteo</li>
          <li><b>Soil Content</b> via ISRIC SoilGrids</li>
          <li><b>Urban Infrastructure</b> via OpenStreetMap</li>
          <li><b>NDVI & Moisture</b> via Google Earth Engine</li>
        </ul>
      </div>

      <button className="btn-analyze" onClick={handleAnalyze} disabled={isAnalyzing}>
        {isAnalyzing ? '⏳ ANALYZING (GEE takes 10-20s)...' : '▶ RUN ANALYSIS'}
      </button>

      <div className="section-header">Legend</div>
      <div className="legend-item">
        <div className="legend-dot" style={{ background: '#FF4B2B' }}></div>
        <span>High Risk Zone (mudslide)</span>
      </div>
      <div className="legend-item">
        <div className="legend-dot" style={{ background: '#FFA41B' }}></div>
        <span>Medium Risk Zone</span>
      </div>
      <div className="legend-item">
        <div className="legend-dot" style={{ background: '#00d4aa' }}></div>
        <span>Low Risk Zone</span>
      </div>

      <div className="section-header">API Response (Live)</div>
      <div className="json-output">{jsonOutput}</div>
    </div>
  );
};
