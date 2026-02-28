import React, { useState } from 'react';
import type { AnalysisParams } from '../types';

interface SidebarProps {
  onAnalyze: (params: AnalysisParams) => void;
  jsonOutput: string;
  loading: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({ onAnalyze, jsonOutput, loading }) => {
  const [lat, setLat] = useState(37.7749);
  const [lon, setLon] = useState(-122.4194);
  const [radius, setRadius] = useState(5);

  const handleAnalyze = () => {
    onAnalyze({ lat, lon, radius });
  };

  return (
    <div className="sidebar">
      <div className="logo">Terra<span>Sight</span></div>
      <div className="tagline">Global Hazard Intelligence Platform</div>
      <span className="status-badge" style={{ background: loading ? '#FFA41B' : '#00d4aa' }}>
        ● {loading ? 'ANALYZING...' : 'SYSTEM READY'}
      </span>

      <div className="section-header">Target Region</div>
      <div className="input-group">
        <label className="input-label">Latitude</label>
        <input
          type="number"
          value={lat}
          onChange={(e) => setLat(parseFloat(e.target.value))}
          step="0.0001"
        />
      </div>
      <div className="input-group">
        <label className="input-label">Longitude</label>
        <input
          type="number"
          value={lon}
          onChange={(e) => setLon(parseFloat(e.target.value))}
          step="0.0001"
        />
      </div>
      <div className="input-group">
        <label className="input-label">Analysis Radius</label>
        <select value={radius} onChange={(e) => setRadius(parseInt(e.target.value))}>
          <option value={2}>2 km</option>
          <option value={5}>5 km</option>
          <option value={10}>10 km</option>
        </select>
      </div>

      <div className="section-header">Automated Intelligence</div>
      <div className="info-box">
        <p>⚡ <strong>Live Weather:</strong> Auto-detected</p>
        <p>🔬 <strong>Soil Texture:</strong> Auto-detected</p>
        <p>🛰️ <strong>Satellite Indices:</strong> Live Fusion</p>
      </div>

      <button
        className="btn-analyze"
        onClick={handleAnalyze}
        disabled={loading}
        style={{ opacity: loading ? 0.6 : 1, cursor: loading ? 'not-allowed' : 'pointer' }}
      >
        {loading ? 'PROCESSING...' : '▶ RUN ANALYSIS'}
      </button>

      <div className="section-header">Visualizer Legend</div>
      <div className="legend-item">
        <div className="legend-dot" style={{ background: '#00F2FF' }}></div>
        <span>Hydrological Flow Path</span>
      </div>
      <div className="legend-item">
        <div className="legend-dot" style={{ background: '#FF4B2B' }}></div>
        <span>Critical Soil Slope</span>
      </div>

      <div className="section-header">API JSON (Debug)</div>
      <pre className="json-output" style={{ fontSize: '10px', maxHeight: '200px', overflow: 'auto' }}>
        {jsonOutput}
      </pre>
    </div>
  );
};
