import { Label } from "@/app/components/ui/label";
import { Droplet, Thermometer, FlaskConical, CloudRain, Gauge, Loader2, MapPin } from "lucide-react";
import { useState, useEffect, useMemo, useRef } from "react";
import { useTranslation } from "react-i18next";
import { getModelLimits, type FeatureRange } from "@/app/services/api";

interface InputFormProps {
  onSubmit: (e: React.FormEvent) => void;
  isLoading?: boolean;
}

// Fallback ranges (matches feature_ranges.json acceptance as of V6 2026-03-03)
const FALLBACK_RANGES: Record<string, FeatureRange> = {
  N:           { min: 0,   max: 210,  unit: "kg/ha" },
  P:           { min: 0,   max: 115,  unit: "kg/ha" },
  K:           { min: 0,   max: 315,  unit: "kg/ha" },
  temperature: { min: 5,   max: 50,   unit: "°C" },
  humidity:    { min: 0,   max: 100,  unit: "%" },
  ph:          { min: 3.0, max: 10.0, unit: "pH" },
  rainfall:    { min: 0,   max: 3200, unit: "mm" },
};

// Map field names used in the form to the keys in feature_ranges.json
const FIELD_TO_RANGE_KEY: Record<string, string> = {
  nitrogen: "N",
  phosphorus: "P",
  potassium: "K",
  temperature: "temperature",
  humidity: "humidity",
  ph: "ph",
  rainfall: "rainfall",
};

