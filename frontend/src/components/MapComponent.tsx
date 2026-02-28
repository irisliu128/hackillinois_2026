import React, { useEffect } from 'react';
import { MapContainer, TileLayer, GeoJSON, useMap } from 'react-leaflet';
import { RISK_ZONES } from '../data';
import type { RiskZoneProperties, AnalysisResponse } from '../types';
import 'leaflet/dist/leaflet.css';

interface MapComponentProps {
  currentAnalysis?: AnalysisResponse | null;
}

const MapUpdater: React.FC<{ center: [number, number] }> = ({ center }) => {
  const map = useMap();
  useEffect(() => {
    map.flyTo(center, 14);
  }, [center, map]);
  return null;
};

export const MapComponent: React.FC<MapComponentProps> = ({ currentAnalysis }) => {
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

  // Default center or analysis center
  const center: [number, number] = currentAnalysis
    ? [currentAnalysis.input_params.latitude, currentAnalysis.input_params.longitude]
    : [21.710, 104.878];

  // Which GeoJSON to show
  const geojsonData = currentAnalysis?.flow_paths || RISK_ZONES;

  return (
    <div className="map-container">
      <MapContainer
        center={[21.710, 104.878]}
        zoom={13}
        style={{ height: '100%', width: '100%' }}
        zoomControl={true}
      >
        <MapUpdater center={center} />
        <TileLayer
          attribution='&copy; <a href="https://www.esri.com/">Esri</a>'
          url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
          maxZoom={18}
        />
        {geojsonData && (
          <GeoJSON
            key={currentAnalysis ? 'live' : 'static'} // force re-mount when switching
            data={geojsonData as any}
            style={getRiskStyle}
            onEachFeature={onEachFeature}
          />
        )}
      </MapContainer>
    </div>
  );
};
