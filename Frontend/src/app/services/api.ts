/**
 * API Service for Crop Recommendation System
 * Handles all backend communication
 */

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'https://crop-recomandation-system.onrender.com/api').replace(/\/$/, '');

/* ── Request types ────────────────────────────────────────────────── */

export interface PredictionInput {
  N: number;
  P: number;
  K: number;
  temperature: number;
  humidity: number;
  ph: number;
  rainfall: number;
  mode?: 'honest' | 'hybrid';
  soil_type?: number;
  irrigation?: number;
  moisture?: number;
}

/* ── Response types ───────────────────────────────────────────────── */

export interface CropRecommendation {
  crop: string;
  confidence: number;
  image_url?: string;
  image_urls?: string[];
  expected_yield?: string | null;
  season?: string | null;
  nutrition?: {
    protein_g: number;
    fat_g: number;
    carbs_g: number;
    fiber_g: number;
    iron_mg: number;
    calcium_mg: number;
    vitamin_a_mcg: number;
    vitamin_c_mg: number;
    energy_kcal: number;
    water_g: number;
  } | null;
}

export interface ModelInfo {
  coverage: number;
  type: string;
}

export interface HybridDetail {
  source_dominance: string;
  rule_triggered: string;
  real_top1: string;
  real_confidence: number;
  synth_top1: string;
  synth_confidence: number;
}

export interface PredictionResponse {
  mode: 'honest' | 'hybrid';
  top_1: CropRecommendation;
  top_3: CropRecommendation[];
  model_info: ModelInfo;
  hybrid_detail?: HybridDetail | null;
}

export interface HealthResponse {
  status: string;
  database: string;
  ml_model: string;
  crop_count?: number;
  honest_crops?: number;
  hybrid_crops?: number;
  modes?: string[];
}

/* ── API calls ────────────────────────────────────────────────────── */

/**
 * Get crop recommendations from the ML model
 */
export async function getPrediction(input: PredictionInput): Promise<PredictionResponse> {
  const url = `${API_BASE_URL}/predict/`;

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input),
    });

    if (!response.ok) {
      let errorDetails;
      try {
        errorDetails = await response.json();
      } catch {
        errorDetails = { error: response.statusText };
      }
      throw new Error(errorDetails.error || `Request failed with status ${response.status}`);
    }

    return await response.json();
  } catch (err) {
    if (err instanceof Error) {
      if (err.message.includes('Failed to fetch') || err.message.includes('NetworkError')) {
        throw new Error('Unable to connect to the server. Please check your internet connection and try again.');
      }
    }
    throw err;
  }
}

/**
 * Check backend health status
 */
export async function checkHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health/`);
  if (!response.ok) throw new Error('Backend is not available');
  return response.json();
}

/**
 * Get list of available crops from ML model
 */
export async function getAvailableCrops(mode: string = 'honest'): Promise<string[]> {
  const response = await fetch(`${API_BASE_URL}/crops/available/?mode=${mode}`);
  if (!response.ok) throw new Error('Failed to fetch available crops');
  const data = await response.json();
  return data.crops;
}
