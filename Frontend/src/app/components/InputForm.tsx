import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card";
import { Input } from "@/app/components/ui/input";
import { Label } from "@/app/components/ui/label";
import { Button } from "@/app/components/ui/button";
import { Droplet, Thermometer, FlaskConical, CloudRain, Gauge, Loader2 } from "lucide-react";
import { useState, useEffect, useMemo } from "react";
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
    if (isNaN(numValue)) return "Please enter a valid number";
    if (numValue < range.min) return `Min: ${range.min} ${range.unit}`;
    if (numValue > range.max) return `Max: ${range.max} ${range.unit}`;
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
    <Card className="shadow-lg border-green-100/60 backdrop-blur-sm bg-white/80">
      <CardHeader className="bg-gradient-to-r from-green-50/80 to-emerald-50/80">
        <CardTitle className="text-2xl text-green-900">Soil & Environmental Parameters</CardTitle>
        <CardDescription className="text-green-700">
          Enter your field's measurements to get personalized crop recommendations
        </CardDescription>
      </CardHeader>
      <CardContent className="pt-6">
        <form onSubmit={handleSubmit} className="space-y-6">

          {/* NPK Section */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide border-b pb-2">
              Soil Nutrients
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <FieldInput label="Nitrogen (N)" name="nitrogen" icon={<FlaskConical className="w-4 h-4 text-blue-600" />} placeholder={`${VALIDATION_RANGES.nitrogen.min}-${VALIDATION_RANGES.nitrogen.max}`} unit="kg/ha" errors={errors} onBlur={handleInputBlur} />
              <FieldInput label="Phosphorus (P)" name="phosphorus" icon={<FlaskConical className="w-4 h-4 text-orange-600" />} placeholder={`${VALIDATION_RANGES.phosphorus.min}-${VALIDATION_RANGES.phosphorus.max}`} unit="kg/ha" errors={errors} onBlur={handleInputBlur} />
              <FieldInput label="Potassium (K)" name="potassium" icon={<FlaskConical className="w-4 h-4 text-purple-600" />} placeholder={`${VALIDATION_RANGES.potassium.min}-${VALIDATION_RANGES.potassium.max}`} unit="kg/ha" errors={errors} onBlur={handleInputBlur} />
            </div>
          </div>

          {/* Environmental Conditions */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide border-b pb-2">
              Environmental Conditions
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FieldInput label="Temperature" name="temperature" icon={<Thermometer className="w-4 h-4 text-red-600" />} placeholder={`${VALIDATION_RANGES.temperature.min} to ${VALIDATION_RANGES.temperature.max}`} unit="°C" step="0.1" errors={errors} onBlur={handleInputBlur} />
              <FieldInput label="Humidity" name="humidity" icon={<Droplet className="w-4 h-4 text-blue-600" />} placeholder={`${VALIDATION_RANGES.humidity.min}-${VALIDATION_RANGES.humidity.max}`} unit="%" step="0.1" errors={errors} onBlur={handleInputBlur} />
              <FieldInput label="Soil pH" name="ph" icon={<Gauge className="w-4 h-4 text-green-600" />} placeholder={`${VALIDATION_RANGES.ph.min}-${VALIDATION_RANGES.ph.max}`} unit="pH" step="0.1" errors={errors} onBlur={handleInputBlur} />
              <FieldInput label="Rainfall" name="rainfall" icon={<CloudRain className="w-4 h-4 text-sky-600" />} placeholder={`${VALIDATION_RANGES.rainfall.min}-${VALIDATION_RANGES.rainfall.max}`} unit="mm" step="0.1" errors={errors} onBlur={handleInputBlur} />
            </div>
          </div>

          {/* Submit Button */}
          <Button
            type="submit"
            disabled={isLoading}
            className="w-full bg-green-600 hover:bg-green-700 text-white py-6 rounded-lg text-lg font-semibold shadow-lg transition-all hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                Analyzing...
              </>
            ) : (
              'Get Crop Recommendation'
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

/* ── Reusable field input ─────────────────────────────────────────── */

function FieldInput({
  label, name, icon, placeholder, unit, step = "0.01", defaultValue, required = true, errors, onBlur,
}: {
  label: string; name: string; icon: React.ReactNode; placeholder: string;
  unit: string; step?: string; defaultValue?: string; required?: boolean;
  errors: Record<string, string>; onBlur: (e: React.FocusEvent<HTMLInputElement>) => void;
}) {
  return (
    <div className="space-y-2">
      <Label htmlFor={name} className="flex items-center gap-2 text-gray-700 text-sm">
        {icon} {label}
      </Label>
      <div className="relative">
        <Input
          id={name}
          name={name}
          type="number"
          step={step}
          placeholder={placeholder}
          required={required}
          defaultValue={defaultValue}
          onBlur={onBlur}
          className={`rounded-lg border-gray-300 focus:border-green-500 focus:ring-green-500 ${errors[name] ? 'border-red-500' : ''}`}
        />
        <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-400">{unit}</span>
      </div>
      {errors[name] && <p className="text-xs text-red-600 mt-1">{errors[name]}</p>}
    </div>
  );
}

