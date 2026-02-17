/**
 * API Service for Crop Recommendation System
 * Handles all backend communication
 */

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'https://crop-recomandation-system.onrender.com/api').replace(/\/$/, '');

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
  const url = `${API_BASE_URL}/predict/`;
  console.log('🌐 API Request URL:', url);
  console.log('📝 API Base URL env:', import.meta.env.VITE_API_BASE_URL);
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(input),
    });

    console.log('📡 Response status:', response.status, response.statusText);

    if (!response.ok) {
      let errorDetails;
      try {
        errorDetails = await response.json();
      } catch {
        errorDetails = { error: response.statusText };
      }
      console.error('❌ API Error Response:', errorDetails);
      throw new Error(errorDetails.error || `Request failed with status ${response.status}`);
    }

    const data = await response.json();
    console.log('✅ API Response data:', data);
    return data;
  } catch (err) {
    console.error('💥 Fetch error:', err);
    if (err instanceof Error) {
      // Network error or timeout
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
