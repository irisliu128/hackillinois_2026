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
}

export interface Recommendation {
  type: string;
  coords: [number, number];  // [lat, lon]
  dimensions: string;
  impact: string;
  reasoning: string;
  critical_diversion_point: boolean;
  accum_value: number;
  slope_degrees: number;
}

export interface AnalysisResponse {
  risk_score: number | null;
  risk_forecast?: number[] | null;
  flow_paths: any | null; // GeoJSON FeatureCollection
  recommendations?: Recommendation[];
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

export interface SimulateResponse {
  status: string;
  pre_intervention_score: number;
  post_intervention_score: number;
  risk_delta: number;
  pct_reduction: number;
  channel_coords: [number, number][];
  intervention_strength: number;
  recommendations: Recommendation[];
  metadata: {
    lat: number;
    lon: number;
    rainfall_mm: number;
    soil_type: string;
    processing_time_s: number;
    timestamp: string;
  };
}
