import { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { MapComponent } from './components/MapComponent';
import { MapInfo } from './components/MapInfo';
import type { AnalysisParams, AnalysisResponse } from './types';

function App() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [jsonOutput, setJsonOutput] = useState(JSON.stringify({ status: "ready" }, null, 2));

  const handleAnalyze = async (params: AnalysisParams) => {
    setLoading(true);
    setJsonOutput(JSON.stringify({ status: "analyzing", ...params }, null, 2));

    try {
      const response = await fetch('http://localhost:8000/v1/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          latitude: params.lat,
          longitude: params.lon,
          radius: params.radius
        })
      });

      if (!response.ok) throw new Error(`API Error: ${response.status}`);

      const data = await response.json();
      setResult(data);
      setJsonOutput(JSON.stringify(data, null, 2));
    } catch (err: any) {
      setJsonOutput(JSON.stringify({ status: "error", message: err.message }, null, 2));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <Sidebar onAnalyze={handleAnalyze} jsonOutput={jsonOutput} loading={loading} />
      <div className="map-container">
        <MapComponent
          center={[result?.environment ? result.input_params?.latitude || 37.77 : 37.77, result?.input_params?.longitude || -122.41]}
          flowPaths={result?.flow_paths}
          key={result?.timestamp}
        />
        <MapInfo result={result} />
      </div>
    </div>
  );
}

export default App;
