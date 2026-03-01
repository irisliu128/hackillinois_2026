import { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { MapComponent } from './components/MapComponent';
import { MapInfo } from './components/MapInfo';
import type { AnalysisParams, AnalysisResponse } from './types';

function App() {
  const [jsonOutput, setJsonOutput] = useState(JSON.stringify(
    {
      status: "ready",
      endpoint: "POST /v1/analyze"
    },
    null,
    2
  ));
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [currentAnalysis, setCurrentAnalysis] = useState<AnalysisResponse | null>(null);

  const handleAnalyze = async (params: AnalysisParams) => {
    // 1. Set UI to loading state
    setIsAnalyzing(true);
    setJsonOutput(JSON.stringify({ status: "analyzing...", ...params }, null, 2));

    try {
      // 2. Make the REAL call to your FastAPI backend
      const response = await fetch('http://localhost:8000/v1/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          latitude: params.lat,
          longitude: params.lon,
          radius: params.radius // Match the backend AnalyzeRequest schema
        }),
      });

      const data = await response.json();

      // 3. Update the sidebar with the actual risk score and flow paths
      setJsonOutput(JSON.stringify(data, null, 2));

      // 4. Update the map (Person 4 will use this data to draw lines)
      console.log('Real-time Analysis Received:', data);

      // Update state for MapComponent and MapInfo
      if (data.status === 'success') {
        setCurrentAnalysis(data);
      }

      setIsAnalyzing(false);

    } catch (error) {
      setJsonOutput(JSON.stringify({ status: "error", message: "Backend unreachable", details: String(error) }, null, 2));
      setIsAnalyzing(false);
    }
  };

  // Load default analysis on mount
  useEffect(() => {
    handleAnalyze({ lat: 21.710, lon: 104.878, radius: 5 });
  }, []);

  return (
    <div className="app-container">
      <Sidebar onAnalyze={handleAnalyze} jsonOutput={jsonOutput} isAnalyzing={isAnalyzing} />
      <div className="map-container">
        <MapComponent currentAnalysis={currentAnalysis} />
        <MapInfo currentAnalysis={currentAnalysis} />
      </div>
    </div>
  );
}

export default App;
