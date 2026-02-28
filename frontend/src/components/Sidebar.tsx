import React, { useState } from 'react';
import type { AnalysisParams } from '../types';

interface SidebarProps {
  onAnalyze: (params: AnalysisParams) => void;
  jsonOutput: string;
}

export const Sidebar: React.FC<SidebarProps> = ({ onAnalyze, jsonOutput }) => {
  const [lat, setLat] = useState(21.710);
  const [lon, setLon] = useState(104.878);
  const [radius, setRadius] = useState(5);
  const [rainfall, setRainfall] = useState(1850);
  const [season, setSeason] = useState('monsoon');
  const [soil, setSoil] = useState('auto');

  const handleAnalyze = () => {
    onAnalyze({ lat, lon, radius, rainfall, season, soil });
  };

  return (
    <div className="sidebar">
      <div className="logo">Terra<span>Sight</span></div>
      <div className="tagline">Decision Support for Agricultural NGOs</div>
      <span className="status-badge">● DEMO MODE</span>

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

      <div className="section-header">Rainfall Parameters</div>
      <div className="input-group">
        <label className="input-label">Expected Annual Rainfall</label>
        <input
          type="range"
          min="800"
          max="3000"
          value={rainfall}
          step="50"
          onChange={(e) => setRainfall(parseInt(e.target.value))}
        />
        <span className="slider-value"><span>{rainfall}</span> mm/yr</span>
      </div>
      <div className="input-group">
        <label className="input-label">Season</label>
        <select value={season} onChange={(e) => setSeason(e.target.value)}>
          <option value="monsoon">Monsoon (Jun–Sep)</option>
          <option value="dry">Dry (Oct–Feb)</option>
          <option value="transition">Transition (Mar–May)</option>
        </select>
      </div>

      <div className="section-header">Soil Type</div>
      <div className="input-group">
        <select value={soil} onChange={(e) => setSoil(e.target.value)}>
          <option value="clay_loam">Clay Loam (high runoff)</option>
          <option value="sandy_loam">Sandy Loam (high drainage)</option>
          <option value="silty_clay">Silty Clay (moderate)</option>
          <option value="auto">Auto-detect from coordinates</option>
        </select>
      </div>

      <button className="btn-analyze" onClick={handleAnalyze}>
        ▶ RUN ANALYSIS
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
