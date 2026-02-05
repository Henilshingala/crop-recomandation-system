import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card";
import { Input } from "@/app/components/ui/input";
import { Label } from "@/app/components/ui/label";
import { Button } from "@/app/components/ui/button";
import { Droplet, Thermometer, FlaskConical, CloudRain, Gauge, Loader2 } from "lucide-react";
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
};

export function InputForm({ onSubmit, isLoading = false }: InputFormProps) {
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateField = (name: string, value: string) => {
    const numValue = parseFloat(value);
    const range = VALIDATION_RANGES[name as keyof typeof VALIDATION_RANGES];
    
    if (!range) return "";
    
    if (isNaN(numValue)) {
      return `Please enter a valid number`;
    }
    
    if (numValue < range.min) {
      return `Value must be greater than or equal to ${range.min} ${range.unit}`;
    }
    
    if (numValue > range.max) {
      return `Value must be less than or equal to ${range.max} ${range.unit}`;
    }
    
    return "";
  };

  const handleInputBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    const error = validateField(name, value);
    
    setErrors(prev => ({
      ...prev,
      [name]: error
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate all fields
    const form = e.target as HTMLFormElement;
    const formData = new FormData(form);
    const newErrors: Record<string, string> = {};
    let hasError = false;
    
    Object.keys(VALIDATION_RANGES).forEach(fieldName => {
      const value = formData.get(fieldName) as string;
      const error = validateField(fieldName, value);
      if (error) {
        newErrors[fieldName] = error;
        hasError = true;
      }
    });
    
    setErrors(newErrors);
    
    if (!hasError) {
      onSubmit(e);
    }
  };

  return (
    <Card className="shadow-lg border-green-100">
      <CardHeader className="bg-gradient-to-r from-green-50 to-emerald-50">
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
              {/* Nitrogen */}
              <div className="space-y-2">
                <Label htmlFor="nitrogen" className="flex items-center gap-2 text-gray-700">
                  <FlaskConical className="w-4 h-4 text-blue-600" />
                  Nitrogen (N)
                </Label>
                <div className="relative">
                  <Input
                    id="nitrogen"
                    name="nitrogen"
                    type="number"
                    step="0.01"
                    placeholder="0-150"
                    required
                    onBlur={handleInputBlur}
                    className={`rounded-lg border-gray-300 focus:border-green-500 focus:ring-green-500 ${errors.nitrogen ? 'border-red-500' : ''}`}
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-400">
                    kg/ha
                  </span>
                </div>
                {errors.nitrogen && (
                  <p className="text-xs text-red-600 mt-1">{errors.nitrogen}</p>
                )}
              </div>

              {/* Phosphorus */}
              <div className="space-y-2">
                <Label htmlFor="phosphorus" className="flex items-center gap-2 text-gray-700">
                  <FlaskConical className="w-4 h-4 text-orange-600" />
                  Phosphorus (P)
                </Label>
                <div className="relative">
                  <Input
                    id="phosphorus"
                    name="phosphorus"
                    type="number"
                    step="0.01"
                    placeholder="0-150"
                    required
                    onBlur={handleInputBlur}
                    className={`rounded-lg border-gray-300 focus:border-green-500 focus:ring-green-500 ${errors.phosphorus ? 'border-red-500' : ''}`}
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-400">
                    kg/ha
                  </span>
                </div>
                {errors.phosphorus && (
                  <p className="text-xs text-red-600 mt-1">{errors.phosphorus}</p>
                )}
              </div>

              {/* Potassium */}
              <div className="space-y-2">
                <Label htmlFor="potassium" className="flex items-center gap-2 text-gray-700">
                  <FlaskConical className="w-4 h-4 text-purple-600" />
                  Potassium (K)
                </Label>
                <div className="relative">
                  <Input
                    id="potassium"
                    name="potassium"
                    type="number"
                    step="0.01"
                    placeholder="0-300"
                    required
                    onBlur={handleInputBlur}
                    className={`rounded-lg border-gray-300 focus:border-green-500 focus:ring-green-500 ${errors.potassium ? 'border-red-500' : ''}`}
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-400">
                    kg/ha
                  </span>
                </div>
                {errors.potassium && (
                  <p className="text-xs text-red-600 mt-1">{errors.potassium}</p>
                )}
              </div>
            </div>
          </div>

          {/* Environmental Conditions */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide border-b pb-2">
              Environmental Conditions
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Temperature */}
              <div className="space-y-2">
                <Label htmlFor="temperature" className="flex items-center gap-2 text-gray-700">
                  <Thermometer className="w-4 h-4 text-red-600" />
                  Temperature
                </Label>
                <div className="relative">
                  <Input
                    id="temperature"
                    name="temperature"
                    type="number"
                    step="0.1"
                    placeholder="0-50"
                    required
                    onBlur={handleInputBlur}
                    className={`rounded-lg border-gray-300 focus:border-green-500 focus:ring-green-500 ${errors.temperature ? 'border-red-500' : ''}`}
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-400">
                    °C
                  </span>
                </div>
                {errors.temperature && (
                  <p className="text-xs text-red-600 mt-1">{errors.temperature}</p>
                )}
              </div>

              {/* Humidity */}
              <div className="space-y-2">
                <Label htmlFor="humidity" className="flex items-center gap-2 text-gray-700">
                  <Droplet className="w-4 h-4 text-blue-600" />
                  Humidity
                </Label>
                <div className="relative">
                  <Input
                    id="humidity"
                    name="humidity"
                    type="number"
                    step="0.1"
                    placeholder="0-100"
                    required
                    onBlur={handleInputBlur}
                    className={`rounded-lg border-gray-300 focus:border-green-500 focus:ring-green-500 ${errors.humidity ? 'border-red-500' : ''}`}
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-400">
                    %
                  </span>
                </div>
                {errors.humidity && (
                  <p className="text-xs text-red-600 mt-1">{errors.humidity}</p>
                )}
              </div>

              {/* pH */}
              <div className="space-y-2">
                <Label htmlFor="ph" className="flex items-center gap-2 text-gray-700">
                  <Gauge className="w-4 h-4 text-green-600" />
                  Soil pH
                </Label>
                <div className="relative">
                  <Input
                    id="ph"
                    name="ph"
                    type="number"
                    step="0.1"
                    placeholder="3.5-9.5"
                    required
                    onBlur={handleInputBlur}
                    className={`rounded-lg border-gray-300 focus:border-green-500 focus:ring-green-500 ${errors.ph ? 'border-red-500' : ''}`}
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-400">
                    pH
                  </span>
                </div>
                {errors.ph && (
                  <p className="text-xs text-red-600 mt-1">{errors.ph}</p>
                )}
              </div>

              {/* Rainfall */}
              <div className="space-y-2">
                <Label htmlFor="rainfall" className="flex items-center gap-2 text-gray-700">
                  <CloudRain className="w-4 h-4 text-sky-600" />
                  Rainfall
                </Label>
                <div className="relative">
                  <Input
                    id="rainfall"
                    name="rainfall"
                    type="number"
                    step="0.1"
                    placeholder="0-3000"
                    required
                    onBlur={handleInputBlur}
                    className={`rounded-lg border-gray-300 focus:border-green-500 focus:ring-green-500 ${errors.rainfall ? 'border-red-500' : ''}`}
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-400">
                    mm
                  </span>
                </div>
                {errors.rainfall && (
                  <p className="text-xs text-red-600 mt-1">{errors.rainfall}</p>
                )}
              </div>
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
