/**
 * API Service for Crop Recommendation System
 * Handles all backend communication
 */

const API_BASE_URL = 'http://127.0.0.1:8000/api';

export interface PredictionInput {
  N: number;
  P: number;
  K: number;
  temperature: number;
  humidity: number;
  ph: number;
  rainfall: number;
}

export interface CropRecommendation {
  crop: string;
  confidence: number;
  image_url: string;
  image_urls?: string[];  // Array of 3 images for carousel
  expected_yield: string | null;
  season: string | null;
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

export interface PredictionResponse {
  recommendations: CropRecommendation[];
}

export interface HealthResponse {
  status: string;
  database: string;
  ml_model: string;
  crop_count?: number;
  available_crops?: string[];
}

/**
 * Get crop recommendations from the ML model
 */
export async function getPrediction(input: PredictionInput): Promise<PredictionResponse> {
  const response = await fetch(`${API_BASE_URL}/predict/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(input),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.error || `Request failed with status ${response.status}`);
  }

  return response.json();
}

/**
 * Check backend health status
 */
export async function checkHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health/`);
  
  if (!response.ok) {
    throw new Error('Backend is not available');
  }

  return response.json();
}

/**
 * Get list of available crops from ML model
 */
export async function getAvailableCrops(): Promise<string[]> {
  const response = await fetch(`${API_BASE_URL}/crops/available/`);
  
  if (!response.ok) {
    throw new Error('Failed to fetch available crops');
  }

  const data = await response.json();
  return data.crops;
}
