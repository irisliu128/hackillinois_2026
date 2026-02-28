export interface EnvironmentData {
  auto_rainfall_mm: number;
  auto_soil_type: string;
  ndvi: number;
  soil_moisture: number;
  is_burn_zone: boolean;
}

export interface AnalysisParams {
  lat: number;
  lon: number;
  radius: number;
}

export interface AnalysisResponse {
  risk_score: number;
  flow_paths: any; // GeoJSON
  environment: EnvironmentData;
  status: string;
  timestamp: string;
  input_params: {
    latitude: number;
    longitude: number;
    radius: number;
  };
}
