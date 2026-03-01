import React, { useState, useEffect, useRef } from 'react';
import type { AnalysisParams } from '../types';

interface SidebarProps {
  onAnalyze: (params: AnalysisParams) => void;
  analysisLogs: string[];
  isAnalyzing: boolean;
  children?: React.ReactNode;
}

export const Sidebar: React.FC<SidebarProps> = ({ onAnalyze, analysisLogs, isAnalyzing, children }) => {
  const [latStr, setLatStr] = useState("21.710");
  const [lonStr, setLonStr] = useState("104.878");
  const [radius, setRadius] = useState(5);
  const logsEndRef = useRef<HTMLDivElement>(null);

  const handleAnalyze = () => {
    onAnalyze({ lat: parseFloat(latStr), lon: parseFloat(lonStr), radius });
  };

  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [analysisLogs]);

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
        {isAnalyzing ? '⏳ STREAMING ANALYSIS...' : '▶ RUN ANALYSIS'}
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

      <div className="section-header">Live Terminal</div>
      <div className="json-output" style={{
        background: '#0a0a0f', color: '#00ffcc', fontFamily: 'monospace',
        padding: '10px', height: '180px', overflowY: 'auto', display: 'flex',
        flexDirection: 'column', gap: '4px', fontSize: '11px',
        border: '1px solid #1a2b3c', borderRadius: '4px'
      }}>
        {analysisLogs.length === 0 ? (
          <span style={{ color: '#556' }}>&gt; Ready to start engine...</span>
        ) : (
          analysisLogs.map((log, i) => (
            <div key={i} style={{ display: 'flex' }}>
              <span style={{ color: '#445', marginRight: '6px' }}>&gt;</span>
              <span>{log}</span>
            </div>
          ))
        )}
        {isAnalyzing && (
          <div style={{ animation: 'blink 1s step-end infinite' }}>█</div>
        )}
        <div ref={logsEndRef} />
      </div>
      <style>{`
        @keyframes blink {
          50% { opacity: 0; }
        }
      `}</style>
      {children}
    </div>
  );
};
