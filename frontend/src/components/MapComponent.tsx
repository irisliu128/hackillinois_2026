import React, { useEffect } from 'react';
import { MapContainer, TileLayer, GeoJSON, Polyline, Marker, useMap, useMapEvents } from 'react-leaflet';
import type { RiskZoneProperties, AnalysisResponse } from '../types';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

interface MapComponentProps {
  currentAnalysis?: AnalysisResponse | null;
  isDrawing: boolean;
  channelPoints: [number, number][];
  onPointAdded: (latlng: [number, number]) => void;
}

// Fix leaflet default marker icon issue in Vite/React
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const MapUpdater: React.FC<{ center: [number, number] }> = ({ center }) => {
  const map = useMap();
  useEffect(() => {
    map.flyTo(center, 14);
  }, [center, map]);
  return null;
};

const DrawHandler: React.FC<{
  isDrawing: boolean;
  onPointAdded: (latlng: [number, number]) => void;
}> = ({ isDrawing, onPointAdded }) => {
  useMapEvents({
    click(e) {
      if (isDrawing) {
        onPointAdded([e.latlng.lat, e.latlng.lng]);
      }
    },
  });
  return null;
};

export const MapComponent: React.FC<MapComponentProps> = ({
  currentAnalysis,
  isDrawing,
  channelPoints,
  onPointAdded,
}) => {
  const getRiskStyle = (feature: any) => {
    const risk = feature.properties.risk;
    let fillColor: string;
    let color: string;

    if (risk === 'high') {
      fillColor = '#FF4B2B';
      color = '#FF4B2B';
    } else if (risk === 'medium') {
      fillColor = '#FFA41B';
      color = '#FFA41B';
    } else {
      fillColor = '#00d4aa';
      color = '#00d4aa';
    }

    return {
      fillColor,
      fillOpacity: 0.35,
      color,
      weight: 2,
      opacity: 0.8,
    };
  };

  const onEachFeature = (feature: any, layer: any) => {
    const props = feature.properties as RiskZoneProperties;
    layer.bindPopup(`
      <div style="font-family: 'DM Sans', sans-serif; font-size: 13px;">
        <strong style="font-family: 'Space Mono', monospace; color: #6b7a96;">${props.zone_id}</strong><br>
        Risk Score: <strong>${props.risk_score}</strong><br>
        Area: <strong>${props.area_ha} ha</strong>
      </div>
    `);
  };

  const center: [number, number] = currentAnalysis
    ? [currentAnalysis.input_params.latitude, currentAnalysis.input_params.longitude]
    : [21.710, 104.878];

  const geojsonData = currentAnalysis?.flow_paths || null;

  // Channel line style
  const channelLineStyle = {
    color: '#4f8ef7',
    weight: 3,
    dashArray: '8 4',
    opacity: 0.9,
  };

  // Recommendation markers from analysis
  const recommendations = currentAnalysis?.recommendations ?? [];

  const recIcon = (isCritical: boolean) =>
    L.divIcon({
      className: '',
      html: `<div style="
        width: 20px; height: 20px;
        background: ${isCritical ? '#FF4B2B' : '#4f8ef7'};
        border: 2px solid white;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 10px;
        box-shadow: 0 0 6px ${isCritical ? '#FF4B2B' : '#4f8ef7'};
      ">🔧</div>`,
      iconSize: [20, 20],
      iconAnchor: [10, 10],
    });

  return (
    <div className="map-container" style={{ cursor: isDrawing ? 'crosshair' : 'grab' }}>
      <MapContainer
        center={[21.710, 104.878]}
        zoom={13}
        style={{ height: '100%', width: '100%' }}
        zoomControl={true}
      >
        <MapUpdater center={center} />
        <DrawHandler isDrawing={isDrawing} onPointAdded={onPointAdded} />

        <TileLayer
          attribution='&copy; <a href="https://www.esri.com/">Esri</a>'
          url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
          maxZoom={18}
        />

        {/* Flow paths from terrain pipeline */}
        {geojsonData && (
          <GeoJSON
            key={currentAnalysis ? 'live' : 'static'}
            data={geojsonData as any}
            style={getRiskStyle}
            onEachFeature={onEachFeature}
          />
        )}

        {/* Proposed diversion channel */}
        {channelPoints.length >= 2 && (
          <Polyline positions={channelPoints} pathOptions={channelLineStyle} />
        )}

        {/* Recommendation markers */}
        {recommendations.map((rec, i) => (
          <Marker
            key={i}
            position={rec.coords as [number, number]}
            icon={recIcon(rec.critical_diversion_point)}
          >
          </Marker>
        ))}
      </MapContainer>

      {/* Draw mode overlay hint */}
      {isDrawing && (
        <div style={{
          position: 'absolute',
          top: '10px',
          left: '50%',
          transform: 'translateX(-50%)',
          padding: '6px 14px',
          background: '#00d4aadd',
          color: '#000',
          borderRadius: '20px',
          fontWeight: 700,
          fontSize: '0.8em',
          pointerEvents: 'none',
          zIndex: 1000,
          fontFamily: "'Space Mono', monospace",
        }}>
          ✏️ Click to place channel points · {channelPoints.length} placed
        </div>
      )}
    </div>
  );
};
