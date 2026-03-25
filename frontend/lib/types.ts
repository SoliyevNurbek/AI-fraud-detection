export type LoginResponse = {
  access_token: string;
  token_type: string;
};

export type ApiErrorShape = {
  detail?: string;
  message?: string;
  error?: string;
};

export type AlertItem = {
  id?: string;
  alert_id?: string;
  severity: string;
  status: string;
  title: string;
  description: string;
  risk_score: number;
  created_at: string;
};

export type TrendPoint = {
  label: string;
  value: number;
};

export type CountryPoint = {
  country_code: string;
  count: number;
  avg_risk: number;
};

export type DashboardSummary = {
  transactions: number;
  alerts: number;
  high_risk: number;
  blocked: number;
  recent_reviews: number;
  average_risk: number;
  model_version: string;
  trend: TrendPoint[];
  countries: CountryPoint[];
};

export type ScoreResponse = {
  transaction_id: string;
  risk_score: number;
  decision: string;
  status: string;
};

export type ConnectionState = "Connecting" | "Live" | "Syncing" | "Disconnected" | "Stream issue" | "Stream error";