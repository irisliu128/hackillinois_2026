import React from 'react';
import { MapContainer, TileLayer, GeoJSON, Popup } from 'react-leaflet';
import { RISK_ZONES } from '../data';
import type { RiskZoneProperties } from '../types';
import 'leaflet/dist/leaflet.css';

export const MapComponent: React.FC = () => {
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

  return (
    <div className="map-container">
      <MapContainer
        center={[21.710, 104.878]}
        zoom={13}
        style={{ height: '100%', width: '100%' }}
        zoomControl={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.esri.com/">Esri</a>'
          url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
          maxZoom={18}
        />
        <GeoJSON
          data={RISK_ZONES as any}
          style={getRiskStyle}
          onEachFeature={onEachFeature}
        />
      </MapContainer>
    </div>
  );
};
