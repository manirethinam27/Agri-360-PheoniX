import axios from 'axios';
import type { ComparePayload, SeasonPayload, SeasonRequest } from './types';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000,
});

export async function generateSeason(config: SeasonRequest): Promise<SeasonPayload> {
  const { data } = await api.post('/api/seasons/generate', config);
  return data;
}

export async function compareNoise(config: SeasonRequest): Promise<ComparePayload> {
  const { data } = await api.post('/api/compare', {
    crop: config.crop,
    planting_date: config.planting_date,
    plots_per_crop: config.plots_per_crop,
    low_cloud_percent: Math.max(0, config.cloud_percent / 2),
    high_cloud_percent: Math.min(85, Math.max(config.cloud_percent + 35, 50)),
    low_noise_level: Math.max(0.005, config.noise_level / 2),
    high_noise_level: Math.min(0.18, Math.max(config.noise_level * 3.5, 0.08)),
    revisit_days: config.revisit_days,
    seed: config.seed,
  });
  return data;
}
