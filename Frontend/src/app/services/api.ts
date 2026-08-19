/**
 * API Service for Crop Recommendation System
 * All requests route through the Render backend (Django gateway).
 * No direct HuggingFace calls from the frontend.
 */

export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ||
  'https://crop-recomandation-system-kcoh.onrender.com/api'
).replace(/\/$/, '');

/* ── Request types ────────────────────────────────────────────────── */

export interface PredictionInput {
  N: number;
  P: number;
  K: number;
  temperature: number;
  humidity: number;
  ph: number;
  rainfall: number;
}

/* ── Response types ───────────────────────────────────────────────── */

export interface CropRecommendation {
  crop: string;
  confidence: number;
  risk_level?: 'low' | 'medium' | 'high';
  advisory_tier?: string;
  explanation?: string;
  ncs?: number;
  ncs_level?: 'strong' | 'moderate' | 'weak';
  environmental_match?: 'strong' | 'acceptable' | 'weak' | 'unknown';
  ems?: number;
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
  version?: string;
}

export interface LimitingFactor {
  feature: string;
  deviation: number;
  all_deviations: Record<string, number>;
}

export interface ExcludedCrop {
  crop: string;
  reasons: string[];
}

export interface PredictionResponse {
  top_1: CropRecommendation;
  top_3: CropRecommendation[];
  model_info: ModelInfo;
  environment_info?: Record<string, unknown>;
  warning?: string;
  disclaimer?: string;
  version?: string;
  fallback_mode?: boolean;
  all_not_recommended?: boolean;
  global_unsuitable?: boolean;
  limiting_factor?: LimitingFactor;
  viable_count?: number;
  excluded_crops?: ExcludedCrop[];
}

export interface HealthResponse {
  status: string;
  database: string;
  ml_model: string;
  crop_count?: number;
  soil_crops?: number;
  extended_crops?: number;
}

/* ── API calls ────────────────────────────────────────────────────── */

/**
 * Get crop recommendations from the Render backend
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
export async function getAvailableCrops(): Promise<string[]> {
  const response = await fetch(`${API_BASE_URL}/crops/available/`);
  if (!response.ok) throw new Error('Failed to fetch available crops');
  const data = await response.json();
  return data.crops;
}

/* ── Feature-range types ──────────────────────────────────────────── */

export interface FeatureRange {
  min: number;
  max: number;
  unit?: string;
}

export interface ModelLimitsResponse {
  acceptance: Record<string, FeatureRange>;
  original?: {
    dataset: string;
    rows: number;
    crops: number;
    features: Record<string, FeatureRange & { p1: number; p99: number; mean: number; std: number }>;
  };
  synthetic?: {
    dataset: string;
    rows: number;
    crops: number;
    features: Record<string, FeatureRange & { p1: number; p99: number; mean: number; std: number }>;
  };
}

/**
 * Fetch feature validation ranges from the backend (single source of truth).
 * Used by InputForm to set dynamic min/max on number fields.
 */
export async function getModelLimits(): Promise<ModelLimitsResponse> {
  const response = await fetch(`${API_BASE_URL}/model/limits/`);
  if (!response.ok) throw new Error('Failed to fetch model limits');
  return response.json();
}

/* ── Location API (cascading dropdowns) ──────────────────────── */

export interface StateItem {
  state: string;
  stateCode: string;
}

export async function getLocationStates(): Promise<StateItem[]> {
  const response = await fetch(`${API_BASE_URL}/locations/states/`);
  if (!response.ok) throw new Error('Failed to fetch states');
  const data = await response.json();
  return data.states;
}

export async function getLocationDistricts(state: string): Promise<{ districts: string[]; cities: string[] }> {
  const response = await fetch(`${API_BASE_URL}/locations/districts/?state=${encodeURIComponent(state)}`);
  if (!response.ok) throw new Error('Failed to fetch districts');
  return response.json();
}

export async function getLocationSubDistricts(state: string, district: string): Promise<string[]> {
  const response = await fetch(`${API_BASE_URL}/locations/subdistricts/?state=${encodeURIComponent(state)}&district=${encodeURIComponent(district)}`);
  if (!response.ok) throw new Error('Failed to fetch sub-districts');
  const data = await response.json();
  return data.subDistricts;
}

export async function getLocationVillages(state: string, district: string, subDistrict: string): Promise<string[]> {
  const response = await fetch(`${API_BASE_URL}/locations/villages/?state=${encodeURIComponent(state)}&district=${encodeURIComponent(district)}&subdistrict=${encodeURIComponent(subDistrict)}`);
  if (!response.ok) throw new Error('Failed to fetch villages');
  const data = await response.json();
  return data.villages;
}
