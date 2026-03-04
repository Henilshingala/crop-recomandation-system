/**
 * Agronomic constraint ranges per crop — mirrors CROP_AGRO_CONSTRAINTS
 * from the backend (Aiml/app.py).  Used solely for generating
 * client-side translated explanations.
 */

export interface CropConstraint {
  ph_range: [number, number];
  temp_range: [number, number];
  rainfall_range: [number, number];
  humidity_range: [number, number];
}

export const CROP_CONSTRAINTS: Record<string, CropConstraint> = {
  apple:         { ph_range: [5.5, 7.0], temp_range: [10, 28], rainfall_range: [500, 1500],  humidity_range: [40, 80] },
  bajra:         { ph_range: [6.0, 8.0], temp_range: [25, 42], rainfall_range: [200, 700],   humidity_range: [20, 65] },
  banana:        { ph_range: [5.5, 7.5], temp_range: [20, 40], rainfall_range: [1000, 3000], humidity_range: [60, 95] },
  barley:        { ph_range: [6.0, 8.5], temp_range: [5, 25],  rainfall_range: [300, 1000],  humidity_range: [30, 70] },
  ber:           { ph_range: [6.5, 9.0], temp_range: [30, 48], rainfall_range: [100, 600],   humidity_range: [10, 50] },
  blackgram:     { ph_range: [5.5, 7.5], temp_range: [25, 38], rainfall_range: [400, 900],   humidity_range: [50, 85] },
  brinjal:       { ph_range: [5.5, 7.0], temp_range: [20, 35], rainfall_range: [300, 1000],  humidity_range: [50, 80] },
  carrot:        { ph_range: [6.0, 7.0], temp_range: [10, 25], rainfall_range: [300, 800],   humidity_range: [50, 80] },
  castor:        { ph_range: [5.0, 8.0], temp_range: [20, 38], rainfall_range: [300, 800],   humidity_range: [30, 70] },
  chickpea:      { ph_range: [6.0, 8.0], temp_range: [15, 30], rainfall_range: [300, 700],   humidity_range: [30, 60] },
  citrus:        { ph_range: [5.5, 7.5], temp_range: [15, 35], rainfall_range: [500, 1500],  humidity_range: [40, 80] },
  coconut:       { ph_range: [5.0, 8.0], temp_range: [22, 38], rainfall_range: [1000, 3200], humidity_range: [60, 95] },
  coffee:        { ph_range: [5.0, 6.5], temp_range: [15, 28], rainfall_range: [1000, 2500], humidity_range: [60, 90] },
  cole_crop:     { ph_range: [6.0, 7.5], temp_range: [5, 22],  rainfall_range: [400, 1500],  humidity_range: [50, 85] },
  cotton:        { ph_range: [5.5, 8.5], temp_range: [25, 40], rainfall_range: [500, 1200],  humidity_range: [40, 75] },
  cucumber:      { ph_range: [5.5, 7.5], temp_range: [18, 35], rainfall_range: [300, 1000],  humidity_range: [50, 85] },
  custard_apple: { ph_range: [5.5, 8.0], temp_range: [25, 42], rainfall_range: [200, 800],   humidity_range: [30, 70] },
  date_palm:     { ph_range: [7.0, 9.0], temp_range: [30, 48], rainfall_range: [50, 400],    humidity_range: [10, 50] },
  finger_millet: { ph_range: [5.0, 7.5], temp_range: [20, 35], rainfall_range: [500, 1200],  humidity_range: [50, 80] },
  gourd:         { ph_range: [5.5, 7.5], temp_range: [20, 38], rainfall_range: [300, 1000],  humidity_range: [50, 85] },
  grapes:        { ph_range: [5.5, 7.5], temp_range: [15, 35], rainfall_range: [400, 1000],  humidity_range: [30, 70] },
  green_chilli:  { ph_range: [5.5, 7.5], temp_range: [20, 35], rainfall_range: [400, 1000],  humidity_range: [50, 80] },
  groundnut:     { ph_range: [5.5, 7.5], temp_range: [22, 38], rainfall_range: [400, 1000],  humidity_range: [40, 75] },
  guava:         { ph_range: [5.0, 7.5], temp_range: [18, 38], rainfall_range: [400, 1500],  humidity_range: [40, 80] },
  jowar:         { ph_range: [5.5, 8.5], temp_range: [25, 42], rainfall_range: [300, 800],   humidity_range: [30, 70] },
  jute:          { ph_range: [5.0, 7.5], temp_range: [25, 38], rainfall_range: [1000, 2500], humidity_range: [60, 95] },
  kidneybeans:   { ph_range: [5.5, 7.0], temp_range: [15, 28], rainfall_range: [300, 800],   humidity_range: [40, 70] },
  lentil:        { ph_range: [6.0, 8.0], temp_range: [10, 28], rainfall_range: [200, 600],   humidity_range: [30, 65] },
  linseed:       { ph_range: [5.5, 7.5], temp_range: [10, 30], rainfall_range: [300, 750],   humidity_range: [30, 65] },
  maize:         { ph_range: [5.5, 7.5], temp_range: [18, 35], rainfall_range: [400, 1200],  humidity_range: [40, 80] },
  mango:         { ph_range: [5.5, 7.5], temp_range: [24, 42], rainfall_range: [500, 2500],  humidity_range: [40, 80] },
  mothbeans:     { ph_range: [6.5, 8.5], temp_range: [25, 42], rainfall_range: [200, 600],   humidity_range: [20, 60] },
  mungbean:      { ph_range: [5.5, 7.5], temp_range: [25, 38], rainfall_range: [400, 800],   humidity_range: [50, 80] },
  muskmelon:     { ph_range: [6.0, 7.5], temp_range: [22, 38], rainfall_range: [200, 600],   humidity_range: [40, 70] },
  mustard:       { ph_range: [5.5, 8.0], temp_range: [10, 28], rainfall_range: [200, 600],   humidity_range: [30, 65] },
  okra:          { ph_range: [6.0, 7.5], temp_range: [22, 38], rainfall_range: [400, 1000],  humidity_range: [50, 80] },
  onion:         { ph_range: [6.0, 7.5], temp_range: [10, 30], rainfall_range: [300, 800],   humidity_range: [40, 75] },
  papaya:        { ph_range: [5.5, 7.5], temp_range: [22, 38], rainfall_range: [600, 2000],  humidity_range: [50, 85] },
  pearl_millet:  { ph_range: [6.0, 8.0], temp_range: [25, 42], rainfall_range: [200, 700],   humidity_range: [20, 65] },
  pigeonpea:     { ph_range: [5.0, 8.0], temp_range: [20, 38], rainfall_range: [600, 1500],  humidity_range: [40, 80] },
  pigeonpeas:    { ph_range: [5.0, 8.0], temp_range: [20, 38], rainfall_range: [600, 1500],  humidity_range: [40, 80] },
  pomegranate:   { ph_range: [5.5, 8.0], temp_range: [22, 40], rainfall_range: [200, 800],   humidity_range: [30, 65] },
  potato:        { ph_range: [5.0, 7.0], temp_range: [10, 25], rainfall_range: [400, 1000],  humidity_range: [50, 85] },
  radish:        { ph_range: [5.5, 7.0], temp_range: [8, 22],  rainfall_range: [200, 800],   humidity_range: [50, 80] },
  ragi:          { ph_range: [5.0, 7.5], temp_range: [20, 35], rainfall_range: [500, 1200],  humidity_range: [50, 80] },
  rice:          { ph_range: [5.0, 7.5], temp_range: [20, 38], rainfall_range: [800, 3000],  humidity_range: [60, 95] },
  safflower:     { ph_range: [6.0, 8.0], temp_range: [15, 35], rainfall_range: [300, 700],   humidity_range: [30, 60] },
  sapota:        { ph_range: [6.0, 8.0], temp_range: [20, 38], rainfall_range: [600, 2000],  humidity_range: [50, 85] },
  sesamum:       { ph_range: [5.5, 8.0], temp_range: [25, 40], rainfall_range: [200, 700],   humidity_range: [30, 65] },
  sesame:        { ph_range: [5.5, 8.0], temp_range: [25, 40], rainfall_range: [200, 700],   humidity_range: [30, 65] },
  sorghum:       { ph_range: [5.5, 8.5], temp_range: [25, 42], rainfall_range: [300, 800],   humidity_range: [30, 70] },
  soybean:       { ph_range: [5.5, 7.5], temp_range: [20, 35], rainfall_range: [500, 1200],  humidity_range: [50, 80] },
  spinach:       { ph_range: [6.0, 7.5], temp_range: [8, 25],  rainfall_range: [300, 800],   humidity_range: [50, 80] },
  sugarcane:     { ph_range: [5.0, 8.5], temp_range: [22, 40], rainfall_range: [800, 2500],  humidity_range: [55, 90] },
  sunflower:     { ph_range: [6.0, 7.5], temp_range: [18, 35], rainfall_range: [400, 1000],  humidity_range: [40, 70] },
  tobacco:       { ph_range: [5.0, 7.5], temp_range: [18, 35], rainfall_range: [400, 1200],  humidity_range: [50, 80] },
  tomato:        { ph_range: [5.5, 7.5], temp_range: [18, 35], rainfall_range: [300, 1000],  humidity_range: [50, 80] },
  watermelon:    { ph_range: [5.5, 7.5], temp_range: [22, 38], rainfall_range: [300, 800],   humidity_range: [40, 75] },
  wheat:         { ph_range: [5.5, 8.0], temp_range: [8, 25],  rainfall_range: [250, 1000],  humidity_range: [30, 70] },
};
