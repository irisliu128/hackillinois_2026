import React from 'react';
import type { SimulateResponse } from '../types';

interface SimulatePanelProps {
    isDrawing: boolean;
    channelPoints: [number, number][];
    onStartDraw: () => void;
    onClearDraw: () => void;
    simulationResult: SimulateResponse | null;
    isSimulating: boolean;
    onSimulate: (coords: [number, number][]) => void;
}

export const SimulatePanel: React.FC<SimulatePanelProps> = ({
    isDrawing,
    channelPoints,
    onStartDraw,
    onClearDraw,
    simulationResult,
    isSimulating,
    onSimulate,
}) => {
    const hasChannel = channelPoints.length >= 2;

    const scoreColor = (score: number) => {
        if (score < 0.3) return '#00d4aa';
        if (score < 0.7) return '#FFA41B';
        return '#FF4B2B';
    };

    return (
        <div style={{ marginTop: '12px' }}>
            <div className="section-header">🔧 What-If Simulation</div>

            <div style={{ padding: '0 15px 10px', fontSize: '0.8em', color: '#8b9bb4', lineHeight: '1.4' }}>
                Draw a proposed diversion channel on the map to see how it reduces downstream risk in real-time.
            </div>

            <div style={{ padding: '0 15px 12px', display: 'flex', gap: '8px' }}>
                <button
                    onClick={isDrawing ? onClearDraw : onStartDraw}
                    style={{
                        flex: 1,
                        padding: '8px 0',
                        background: isDrawing ? '#ff4b2b22' : '#00d4aa22',
                        border: `1px solid ${isDrawing ? '#FF4B2B' : '#00d4aa'}`,
                        borderRadius: '4px',
                        color: isDrawing ? '#FF4B2B' : '#00d4aa',
                        cursor: 'pointer',
                        fontFamily: "'Space Mono', monospace",
                        fontSize: '0.75em',
                        fontWeight: 600,
                    }}
                >
                    {isDrawing ? '✕ Cancel Draw' : '✏️ Draw Channel'}
                </button>

                {hasChannel && (
                    <button
                        onClick={() => onSimulate(channelPoints)}
                        disabled={isSimulating}
                        style={{
                            flex: 1,
                            padding: '8px 0',
                            background: isSimulating ? '#1a2b3c' : '#4f8ef744',
                            border: '1px solid #4f8ef7',
                            borderRadius: '4px',
                            color: '#4f8ef7',
                            cursor: isSimulating ? 'not-allowed' : 'pointer',
                            fontFamily: "'Space Mono', monospace",
                            fontSize: '0.75em',
                            fontWeight: 600,
                            opacity: isSimulating ? 0.6 : 1,
                        }}
                    >
                        {isSimulating ? '⏳ Running...' : '▶ Simulate'}
                    </button>
                )}
            </div>

            {isDrawing && (
                <div style={{
                    margin: '0 15px 10px',
                    padding: '8px',
                    background: '#00d4aa11',
                    border: '1px dashed #00d4aa55',
                    borderRadius: '4px',
                    fontSize: '0.78em',
                    color: '#00d4aa',
                    textAlign: 'center',
                }}>
                    Click on the map to place channel points ({channelPoints.length} placed).<br />
                    {channelPoints.length >= 2 && <span style={{ color: '#FFA41B' }}>Ready to simulate!</span>}
                </div>
            )}

            {simulationResult && (
                <div style={{ padding: '0 15px 10px' }}>
                    <div style={{
                        background: '#0d1929',
                        border: '1px solid #1a2b4a',
                        borderRadius: '6px',
                        padding: '12px',
                    }}>
                        <div style={{ fontSize: '0.75em', color: '#8b9bb4', marginBottom: '8px', fontFamily: "'Space Mono', monospace" }}>
                            INTERVENTION IMPACT
                        </div>

                        <div style={{ display: 'flex', gap: '8px', marginBottom: '10px' }}>
                            <div style={{ flex: 1, textAlign: 'center', padding: '8px', background: '#0a0a0f', borderRadius: '4px', border: '1px solid #1a2b3c' }}>
                                <div style={{ fontSize: '0.7em', color: '#556', marginBottom: '2px' }}>BEFORE</div>
                                <div style={{ fontSize: '1.4em', fontWeight: 700, color: scoreColor(simulationResult.pre_intervention_score), fontFamily: "'Space Mono', monospace" }}>
                                    {simulationResult.pre_intervention_score.toFixed(3)}
                                </div>
                            </div>

                            <div style={{ display: 'flex', alignItems: 'center', color: '#00d4aa', fontSize: '1.2em' }}>→</div>

                            <div style={{ flex: 1, textAlign: 'center', padding: '8px', background: '#0a0a0f', borderRadius: '4px', border: '1px solid #1a2b3c' }}>
                                <div style={{ fontSize: '0.7em', color: '#556', marginBottom: '2px' }}>AFTER</div>
                                <div style={{ fontSize: '1.4em', fontWeight: 700, color: scoreColor(simulationResult.post_intervention_score), fontFamily: "'Space Mono', monospace" }}>
                                    {simulationResult.post_intervention_score.toFixed(3)}
                                </div>
                            </div>
                        </div>

                        <div style={{
                            textAlign: 'center',
                            padding: '6px',
                            background: '#00d4aa15',
                            border: '1px solid #00d4aa33',
                            borderRadius: '4px',
                            fontSize: '0.85em',
                            color: '#00d4aa',
                            fontWeight: 600,
                        }}>
                            ↓ {simulationResult.pct_reduction}% risk reduction via proposed channel
                        </div>

                        <div style={{ marginTop: '8px', fontSize: '0.72em', color: '#556', textAlign: 'center', fontFamily: "'Space Mono', monospace" }}>
                            Δ = {simulationResult.risk_delta > 0 ? '-' : '+'}{Math.abs(simulationResult.risk_delta).toFixed(4)} | {channelPoints.length} waypoints
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
