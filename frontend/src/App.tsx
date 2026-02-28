import React, { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { MapComponent } from './components/MapComponent';
import { MapInfo } from './components/MapInfo';
import type { AnalysisParams } from './types';

function App() {
  const [jsonOutput, setJsonOutput] = useState(JSON.stringify(
    {
      status: "ready",
      endpoint: "POST /v1/analyze"
    },
    null,
    2
  ));

  const handleAnalyze = (params: AnalysisParams) => {
    const output = {
      status: "analyzing",
      input: {
        lat: params.lat,
        lon: params.lon,
        radius_km: params.radius,
        rainfall_mm: params.rainfall,
        soil_type: params.soil,
        season: params.season
      },
      timestamp: new Date().toISOString()
    };

    setJsonOutput(JSON.stringify(output, null, 2));

    // TODO: Make actual API call when backend is ready
    console.log('Analysis requested:', output);
  };

  return (
    <div className="app-container">
      <Sidebar onAnalyze={handleAnalyze} jsonOutput={jsonOutput} />
      <div className="map-container">
        <MapComponent />
        <MapInfo />
      </div>
    </div>
  );
}

export default App;
