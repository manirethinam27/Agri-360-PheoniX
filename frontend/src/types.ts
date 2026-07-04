export type CropName = 'Rice' | 'Wheat' | 'Cotton' | 'Sugarcane' | 'All';

export interface SeasonRequest {
  crop: CropName;
  planting_date: string;
  plots_per_crop: number;
  cloud_percent: number;
  noise_level: number;
  revisit_days: number;
  seed?: number | null;
}

export interface Advisory {
  level: string;
  reason: string;
  current_ndmi?: number;
  stress_score: number;
  recommendation: string;
}

export interface Observation {
  plot_id: string;
  crop: string;
  date: string;
  day: number;
  day_norm: number;
  duration: number;
  growth_stage: string;
  stage_name: string;
  true_ndvi: number;
  true_ndmi: number;
  observed_ndvi: number | null;
  observed_ndmi: number | null;
  water_stress_label: string;
  stress_score: number;
  weather_factor: number;
  missing_reason: string;
  cloud_contaminated: boolean;
  synthetic: boolean;
  advisory?: Advisory;
}

export interface MatrixPayload {
  labels: string[];
  matrix: number[][];
  total: number;
}

export interface ModelMetrics {
  target: string;
  accuracy: number;
  labels: string[];
  confusion_matrix: MatrixPayload;
  classification_report: Record<string, any>;
  feature_count: number;
  model: string;
  features_used?: string[];
  warning?: string;
}

export interface SeasonPayload {
  season_id: string;
  seed: number;
  config: SeasonRequest;
  summary: {
    synthetic_disclosure: string;
    rows: number;
    clear_observations: number;
    missing_observations: number;
    cloud_percent_realized: number;
    crop_counts: Record<string, number>;
    stress_counts: Record<string, number>;
    mean_observed_ndvi: number | null;
    mean_observed_ndmi: number | null;
    latest_plot_status: Observation[];
  };
  metrics: {
    crop_classifier: ModelMetrics;
    growth_stage_predictor: ModelMetrics;
  };
  observations: Observation[];
}

export interface ComparePayload {
  seed: number;
  low_noise: { metrics: SeasonPayload['metrics']; summary: SeasonPayload['summary']; config: SeasonRequest };
  high_noise: { metrics: SeasonPayload['metrics']; summary: SeasonPayload['summary']; config: SeasonRequest };
  accuracy_delta: { crop_classifier: number; growth_stage_predictor: number };
  interpretation: string;
}
