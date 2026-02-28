export interface RiskZoneProperties {
  zone_id: string;
  risk: 'high' | 'medium' | 'low';
  risk_score: number;
  area_ha: number;
}

export interface AnalysisParams {
  lat: number;
  lon: number;
  radius: number;
  rainfall: number;
  season: string;
  soil: string;
}

export interface AnalysisResponse {
  risk_score: number | null;
  flow_paths: any | null; // GeoJSON FeatureCollection
  status: string;
  input_params: {
    latitude: number;
    longitude: number;
    radius: number;
  };
  environment: {
    auto_rainfall_mm: number;
    auto_soil_type: string;
    ndvi: number;
    soil_moisture: number;
    is_burn_zone: boolean;
  };
  metadata: any;
}
