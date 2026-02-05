import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card";
import { Input } from "@/app/components/ui/input";
import { Label } from "@/app/components/ui/label";
import { Button } from "@/app/components/ui/button";
import { Droplet, Thermometer, FlaskConical, CloudRain, Gauge } from "lucide-react";

interface InputFormProps {
  onSubmit: (e: React.FormEvent) => void;
}

export function InputForm({ onSubmit }: InputFormProps) {
  return (
    <Card className="shadow-lg border-green-100">
      <CardHeader className="bg-gradient-to-r from-green-50 to-emerald-50">
        <CardTitle className="text-2xl text-green-900">Soil & Environmental Parameters</CardTitle>
        <CardDescription className="text-green-700">
          Enter your field's measurements to get personalized crop recommendations
        </CardDescription>
      </CardHeader>
      <CardContent className="pt-6">
        <form onSubmit={onSubmit} className="space-y-6">
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
                    placeholder="0-140"
                    required
                    className="rounded-lg border-gray-300 focus:border-green-500 focus:ring-green-500"
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-400">
                    kg/ha
                  </span>
                </div>
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
                    placeholder="0-145"
                    required
                    className="rounded-lg border-gray-300 focus:border-green-500 focus:ring-green-500"
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-400">
                    kg/ha
                  </span>
                </div>
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
                    placeholder="0-205"
                    required
                    className="rounded-lg border-gray-300 focus:border-green-500 focus:ring-green-500"
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-400">
                    kg/ha
                  </span>
                </div>
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
                    className="rounded-lg border-gray-300 focus:border-green-500 focus:ring-green-500"
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-400">
                    °C
                  </span>
                </div>
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
                    className="rounded-lg border-gray-300 focus:border-green-500 focus:ring-green-500"
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-400">
                    %
                  </span>
                </div>
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
                    placeholder="3.0-10.0"
                    required
                    className="rounded-lg border-gray-300 focus:border-green-500 focus:ring-green-500"
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-400">
                    pH
                  </span>
                </div>
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
                    placeholder="0-300"
                    required
                    className="rounded-lg border-gray-300 focus:border-green-500 focus:ring-green-500"
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-400">
                    mm
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Submit Button */}
          <Button 
            type="submit" 
            className="w-full bg-green-600 hover:bg-green-700 text-white py-6 rounded-lg text-lg font-semibold shadow-lg transition-all hover:shadow-xl"
          >
            Get Crop Recommendation
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
