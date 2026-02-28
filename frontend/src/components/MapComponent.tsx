import React from 'react';
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

interface MapComponentProps {
  center: [number, number];
  flowPaths: any; // GeoJSON
}

export const MapComponent: React.FC<MapComponentProps> = ({ center, flowPaths }) => {
  const getFlowStyle = (feature: any) => {
    return {
      fillColor: "#00F2FF",
      color: "#111720",
      weight: 2,
      opacity: 1,
      fillOpacity: 1,
      radius: 5
    };
  };

  const pointToLayer = (feature: any, latlng: L.LatLng) => {
    return L.circleMarker(latlng, {
      radius: 5,
      fillColor: "#00F2FF",
      color: "#111720",
      weight: 2,
      opacity: 1,
      fillOpacity: 1
    });
  };

  const onEachFeature = (feature: any, layer: any) => {
    if (feature.properties && feature.properties.intensity) {
      layer.bindPopup(`<strong>Flow Intensity:</strong> ${feature.properties.intensity.toFixed(3)}`);
    }
  };

  return (
    <div className="map-container">
      <MapContainer
        center={center}
        zoom={13}
        style={{ height: '100%', width: '100%' }}
        zoomControl={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.esri.com/">Esri</a>'
          url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
          maxZoom={18}
        />
        {flowPaths && (
          <GeoJSON
            data={flowPaths}
            pointToLayer={pointToLayer}
            onEachFeature={onEachFeature}
          />
        )}
      </MapContainer>
    </div>
  );
};
