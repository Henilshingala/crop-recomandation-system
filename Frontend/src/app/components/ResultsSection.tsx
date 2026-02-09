import { Card, CardContent, CardHeader, CardTitle } from "@/app/components/ui/card";
import { Badge } from "@/app/components/ui/badge";
import { Sprout, TrendingUp, AlertCircle, Calendar } from "lucide-react";
import { type CropRecommendation } from "@/app/services/api";
import { useEffect, useState, useMemo } from "react";

interface ResultsSectionProps {
  recommendations: CropRecommendation[];
}

// Auto Carousel Component
function AutoCarousel({ images, alt }: { images: string[], alt: string }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  
  // Memoize images to prevent unnecessary re-renders
  const imageList = useMemo(() => images, [JSON.stringify(images)]);

  useEffect(() => {
    if (imageList.length <= 1) return; // Don't auto-advance if only 1 image
    
    // Auto-advance carousel every 3 seconds
    const interval = setInterval(() => {
      setCurrentIndex((prevIndex) => (prevIndex + 1) % imageList.length);
    }, 3000);

    return () => clearInterval(interval);
  }, [imageList.length]);

  return (
    <div className="relative w-full aspect-square">
      {imageList.map((image, index) => (
        <img
          key={`${image}-${index}`}
          src={image}
          alt={`${alt} - Image ${index + 1}`}
          className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-500 ${
            index === currentIndex ? 'opacity-100' : 'opacity-0'
          }`}
          onError={(e) => {
            (e.target as HTMLImageElement).src = `https://via.placeholder.com/400x400?text=${alt}`;
          }}
        />
      ))}
      
      {/* Carousel Indicators */}
      {imageList.length > 1 && (
        <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex gap-2">
          {imageList.map((_, index) => (
            <button
              key={index}
              onClick={() => setCurrentIndex(index)}
              className={`w-2 h-2 rounded-full transition-all ${
                index === currentIndex 
                  ? 'bg-white w-6' 
                  : 'bg-white/50 hover:bg-white/75'
              }`}
              aria-label={`Go to image ${index + 1}`}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export function ResultsSection({ recommendations }: ResultsSectionProps) {
  const [selectedIndex, setSelectedIndex] = useState(0);

  if (!recommendations || recommendations.length === 0) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-yellow-700">
        No recommendations available. Please try again.
      </div>
    );
  }

  const topCrop = recommendations[selectedIndex];

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* Main Result Card - Top Recommendation */}
      <Card className="shadow-xl border-green-200 overflow-hidden">
        <div className="bg-gradient-to-r from-green-600 to-emerald-600 text-white px-6 py-8">
          <div className="flex items-center gap-3 mb-2">
            <Sprout className="w-8 h-8" />
            <h2 className="text-2xl font-bold">{selectedIndex === 0 ? "Top Recommendation" : "Selected Crop Details"}</h2>
          </div>
          <div className="flex items-baseline gap-3">
            <p className="text-5xl font-bold capitalize">{topCrop.crop}</p>
            <Badge className="bg-white text-green-700 text-sm font-semibold px-3 py-1">
              {topCrop.confidence.toFixed(1)}% Match
            </Badge>
          </div>
        </div>

        <CardContent className="p-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Crop Image Carousel - Square */}
            <div className="rounded-lg overflow-hidden shadow-md bg-gray-100 max-w-sm mx-auto lg:mx-0">
              {topCrop.image_urls && topCrop.image_urls.length > 0 ? (
                <AutoCarousel 
                  key={topCrop.crop} 
                  images={topCrop.image_urls} 
                  alt={topCrop.crop} 
                />
              ) : (
                <div className="aspect-square">
                  <img
                    key={topCrop.crop}
                    src={topCrop.image_url}
                    alt={topCrop.crop}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      (e.target as HTMLImageElement).src = `https://via.placeholder.com/400x400?text=${topCrop.crop}`;
                    }}
                  />
                </div>
              )}
            </div>

            {/* Nutrition Data */}
            {topCrop.nutrition && (
              <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Nutrition (per kg)
                </h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Energy:</span>
                    <span className="font-medium text-gray-900">{topCrop.nutrition.energy_kcal} kcal</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Protein:</span>
                    <span className="font-medium text-gray-900">{topCrop.nutrition.protein_g} g</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Carbs:</span>
                    <span className="font-medium text-gray-900">{topCrop.nutrition.carbs_g} g</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Fat:</span>
                    <span className="font-medium text-gray-900">{topCrop.nutrition.fat_g} g</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Fiber:</span>
                    <span className="font-medium text-gray-900">{topCrop.nutrition.fiber_g} g</span>
                  </div>
                  <div className="h-px bg-green-200 my-2"></div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Iron:</span>
                    <span className="font-medium text-gray-900">{topCrop.nutrition.iron_mg} mg</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Calcium:</span>
                    <span className="font-medium text-gray-900">{topCrop.nutrition.calcium_mg} mg</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Vitamin A:</span>
                    <span className="font-medium text-gray-900">{topCrop.nutrition.vitamin_a_mcg} mcg</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Vitamin C:</span>
                    <span className="font-medium text-gray-900">{topCrop.nutrition.vitamin_c_mg} mg</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Water:</span>
                    <span className="font-medium text-gray-900">{topCrop.nutrition.water_g} g</span>
                  </div>
                </div>
              </div>
            )}

            {/* Details */}
            <div className="space-y-4">
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">About {topCrop.crop}</h3>
                <p className="text-gray-600">
                  Based on your soil nutrients and environmental conditions, <strong className="capitalize">{topCrop.crop}</strong> is 
                  the best suited crop for your field with a {topCrop.confidence.toFixed(1)}% confidence match.
                </p>
              </div>

              <div className="flex items-center gap-2 text-sm">
                <Calendar className="w-4 h-4 text-green-600" />
                <span className="font-medium">Best Season:</span>
                <span className="text-gray-700">{topCrop.season || 'Not specified'}</span>
              </div>

              <div className="flex items-center gap-2 text-sm">
                <TrendingUp className="w-4 h-4 text-green-600" />
                <span className="font-medium">Expected Yield:</span>
                <span className="text-gray-700">{topCrop.expected_yield || 'Varies by conditions'}</span>
              </div>

              {/* Confidence Bar */}
              <div className="pt-4">
                <div className="flex justify-between text-sm mb-1">
                  <span className="font-medium text-gray-700">Confidence Score</span>
                  <span className="text-green-600 font-bold">{topCrop.confidence.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div 
                    className="bg-gradient-to-r from-green-500 to-emerald-500 h-3 rounded-full transition-all duration-500"
                    style={{ width: `${Math.min(topCrop.confidence, 100)}%` }}
                  />
                </div>
              </div>
            </div>
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
          <p className="text-sm text-green-700 mt-1">Click on a crop to view detailed information above.</p>
        </CardHeader>
        <CardContent className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {recommendations.slice(0, 3).map((crop, index) => (
              <Card 
                key={crop.crop} 
                className={`border-2 transition-all duration-300 cursor-pointer hover:shadow-md transform hover:-translate-y-1 ${
                  index === selectedIndex 
                    ? 'border-green-500 bg-green-50 ring-2 ring-green-200' 
                    : 'border-transparent hover:border-green-200'
                }`}
                onClick={() => {
                  setSelectedIndex(index);
                  window.scrollTo({ top: 0, behavior: 'smooth' });
                }}
              >
                <CardContent className="p-4">
                  {/* Crop Image */}
                  <div className="w-full h-32 bg-gray-100 rounded-lg mb-3 overflow-hidden">
                    <img
                      src={crop.image_url}
                      alt={crop.crop}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        (e.target as HTMLImageElement).src = `https://via.placeholder.com/200x150?text=${crop.crop}`;
                      }}
                    />
                  </div>

                  {/* Rank Badge */}
                  <div className="flex items-center justify-between mb-2">
                    <Badge 
                      variant="outline" 
                      className={`
                        ${index === 0 ? 'border-yellow-400 text-yellow-700 bg-yellow-50' : ''}
                        ${index === 1 ? 'border-gray-400 text-gray-700 bg-gray-50' : ''}
                        ${index === 2 ? 'border-orange-400 text-orange-700 bg-orange-50' : ''}
                      `}
                    >
                      #{index + 1}
                    </Badge>
                    <Badge className="bg-green-100 text-green-700 border border-green-200">
                      {crop.confidence.toFixed(1)}%
                    </Badge>
                  </div>

                  {/* Crop Name */}
                  <h4 className="font-semibold text-lg text-gray-900 mb-2 capitalize">{crop.crop}</h4>

                  {/* Details */}
                  <div className="space-y-1 text-xs text-gray-500">
                    <div className="flex justify-between">
                      <span>Yield:</span>
                      <span className="text-gray-700">{crop.expected_yield || '—'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Season:</span>
                      <span className="text-gray-700">{crop.season || '—'}</span>
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
