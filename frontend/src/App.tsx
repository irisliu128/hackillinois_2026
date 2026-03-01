import { useState, useCallback } from 'react';
import { Sidebar } from './components/Sidebar';
import { MapComponent } from './components/MapComponent';
import { MapInfo } from './components/MapInfo';
import { SimulatePanel } from './components/SimulatePanel';
import type { AnalysisParams, AnalysisResponse, SimulateResponse } from './types';

function App() {
  const [analysisLogs, setAnalysisLogs] = useState<string[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [currentAnalysis, setCurrentAnalysis] = useState<AnalysisResponse | null>(null);

  // Simulation state
  const [isDrawing, setIsDrawing] = useState(false);
  const [channelPoints, setChannelPoints] = useState<[number, number][]>([]);
  const [simulationResult, setSimulationResult] = useState<SimulateResponse | null>(null);
  const [isSimulating, setIsSimulating] = useState(false);

  // ── Analysis (SSE stream) ──────────────────────────────────────────────────
  const handleAnalyze = async (params: AnalysisParams) => {
    setIsAnalyzing(true);
    setAnalysisLogs(['Initializing Analysis Engine...']);
    setSimulationResult(null);
    setChannelPoints([]);

    try {
      const response = await fetch('http://localhost:8000/v1/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify({
          latitude: params.lat,
          longitude: params.lon,
          radius: params.radius,
        }),
      });

      if (!response.body) throw new Error('ReadableStream not supported by browser.');

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let streamData = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        streamData += decoder.decode(value, { stream: true });
        const lines = streamData.split('\n\n');
        streamData = lines.pop() || '';

        for (const line of lines) {
          if (line.trim().startsWith('data:')) {
            const jsonStr = line.replace('data:', '').trim();
            if (!jsonStr) continue;
            try {
              const parsed = JSON.parse(jsonStr);
              if (parsed.log) {
                setAnalysisLogs(prev => [...prev, parsed.log]);
              } else if (parsed.error) {
                setAnalysisLogs(prev => [...prev, `[ERROR] ${parsed.error} - ${parsed.detail || ''}`]);
              } else if (parsed.status === 'success') {
                setAnalysisLogs(prev => [...prev, 'Engine Shutdown. Rendering map...']);
                setCurrentAnalysis(parsed);
              }
            } catch (e) {
              console.error('Failed to parse SSE line', line, e);
            }
          }
        }
      }
      setIsAnalyzing(false);
    } catch (error) {
      setAnalysisLogs(prev => [...prev, `[FATAL ERROR] Backend unreachable: ${String(error)}`]);
      setIsAnalyzing(false);
    }
  };

  // ── Draw mode handlers ─────────────────────────────────────────────────────
  const handleStartDraw = useCallback(() => {
    setIsDrawing(true);
    setChannelPoints([]);
    setSimulationResult(null);
  }, []);

  const handleClearDraw = useCallback(() => {
    setIsDrawing(false);
    setChannelPoints([]);
    setSimulationResult(null);
  }, []);

  const handlePointAdded = useCallback((latlng: [number, number]) => {
    setChannelPoints(prev => [...prev, latlng]);
  }, []);

  // ── Simulation ─────────────────────────────────────────────────────────────
  const handleSimulate = async (coords: [number, number][]) => {
    if (!currentAnalysis || coords.length < 2) return;
    setIsSimulating(true);
    setIsDrawing(false); // exit draw mode

    // Build GeoJSON LineString: coords are [lat, lon], GeoJSON needs [lon, lat]
    const geojsonLine = {
      type: 'LineString',
      coordinates: coords.map(([lat, lon]) => [lon, lat]),
    };

    try {
      const resp = await fetch('http://localhost:8000/v1/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          latitude: currentAnalysis.input_params.latitude,
          longitude: currentAnalysis.input_params.longitude,
          proposed_channel: geojsonLine,
          intervention_strength: 0.5,
        }),
      });

      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data: SimulateResponse = await resp.json();
      setSimulationResult(data);
    } catch (err) {
      console.error('Simulation failed:', err);
    } finally {
      setIsSimulating(false);
    }
  };

  return (
    <div className="app-container">
      <Sidebar onAnalyze={handleAnalyze} analysisLogs={analysisLogs} isAnalyzing={isAnalyzing}>
        {/* What-If Simulation panel appended inside Sidebar */}
        <SimulatePanel
          isDrawing={isDrawing}
          channelPoints={channelPoints}
          onStartDraw={handleStartDraw}
          onClearDraw={handleClearDraw}
          simulationResult={simulationResult}
          isSimulating={isSimulating}
          onSimulate={handleSimulate}
        />
      </Sidebar>
      <div className="map-container">
        <MapComponent
          currentAnalysis={currentAnalysis}
          isDrawing={isDrawing}
          channelPoints={channelPoints}
          onPointAdded={handlePointAdded}
        />
        <MapInfo
          currentAnalysis={currentAnalysis}
        />
      </div>
    </div>
  );
}

export default App;
