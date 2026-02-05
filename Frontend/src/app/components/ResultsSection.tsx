import { Card, CardContent, CardHeader, CardTitle } from "@/app/components/ui/card";
import { Badge } from "@/app/components/ui/badge";
import { Sprout, TrendingUp, Droplet, Sun, AlertCircle, CloudRain, Thermometer, TreePine, Calendar, Leaf } from "lucide-react";

export function ResultsSection() {
  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* Main Result Card */}
      <Card className="shadow-xl border-green-200 overflow-hidden">
        <div className="bg-gradient-to-r from-green-600 to-emerald-600 text-white px-6 py-8">
          <div className="flex items-center gap-3 mb-2">
            <Sprout className="w-8 h-8" />
            <h2 className="text-2xl font-bold">Recommended Crop</h2>
          </div>
          <div className="flex items-baseline gap-3">
            <p className="text-5xl font-bold">—</p>
            <Badge className="bg-white text-green-700 text-sm font-semibold px-3 py-1">
              —%
            </Badge>
          </div>
        </div>

        <CardContent className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Image Placeholder */}
            <div className="rounded-lg overflow-hidden shadow-md bg-gray-100 flex items-center justify-center h-64">
              <div className="text-center text-gray-400">
                <Sprout className="w-16 h-16 mx-auto mb-2 opacity-30" />
                <p className="text-sm">Crop Image</p>
              </div>
            </div>

            {/* Details */}
            <div className="space-y-4">
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">About This Crop</h3>
                <div className="space-y-2">
                  <div className="h-3 bg-gray-200 rounded w-full"></div>
                  <div className="h-3 bg-gray-200 rounded w-5/6"></div>
                  <div className="h-3 bg-gray-200 rounded w-4/6"></div>
                </div>
              </div>

              <div className="flex items-center gap-2 text-sm">
                <Sun className="w-4 h-4 text-orange-500" />
                <span className="font-medium">Best Season:</span>
                <span className="text-gray-400">—</span>
              </div>

              <div className="flex items-center gap-2 text-sm">
                <TrendingUp className="w-4 h-4 text-green-600" />
                <span className="font-medium">Expected Yield:</span>
                <span className="text-gray-400">—</span>
              </div>
            </div>
          </div>

          {/* Crop Details Section */}
          <div className="mt-6 pt-6 border-t">
            <h3 className="font-semibold text-gray-900 mb-4 text-lg">Crop Details</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Soil Suitability */}
              <div className="flex items-start gap-3 p-4 bg-amber-50 rounded-lg border border-amber-100">
                <TreePine className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-gray-900 text-sm">Soil Suitability</p>
                  <p className="text-sm text-gray-400 mt-1">—</p>
                </div>
              </div>

              {/* Climate Suitability */}
              <div className="flex items-start gap-3 p-4 bg-sky-50 rounded-lg border border-sky-100">
                <Thermometer className="w-5 h-5 text-sky-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-gray-900 text-sm">Climate Suitability</p>
                  <p className="text-sm text-gray-400 mt-1">—</p>
                </div>
              </div>

              {/* Growing Season */}
              <div className="flex items-start gap-3 p-4 bg-green-50 rounded-lg border border-green-100">
                <Calendar className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-gray-900 text-sm">Growing Season</p>
                  <p className="text-sm text-gray-400 mt-1">—</p>
                </div>
              </div>

              {/* Water Requirement */}
              <div className="flex items-start gap-3 p-4 bg-blue-50 rounded-lg border border-blue-100">
                <CloudRain className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-gray-900 text-sm">Water Requirement</p>
                  <p className="text-sm text-gray-400 mt-1">—</p>
                </div>
              </div>

              {/* Fertilizer Note */}
              <div className="flex items-start gap-3 p-4 bg-purple-50 rounded-lg border border-purple-100 md:col-span-2">
                <Leaf className="w-5 h-5 text-purple-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-gray-900 text-sm">Fertilizer Recommendation</p>
                  <p className="text-sm text-gray-400 mt-1">—</p>
                </div>
              </div>
            </div>
          </div>

          {/* Cultivation Tips */}
          <div className="mt-6 pt-6 border-t">
            <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <Droplet className="w-5 h-5 text-blue-600" />
              Cultivation Tips
            </h3>
            <ul className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {[1, 2, 3, 4].map((item) => (
                <li key={item} className="flex items-start gap-2 text-sm">
                  <span className="text-green-600 font-bold mt-0.5">•</span>
                  <div className="h-3 bg-gray-200 rounded flex-1 mt-1"></div>
                </li>
              ))}
            </ul>
          </div>

          {/* Info Alert */}
          <div className="mt-6 bg-amber-50 border border-amber-200 rounded-lg p-4 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-amber-800">
              <p className="font-semibold mb-1">Important Note</p>
              <p>
                This recommendation is based on the parameters you provided. For best results, 
                consult with local agricultural experts and consider regional factors like local climate patterns and market demand.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Top 3 Recommendations */}
      <Card className="shadow-lg border-green-100">
        <CardHeader className="bg-gradient-to-r from-green-50 to-emerald-50">
          <CardTitle className="text-xl text-green-900 flex items-center gap-2">
            <TrendingUp className="w-6 h-6" />
            Top 3 Recommended Crops
          </CardTitle>
        </CardHeader>
        <CardContent className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[1, 2, 3].map((rank) => (
              <Card key={rank} className="border-2 hover:border-green-300 transition-colors cursor-pointer">
                <CardContent className="p-4">
                  {/* Image Placeholder */}
                  <div className="w-full h-32 bg-gray-100 rounded-lg mb-3 flex items-center justify-center">
                    <Sprout className="w-10 h-10 text-gray-300" />
                  </div>

                  {/* Rank Badge */}
                  <div className="flex items-center justify-between mb-2">
                    <Badge 
                      variant="outline" 
                      className={`
                        ${rank === 1 ? 'border-yellow-400 text-yellow-700 bg-yellow-50' : ''}
                        ${rank === 2 ? 'border-gray-400 text-gray-700 bg-gray-50' : ''}
                        ${rank === 3 ? 'border-orange-400 text-orange-700 bg-orange-50' : ''}
                      `}
                    >
                      #{rank}
                    </Badge>
                    <Badge className="bg-green-100 text-green-700 border border-green-200">
                      —%
                    </Badge>
                  </div>

                  {/* Crop Name Placeholder */}
                  <h4 className="font-semibold text-lg text-gray-900 mb-2">—</h4>

                  {/* Details */}
                  <div className="space-y-1 text-xs text-gray-500">
                    <div className="flex justify-between">
                      <span>Yield:</span>
                      <span className="text-gray-400">—</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Season:</span>
                      <span className="text-gray-400">—</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Action Button */}
      <div className="flex justify-center">
        <button
          onClick={() => window.location.reload()}
          className="px-6 py-3 border-2 border-green-600 text-green-700 rounded-lg font-semibold hover:bg-green-50 transition-colors"
        >
          Try Another Analysis
        </button>
      </div>
    </div>
  );
}
