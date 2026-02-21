import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card";
import { Input } from "@/app/components/ui/input";
import { Label } from "@/app/components/ui/label";
import { Button } from "@/app/components/ui/button";
import { Badge } from "@/app/components/ui/badge";
import { Droplet, Thermometer, FlaskConical, CloudRain, Gauge, Loader2, ChevronDown, Shield, Layers, Combine } from "lucide-react";
import { useState } from "react";

interface InputFormProps {
  onSubmit: (e: React.FormEvent) => void;
  isLoading?: boolean;
}

// Validation ranges
const VALIDATION_RANGES = {
  nitrogen: { min: 0, max: 150, unit: "kg/ha" },
  phosphorus: { min: 0, max: 150, unit: "kg/ha" },
  potassium: { min: 0, max: 300, unit: "kg/ha" },
  temperature: { min: 0, max: 50, unit: "°C" },
  humidity: { min: 0, max: 100, unit: "%" },
  ph: { min: 3.5, max: 9.5, unit: "pH" },
  rainfall: { min: 0, max: 3000, unit: "mm" },
  moisture: { min: 0, max: 100, unit: "%" },
};

export function InputForm({ onSubmit, isLoading = false }: InputFormProps) {
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [mode, setMode] = useState<'original' | 'synthetic' | 'both'>('original');
  const [showAdvanced, setShowAdvanced] = useState(false);

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
              <FieldInput label="Nitrogen (N)" name="nitrogen" icon={<FlaskConical className="w-4 h-4 text-blue-600" />} placeholder="0-150" unit="kg/ha" errors={errors} onBlur={handleInputBlur} />
              <FieldInput label="Phosphorus (P)" name="phosphorus" icon={<FlaskConical className="w-4 h-4 text-orange-600" />} placeholder="0-150" unit="kg/ha" errors={errors} onBlur={handleInputBlur} />
              <FieldInput label="Potassium (K)" name="potassium" icon={<FlaskConical className="w-4 h-4 text-purple-600" />} placeholder="0-300" unit="kg/ha" errors={errors} onBlur={handleInputBlur} />
            </div>
          </div>

          {/* Environmental Conditions */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide border-b pb-2">
              Environmental Conditions
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FieldInput label="Temperature" name="temperature" icon={<Thermometer className="w-4 h-4 text-red-600" />} placeholder="0-50" unit="°C" step="0.1" errors={errors} onBlur={handleInputBlur} />
              <FieldInput label="Humidity" name="humidity" icon={<Droplet className="w-4 h-4 text-blue-600" />} placeholder="0-100" unit="%" step="0.1" errors={errors} onBlur={handleInputBlur} />
              <FieldInput label="Soil pH" name="ph" icon={<Gauge className="w-4 h-4 text-green-600" />} placeholder="3.5-9.5" unit="pH" step="0.1" errors={errors} onBlur={handleInputBlur} />
              <FieldInput label="Rainfall" name="rainfall" icon={<CloudRain className="w-4 h-4 text-sky-600" />} placeholder="0-3000" unit="mm" step="0.1" errors={errors} onBlur={handleInputBlur} />
            </div>
          </div>

          {/* Advanced Parameters (collapsible) */}
          <div className="space-y-3">
            <button
              type="button"
              onClick={() => setShowAdvanced(v => !v)}
              className="flex items-center gap-2 text-sm font-semibold text-gray-500 hover:text-green-700 transition-colors uppercase tracking-wide"
            >
              <ChevronDown className={`w-4 h-4 transition-transform ${showAdvanced ? 'rotate-180' : ''}`} />
              Advanced Soil Parameters
            </button>

            {showAdvanced && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2 animate-in slide-in-from-top-2 duration-200">
                {/* Soil Type */}
                <div className="space-y-2">
                  <Label htmlFor="soil_type" className="flex items-center gap-2 text-gray-700 text-sm">
                    Soil Type
                  </Label>
                  <select
                    id="soil_type"
                    name="soil_type"
                    defaultValue="1"
                    className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-green-500 focus:ring-1 focus:ring-green-500 outline-none"
                  >
                    <option value="0">Sandy</option>
                    <option value="1">Loamy</option>
                    <option value="2">Clay</option>
                  </select>
                </div>

                {/* Irrigation */}
                <div className="space-y-2">
                  <Label htmlFor="irrigation" className="flex items-center gap-2 text-gray-700 text-sm">
                    Irrigation
                  </Label>
                  <select
                    id="irrigation"
                    name="irrigation"
                    defaultValue="0"
                    className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-green-500 focus:ring-1 focus:ring-green-500 outline-none"
                  >
                    <option value="0">Rainfed</option>
                    <option value="1">Irrigated</option>
                  </select>
                </div>

                {/* Soil Moisture */}
                <FieldInput label="Soil Moisture" name="moisture" icon={<Droplet className="w-4 h-4 text-teal-600" />} placeholder="0-100" unit="%" step="0.1" defaultValue="43.5" required={false} errors={errors} onBlur={handleInputBlur} />
              </div>
            )}
          </div>

          {/* ── Mode Selector ──────────────────────────────────────── */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide border-b pb-2">
              Prediction Mode
            </h3>
            <input type="hidden" name="mode" value={mode} />
            <div className="grid grid-cols-3 gap-3">
              <ModeCard
                active={mode === 'original'}
                onClick={() => setMode('original')}
                icon={<Shield className="w-5 h-5" />}
                title="Original"
                subtitle="19 real-world crops"
                badge="V3 ensemble"
                badgeClass="bg-emerald-100 text-emerald-700 border-emerald-200"
              />
              <ModeCard
                active={mode === 'synthetic'}
                onClick={() => setMode('synthetic')}
                icon={<Layers className="w-5 h-5" />}
                title="Synthetic"
                subtitle="51 augmented crops"
                badge="Extended"
                badgeClass="bg-blue-100 text-blue-700 border-blue-200"
              />
              <ModeCard
                active={mode === 'both'}
                onClick={() => setMode('both')}
                icon={<Combine className="w-5 h-5" />}
                title="Both"
                subtitle="59 merged crops"
                badge="Full coverage"
                badgeClass="bg-purple-100 text-purple-700 border-purple-200"
              />
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

/* ── Mode toggle card ─────────────────────────────────────────────── */

function ModeCard({
  active, onClick, icon, title, subtitle, badge, badgeClass,
}: {
  active: boolean; onClick: () => void; icon: React.ReactNode;
  title: string; subtitle: string; badge: string; badgeClass: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`relative flex flex-col items-center gap-2 rounded-xl border-2 p-4 transition-all duration-200 text-center
        ${active
          ? 'border-green-500 bg-green-50/70 ring-2 ring-green-200 shadow-md'
          : 'border-gray-200 bg-white hover:border-green-300 hover:bg-green-50/30'
        }`}
    >
      <div className={`rounded-full p-2 ${active ? 'bg-green-600 text-white' : 'bg-gray-100 text-gray-500'}`}>
        {icon}
      </div>
      <div>
        <p className={`font-semibold text-sm ${active ? 'text-green-900' : 'text-gray-700'}`}>{title}</p>
        <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>
      </div>
      <Badge variant="outline" className={`text-[10px] px-2 py-0.5 ${badgeClass}`}>{badge}</Badge>
      {active && (
        <div className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-green-600 flex items-center justify-center">
          <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
          </svg>
        </div>
      )}
    </button>
  );
}
