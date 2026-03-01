import React from 'react';

interface ApiDocsProps {
    onClose: () => void;
}

export const ApiDocs: React.FC<ApiDocsProps> = ({ onClose }) => {
    return (
        <div className="api-docs-container">
            <div className="docs-header">
                <h2>TerraSight API Reference</h2>
                <button className="btn-close-docs" onClick={onClose}>Close Docs</button>
            </div>

            <div className="docs-content">
                <div className="docs-section">
                    <h3><span className="method get">GET</span> /v1/health</h3>
                    <p>Validates system connectivity and confirms the Terrain Engine (WhiteboxTools/GEE) is ready.</p>
                    <div className="code-block">
                        <pre>
                            {`{
  "status": "ok",
  "terrain_engine": true,
  "timestamp": "2026-03-01T07:53:24Z"
}`}
                        </pre>
                    </div>
                </div>

                <div className="docs-section">
                    <h3><span className="method post">POST</span> /v1/analyze</h3>
                    <p>The core engine of TerraSight. Calculates landslide susceptibility by merging NASA Landslide Catalog heuristics with live environmental data.</p>
                    <h4>Request Body</h4>
                    <table className="docs-table">
                        <thead>
                            <tr><th>Parameter</th><th>Type</th><th>Constraints</th></tr>
                        </thead>
                        <tbody>
                            <tr><td>latitude</td><td>number</td><td>[-90.0, 90.0]</td></tr>
                            <tr><td>longitude</td><td>number</td><td>[-180.0, 180.0]</td></tr>
                            <tr><td>radius</td><td>number</td><td>&gt; 0 km</td></tr>
                        </tbody>
                    </table>
                    <h4>Response (200 OK)</h4>
                    <div className="code-block">
                        <pre>
                            {`{
  "risk_score": 0.84,
  "flow_paths": null,
  "environment": {
    "auto_rainfall_mm": 45.5,
    "auto_soil_type": "clay",
    "ndvi": 0.35,
    "soil_moisture": 0.45,
    "is_burn_zone": false
  },
  "status": "success",
  "metadata": {
    "processing_time_s": 14.21
  }
}`}
                        </pre>
                    </div>
                </div>

                <div className="docs-section">
                    <h3><span className="method post">POST</span> /v1/settings</h3>
                    <p>Initializes a new user session for adaptive polling.</p>
                    <h4>Request Body</h4>
                    <div className="code-block">
                        <pre>
                            {`{
  "polling_interval_minutes": 1440,
  "auto_scale": true
}`}
                        </pre>
                    </div>
                </div>

                <div className="docs-section">
                    <h3><span className="method post">POST</span> /v1/poll</h3>
                    <p>Manually forces an adaptive evaluation. Asynchronous "fire and forget".</p>
                    <div className="code-block">
                        <pre>
                            {`{
  "latitude": 22.57,
  "longitude": 88.36,
  "session_id": "optional-string"
}`}
                        </pre>
                    </div>
                </div>
            </div>
        </div>
    );
};
