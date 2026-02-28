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
  status: string;
  input: AnalysisParams;
  timestamp: string;
}