export function InputForm({ onSubmit, isLoading = false }: InputFormProps) {
  const { t } = useTranslation();
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [acceptanceRanges, setAcceptanceRanges] = useState<Record<string, FeatureRange>>(FALLBACK_RANGES);
  const [isDetecting, setIsDetecting] = useState(false);
  const formRef = useRef<HTMLFormElement>(null);

  const handleAutoDetect = () => {
    setIsDetecting(true);
    if (!navigator.geolocation) {
      alert("Geolocation is not supported by your browser");
      setIsDetecting(false);
      return;
    }
    
    // 1. Get GPS, 2. Call Open-Meteo for real weather, 3. Fill Form
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = position.coords.latitude;
        const lon = position.coords.longitude;

        fetch(`https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,relative_humidity_2m,precipitation`)
          .then(res => res.json())
          .then(data => {
            if (formRef.current && data.current) {
              // Simulated soil based on state/district (mocked for now)
              (formRef.current.elements.namedItem('nitrogen') as HTMLInputElement).value = "90";
              (formRef.current.elements.namedItem('phosphorus') as HTMLInputElement).value = "42";
              (formRef.current.elements.namedItem('potassium') as HTMLInputElement).value = "43";
              (formRef.current.elements.namedItem('ph') as HTMLInputElement).value = "6.5";
              
              // 100% REAL Live Weather from Open-Meteo API
              (formRef.current.elements.namedItem('temperature') as HTMLInputElement).value = data.current.temperature_2m.toString();
              (formRef.current.elements.namedItem('humidity') as HTMLInputElement).value = data.current.relative_humidity_2m.toString();
              (formRef.current.elements.namedItem('rainfall') as HTMLInputElement).value = "110"; // Keep rainfall simulated as crops expect yearly avg, not hourly
            }
          })
          .catch((error) => {
             console.error("Weather API failed", error);
             alert("Could not fetch live weather. Filling with simulated data.");
             if (formRef.current) {
                // Fallback simulation
                (formRef.current.elements.namedItem('nitrogen') as HTMLInputElement).value = "90";
                (formRef.current.elements.namedItem('phosphorus') as HTMLInputElement).value = "42";
                (formRef.current.elements.namedItem('potassium') as HTMLInputElement).value = "43";
                (formRef.current.elements.namedItem('ph') as HTMLInputElement).value = "6.5";
                (formRef.current.elements.namedItem('temperature') as HTMLInputElement).value = "26.5";
                (formRef.current.elements.namedItem('humidity') as HTMLInputElement).value = "71";
                (formRef.current.elements.namedItem('rainfall') as HTMLInputElement).value = "110";
             }
          })
          .finally(() => {
            setIsDetecting(false);
          });
      },
      (error) => {
        console.error(error);
        alert("Unable to retrieve your location. Please check browser permissions.");
        setIsDetecting(false);
      }
    );
  };

  // Fetch real acceptance ranges from /api/model/limits/ on mount
  useEffect(() => {
    let cancelled = false;
    getModelLimits()
      .then((data) => {
        if (!cancelled && data.acceptance) {
          // Build ranges from API response, keeping unit from fallback where needed
          const merged: Record<string, FeatureRange> = {};
          for (const [key, fallback] of Object.entries(FALLBACK_RANGES)) {
            const remote = data.acceptance[key];
            merged[key] = remote
              ? { min: remote.min, max: remote.max, unit: remote.unit ?? fallback.unit }
              : fallback;
          }
          setAcceptanceRanges(merged);
        }
      })
      .catch(() => {
        // Silently keep fallback ranges
      });
    return () => { cancelled = true; };
  }, []);

  // Derive VALIDATION_RANGES mapping (form field name → range) dynamically
  const VALIDATION_RANGES = useMemo(() => {
    const out: Record<string, FeatureRange> = {};
    for (const [field, rangeKey] of Object.entries(FIELD_TO_RANGE_KEY)) {
      out[field] = acceptanceRanges[rangeKey] ?? FALLBACK_RANGES[rangeKey];
    }
    return out;
  }, [acceptanceRanges]);

  const validateField = (name: string, value: string) => {
    const numValue = parseFloat(value);
    const range = VALIDATION_RANGES[name as keyof typeof VALIDATION_RANGES];

    if (!range) return "";
    if (value === "" || value === undefined) return "";
    if (isNaN(numValue)) return t("form.validNumber");
    if (numValue < range.min) return `${t("form.min")}: ${range.min} ${range.unit}`;
    if (numValue > range.max) return `${t("form.max")}: ${range.max} ${range.unit}`;
    return "";
  };

  const handleInputBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    const error = validateField(name, value);
    setErrors(prev => ({ ...prev, [name]: error }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const form = e.target as HTMLFormElement;
    const formData = new FormData(form);
    const newErrors: Record<string, string> = {};
    let hasError = false;

    // Validate required fields
    for (const fieldName of ['nitrogen', 'phosphorus', 'potassium', 'temperature', 'humidity', 'ph', 'rainfall']) {
      const value = formData.get(fieldName) as string;
      const error = validateField(fieldName, value);
      if (error) { newErrors[fieldName] = error; hasError = true; }
    }

    setErrors(newErrors);
    if (!hasError) onSubmit(e);
  };

  return (
    <div className="agri-card animate-fade-in-up">
      {isLoading && <div className="scan-line" />}

      {/* Card header */}
      <div className="flex justify-between items-start border-b border-[var(--color-border-line)] pb-4 mb-6 border-dashed">
        <div>
          <span className="eyebrow">{t("form.officialForm")}</span>
          <h2 className="text-2xl font-bold text-[var(--color-ink)] mt-1" style={{fontFamily: 'var(--font-display)'}}>{t("form.soilHealthCard")}</h2>
        </div>
        <div className="verified-stamp">{t("form.verified")}</div>
      </div>

      {/* Card body */}
      <div>
        <button
            type="button"
            onClick={handleAutoDetect}
            disabled={isDetecting || isLoading}
            className="mb-8 w-full py-3 bg-[var(--color-paper-deep)] hover:bg-[var(--color-border-line)] border border-[var(--color-border-line)] text-[var(--color-ink)] rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
        >
            {isDetecting ? (
                <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    {t("form.fetchingLocation")}
                </>
            ) : (
                <>
                    <MapPin className="w-5 h-5 text-[var(--color-mustard)]" />
                    {t("form.autoDetect")}
                </>
            )}
        </button>

        <form ref={formRef} onSubmit={handleSubmit} className="space-y-6">

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <AgriField label={t("form.nitrogen")} name="nitrogen" placeholder={`${VALIDATION_RANGES.nitrogen.min}–${VALIDATION_RANGES.nitrogen.max}`} unit="N" errors={errors} onBlur={handleInputBlur} />
            <AgriField label={t("form.phosphorus")} name="phosphorus" placeholder={`${VALIDATION_RANGES.phosphorus.min}–${VALIDATION_RANGES.phosphorus.max}`} unit="P" errors={errors} onBlur={handleInputBlur} />
            <AgriField label={t("form.potassium")} name="potassium" placeholder={`${VALIDATION_RANGES.potassium.min}–${VALIDATION_RANGES.potassium.max}`} unit="K" errors={errors} onBlur={handleInputBlur} />
            <AgriField label={t("form.ph")} name="ph" placeholder={`${VALIDATION_RANGES.ph.min}–${VALIDATION_RANGES.ph.max}`} unit="pH" step="0.1" errors={errors} onBlur={handleInputBlur} />
            <AgriField label={t("form.temperature")} name="temperature" placeholder={`${VALIDATION_RANGES.temperature.min} - ${VALIDATION_RANGES.temperature.max}`} unit="°C" step="0.1" errors={errors} onBlur={handleInputBlur} />
            <AgriField label={t("form.humidity")} name="humidity" placeholder={`${VALIDATION_RANGES.humidity.min}–${VALIDATION_RANGES.humidity.max}`} unit="%" step="0.1" errors={errors} onBlur={handleInputBlur} />
            <AgriField label={t("form.rainfall")} name="rainfall" placeholder={`${VALIDATION_RANGES.rainfall.min}–${VALIDATION_RANGES.rainfall.max}`} unit="mm" step="0.1" errors={errors} onBlur={handleInputBlur} />
          </div>

          <div className="pt-4 border-t border-[var(--color-border-line)] border-dashed">
            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary w-full py-4 text-lg font-bold"
            >
              {isLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <Loader2 className="w-5 h-5 animate-spin" />
                  {t("form.analyzingReport")}
                </span>
              ) : (
                t("form.analyzeReport")
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

/* ── Agri field input ────────────────────────────────────────────── */

function AgriField({
  label, name, placeholder, unit, step = "0.01", errors, onBlur,
}: {
  label: string; name: string; placeholder: string;
  unit: string; step?: string;
  errors: Record<string, string>; onBlur: (e: React.FocusEvent<HTMLInputElement>) => void;
}) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={name} className="block text-[var(--color-ink-soft)] text-xs font-semibold uppercase tracking-wider">
        {label}
      </Label>
      <div className="relative">
        <input
          id={name}
          name={name}
          type="number"
          step={step}
          placeholder={placeholder}
          required
          onBlur={onBlur}
          className={`agri-input w-full px-4 py-3 text-sm font-medium ${errors[name] ? '!border-red-500/50' : ''}`}
        />
        <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-bold text-[var(--color-mustard)] mono-data">{unit}</span>
      </div>
      {errors[name] && (
        <p className="text-xs text-red-600 mt-1 animate-fade-in">{errors[name]}</p>
      )}
    </div>
  );
}

