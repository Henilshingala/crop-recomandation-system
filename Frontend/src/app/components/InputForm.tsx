import { Label } from "@/app/components/ui/label";
import { Droplet, Thermometer, FlaskConical, CloudRain, Gauge, Loader2 } from "lucide-react";
import { useState, useEffect, useMemo } from "react";
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
    <div className="glass-card overflow-hidden animate-fade-in-up">
      {/* Card header */}
      <div className="px-6 py-5 border-b border-gray-200/60">
        <h2 className="text-xl font-bold text-gray-900">{t("form.title")}</h2>
        <p className="text-sm text-gray-500 mt-1">{t("form.description")}</p>
      </div>

      {/* Card body */}
      <div className="p-6">
        <form onSubmit={handleSubmit} className="space-y-8">

          {/* NPK Section */}
          <div className="space-y-4">
            <div className="flex items-center gap-3 mb-4">
              <div className="h-px flex-1 bg-gradient-to-r from-emerald-500/30 to-transparent" />
              <h3 className="text-xs font-semibold text-emerald-700 uppercase tracking-widest whitespace-nowrap">
                {t("form.soilNutrients")}
              </h3>
              <div className="h-px flex-1 bg-gradient-to-l from-emerald-500/30 to-transparent" />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              <GlassField label={t("form.nitrogen")} name="nitrogen" icon={<FlaskConical className="w-4 h-4 text-blue-400" />} placeholder={`${VALIDATION_RANGES.nitrogen.min}–${VALIDATION_RANGES.nitrogen.max}`} unit="kg/ha" errors={errors} onBlur={handleInputBlur} />
              <GlassField label={t("form.phosphorus")} name="phosphorus" icon={<FlaskConical className="w-4 h-4 text-orange-400" />} placeholder={`${VALIDATION_RANGES.phosphorus.min}–${VALIDATION_RANGES.phosphorus.max}`} unit="kg/ha" errors={errors} onBlur={handleInputBlur} />
              <GlassField label={t("form.potassium")} name="potassium" icon={<FlaskConical className="w-4 h-4 text-purple-400" />} placeholder={`${VALIDATION_RANGES.potassium.min}–${VALIDATION_RANGES.potassium.max}`} unit="kg/ha" errors={errors} onBlur={handleInputBlur} />
            </div>
          </div>

          {/* Environmental Conditions */}
          <div className="space-y-4">
            <div className="flex items-center gap-3 mb-4">
              <div className="h-px flex-1 bg-gradient-to-r from-teal-500/30 to-transparent" />
              <h3 className="text-xs font-semibold text-teal-700 uppercase tracking-widest whitespace-nowrap">
                {t("form.envConditions")}
              </h3>
              <div className="h-px flex-1 bg-gradient-to-l from-teal-500/30 to-transparent" />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <GlassField label={t("form.temperature")} name="temperature" icon={<Thermometer className="w-4 h-4 text-red-400" />} placeholder={`${VALIDATION_RANGES.temperature.min} to ${VALIDATION_RANGES.temperature.max}`} unit="°C" step="0.1" errors={errors} onBlur={handleInputBlur} />
              <GlassField label={t("form.humidity")} name="humidity" icon={<Droplet className="w-4 h-4 text-sky-400" />} placeholder={`${VALIDATION_RANGES.humidity.min}–${VALIDATION_RANGES.humidity.max}`} unit="%" step="0.1" errors={errors} onBlur={handleInputBlur} />
              <GlassField label={t("form.ph")} name="ph" icon={<Gauge className="w-4 h-4 text-emerald-400" />} placeholder={`${VALIDATION_RANGES.ph.min}–${VALIDATION_RANGES.ph.max}`} unit="pH" step="0.1" errors={errors} onBlur={handleInputBlur} />
              <GlassField label={t("form.rainfall")} name="rainfall" icon={<CloudRain className="w-4 h-4 text-cyan-400" />} placeholder={`${VALIDATION_RANGES.rainfall.min}–${VALIDATION_RANGES.rainfall.max}`} unit="mm" step="0.1" errors={errors} onBlur={handleInputBlur} />
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isLoading}
            className="btn-glow w-full py-4 text-lg tracking-wide cursor-pointer"
          >
            {isLoading ? (
              <span className="flex items-center justify-center gap-2">
                <Loader2 className="w-5 h-5 animate-spin" />
                {t("form.analyzing")}
              </span>
            ) : (
              t("form.submit")
            )}
          </button>
        </form>
      </div>
    </div>
  );
}

/* ── Glass field input ────────────────────────────────────────────── */

function GlassField({
  label, name, icon, placeholder, unit, step = "0.01", errors, onBlur,
}: {
  label: string; name: string; icon: React.ReactNode; placeholder: string;
  unit: string; step?: string;
  errors: Record<string, string>; onBlur: (e: React.FocusEvent<HTMLInputElement>) => void;
}) {
  return (
    <div className="space-y-2">
      <Label htmlFor={name} className="flex items-center gap-2 text-gray-700 text-sm font-medium">
        {icon} {label}
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
          className={`glass-input w-full px-4 py-2.5 text-sm ${errors[name] ? '!border-red-500/50' : ''}`}
        />
        <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-500">{unit}</span>
      </div>
      {errors[name] && (
        <p className="text-xs text-red-600 mt-1 animate-fade-in">{errors[name]}</p>
      )}
    </div>
  );
}

