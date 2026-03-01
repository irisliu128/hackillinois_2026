import { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { MapComponent } from './components/MapComponent';
import { MapInfo } from './components/MapInfo';
import type { AnalysisParams, AnalysisResponse } from './types';

function App() {
  const [analysisLogs, setAnalysisLogs] = useState<string[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [currentAnalysis, setCurrentAnalysis] = useState<AnalysisResponse | null>(null);

  const handleAnalyze = async (params: AnalysisParams) => {
    // 1. Set UI to analyzing state
    setIsAnalyzing(true);
    setAnalysisLogs(["Initializing Analysis Engine..."]);

    try {
      // 2. Make the Streaming call to your FastAPI backend
      const response = await fetch('http://localhost:8000/v1/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream'
        },
        body: JSON.stringify({
          latitude: params.lat,
          longitude: params.lon,
          radius: params.radius
        }),
      });

      if (!response.body) {
        throw new Error("ReadableStream not supported by browser.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let streamData = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        streamData += decoder.decode(value, { stream: true });

        // Process each SSE 'data:' chunk
        const lines = streamData.split('\n\n');
        // The last line might be incomplete, so we keep it in the buffer
        streamData = lines.pop() || "";

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
              } else if (parsed.status === "success") {
                setAnalysisLogs(prev => [...prev, "Engine Shutdown. Rendering map..."]);
                setCurrentAnalysis(parsed);
              }
            } catch (e) {
              console.error("Failed to parse SSE line", line, e);
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

  return (
    <div className="app-container">
      <Sidebar onAnalyze={handleAnalyze} analysisLogs={analysisLogs} isAnalyzing={isAnalyzing} />
      <div className="map-container">
        <MapComponent currentAnalysis={currentAnalysis} />
        <MapInfo currentAnalysis={currentAnalysis} />
      </div>
    </div>
  );
}

export default App;
