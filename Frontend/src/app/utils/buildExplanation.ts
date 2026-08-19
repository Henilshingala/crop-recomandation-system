/**
 * Client-side translated crop explanation builder.
 *
 * Mirrors the logic of `generate_explanation()` in Aiml/app.py
 * but uses i18n templates so the output respects the active language.
 */

import type { TFunction } from "i18next";
import { CROP_CONSTRAINTS } from "./cropConstraints";

export interface ExplanationInput {
  temperature: number;
  humidity: number;
  ph: number;
  rainfall: number;
}

/**
 * Build a translated explanation string for a crop recommendation.
 *
 * @param crop     - API crop key (e.g. "finger_millet")
 * @param input    - The user's environmental input values
 * @param t        - i18next translate function (from `useTranslation()`)
 * @param tc       - crop-name translator  `(crop) => t(\`crops.\${crop}\`)`
 * @param isFallback - Whether this is a fallback (all-not-recommended) result
 * @param stressPerFeature - Optional per-feature stress values from API
 * @param isOod    - Whether input is out-of-distribution
 */
export function buildExplanation(
  crop: string,
  input: ExplanationInput,
  t: TFunction,
  tc: (crop: string) => string,
  isFallback = false,
  stressPerFeature?: Record<string, number>,
  isOod = false,
): string {
  const cropName = tc(crop);

  // If it's a fallback scenario, return the short fallback sentence
  if (isFallback) {
    return t("explanation.fallback", { crop: cropName });
  }

  const constraints = CROP_CONSTRAINTS[crop];
  if (!constraints) {
    // No constraint data → can't generate a local explanation
    return "";
  }

  const { temperature: temp, humidity: hum, ph, rainfall: rain } = input;
  const parts: string[] = [];

  // ── Temperature ──────────────────────────────────────────────
  const [tMin, tMax] = constraints.temp_range;
  if (temp >= tMin && temp <= tMax) {
    parts.push(t("explanation.tempInRange", { temp: temp.toFixed(1), crop: cropName, min: tMin, max: tMax }));
  } else if (temp < tMin) {
    parts.push(t("explanation.tempBelow", { temp: temp.toFixed(1), crop: cropName, deficit: (tMin - temp).toFixed(1), min: tMin }));
  } else {
    parts.push(t("explanation.tempAbove", { temp: temp.toFixed(1), crop: cropName, excess: (temp - tMax).toFixed(1), max: tMax }));
  }

  // ── Rainfall ─────────────────────────────────────────────────
  const [rMin, rMax] = constraints.rainfall_range;
  if (rain >= rMin && rain <= rMax) {
    parts.push(t("explanation.rainInRange", { rain: Math.round(rain), crop: cropName, min: rMin, max: rMax }));
  } else if (rain < rMin) {
    parts.push(t("explanation.rainBelow", { rain: Math.round(rain), crop: cropName, min: rMin }));
  } else {
    parts.push(t("explanation.rainAbove", { rain: Math.round(rain), crop: cropName, max: rMax }));
  }

  // ── pH ───────────────────────────────────────────────────────
  const [phMin, phMax] = constraints.ph_range;
  if (ph >= phMin && ph <= phMax) {
    parts.push(t("explanation.phInRange", { ph: ph.toFixed(1), min: phMin, max: phMax }));
  } else if (ph < phMin) {
    parts.push(t("explanation.phBelow", { ph: ph.toFixed(1), crop: cropName, min: phMin }));
  } else {
    parts.push(t("explanation.phAbove", { ph: ph.toFixed(1), crop: cropName, max: phMax }));
  }

  // ── Humidity ─────────────────────────────────────────────────
  const [hMin, hMax] = constraints.humidity_range;
  if (hum < hMin) {
    parts.push(t("explanation.humidityLow", { hum: Math.round(hum), crop: cropName, min: hMin }));
  } else if (hum > hMax) {
    parts.push(t("explanation.humidityHigh", { hum: Math.round(hum), crop: cropName }));
  }

  // ── Stress warnings ──────────────────────────────────────────
  if (stressPerFeature) {
    const highStress = Object.entries(stressPerFeature)
      .filter(([, v]) => v > 0.6)
      .map(([f]) => f);
    if (highStress.length) {
      parts.push(t("explanation.highStress", { features: highStress.join(", ") }));
    }

    const boundary = Object.entries(stressPerFeature)
      .filter(([, v]) => v > 0.4 && v <= 0.6)
      .map(([f]) => f);
    if (boundary.length) {
      parts.push(t("explanation.boundary", { features: boundary.join(", ") }));
    }
  }

  // ── Out-of-distribution warning ──────────────────────────────
  if (isOod) {
    parts.push(t("explanation.oodWarning"));
  }

  return parts.join(" ");
}
