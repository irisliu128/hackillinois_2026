import React, { useState } from 'react';
import type { AnalysisParams } from '../types';

interface SidebarProps {
  onAnalyze: (params: AnalysisParams) => void;
  jsonOutput: string;
  isAnalyzing: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({ onAnalyze, jsonOutput, isAnalyzing }) => {
  const [latStr, setLatStr] = useState("21.710");
  const [lonStr, setLonStr] = useState("104.878");
  const [radius, setRadius] = useState(5);

  const handleAnalyze = () => {
    onAnalyze({ lat: parseFloat(latStr), lon: parseFloat(lonStr), radius });
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
          value={latStr}
          onChange={(e) => setLatStr(e.target.value)}
          step="0.001"
        />
      </div>
      <div className="input-group">
        <label className="input-label">Longitude</label>
        <input
          type="number"
          value={lonStr}
          onChange={(e) => setLonStr(e.target.value)}
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

      <div className="section-header">API Response (Live)</div>
      <div className="json-output">{jsonOutput}</div>
    </div>
  );
};
