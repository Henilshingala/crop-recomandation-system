import { Card, CardContent, CardHeader, CardTitle } from "@/app/components/ui/card";
import { Badge } from "@/app/components/ui/badge";
import { Sprout, TrendingUp, AlertCircle, Calendar, Shield, Layers, Combine } from "lucide-react";
import { type PredictionResponse, type CropRecommendation } from "@/app/services/api";
import { useEffect, useState, useMemo } from "react";

interface ResultsSectionProps {
  data: PredictionResponse;
}

/* ── Auto Carousel ────────────────────────────────────────────────── */

function AutoCarousel({ images, alt }: { images: string[]; alt: string }) {
  const [idx, setIdx] = useState(0);
  const list = useMemo(() => images, [JSON.stringify(images)]);

  useEffect(() => {
    if (list.length <= 1) return;
    const id = setInterval(() => setIdx(i => (i + 1) % list.length), 3000);
    return () => clearInterval(id);
  }, [list.length]);

  return (
    <div className="relative w-full aspect-square">
      {list.map((src, i) => (
        <img
          key={`${src}-${i}`}
          src={src}
          alt={`${alt} ${i + 1}`}
          className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-500 ${i === idx ? 'opacity-100' : 'opacity-0'}`}
          onError={e => { (e.target as HTMLImageElement).src = `https://via.placeholder.com/400x400?text=${alt}`; }}
        />
      ))}
      {list.length > 1 && (
        <div className="absolute bottom-3 left-1/2 -translate-x-1/2 flex gap-1.5">
          {list.map((_, i) => (
            <button key={i} onClick={() => setIdx(i)}
              className={`h-1.5 rounded-full transition-all ${i === idx ? 'bg-white w-5' : 'bg-white/50 w-1.5 hover:bg-white/75'}`}
            />
          ))}
        </div>
      )}
    </div>
  );
}

/* ── Confidence bar ───────────────────────────────────────────────── */

function ConfidenceBar({ value, size = "md" }: { value: number; size?: "sm" | "md" }) {
  const h = size === "sm" ? "h-2" : "h-3";
  const color =
    value >= 75 ? "from-green-500 to-emerald-500"
    : value >= 50 ? "from-yellow-400 to-amber-500"
    : "from-orange-400 to-red-500";
  const textColor =
    value >= 75 ? "text-green-700"
    : value >= 50 ? "text-amber-700"
    : "text-red-700";

  return (
    <div className="w-full">
      <div className="flex justify-between text-sm mb-1">
        <span className="font-medium text-gray-600">Confidence</span>
        <span className={`font-bold ${textColor}`}>{value.toFixed(1)}%</span>
      </div>
      <div className={`w-full bg-gray-200 rounded-full ${h}`}>
        <div
          className={`bg-gradient-to-r ${color} ${h} rounded-full transition-all duration-700 ease-out`}
          style={{ width: `${Math.min(value, 100)}%` }}
        />
      </div>
    </div>
  );
}

/* ── Mode badge ───────────────────────────────────────────────────── */

function ModeBadge({ mode }: { mode: string }) {
  if (mode === "original") {
    return (
      <Badge className="bg-emerald-100 text-emerald-800 border border-emerald-300 gap-1.5 px-3 py-1 text-xs font-medium">
        <Shield className="w-3 h-3" />
        Original — 19 real-world crops
      </Badge>
    );
  }
  if (mode === "synthetic") {
    return (
      <Badge className="bg-blue-100 text-blue-800 border border-blue-300 gap-1.5 px-3 py-1 text-xs font-medium">
        <Layers className="w-3 h-3" />
        Synthetic — 51 augmented crops
      </Badge>
    );
  }
  return (
    <Badge className="bg-purple-100 text-purple-800 border border-purple-300 gap-1.5 px-3 py-1 text-xs font-medium">
      <Combine className="w-3 h-3" />
      Both — 59 merged crops
    </Badge>
  );
}

/* ── Main component ───────────────────────────────────────────────── */

export function ResultsSection({ data }: ResultsSectionProps) {
  const { mode, top_1, top_3, model_info } = data;
  const [selectedIdx, setSelectedIdx] = useState(0);
  const selected = top_3[selectedIdx] ?? top_1;

  if (!top_1 || !top_3?.length) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-yellow-700">
        No recommendations available. Please try again.
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-500">

      {/* ── Top-1 Hero Card ────────────────────────────────────────── */}
      <Card className="shadow-xl border-0 overflow-hidden bg-white/80 backdrop-blur-sm">
        {/* Header gradient */}
        <div className="bg-gradient-to-r from-green-600 to-emerald-600 text-white px-6 py-8">
          <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
            <div className="flex items-center gap-3">
              <Sprout className="w-8 h-8" />
              <h2 className="text-2xl font-bold">
                {selectedIdx === 0 ? "Top Recommendation" : "Selected Crop"}
              </h2>
            </div>
            <ModeBadge mode={mode} />
          </div>

          <div className="flex items-baseline gap-4">
            <p className="text-5xl font-bold capitalize">{selected.crop}</p>
            <Badge className="bg-white/20 backdrop-blur text-white text-sm font-semibold px-3 py-1 border border-white/30">
              {selected.confidence.toFixed(1)}% Match
            </Badge>
          </div>
        </div>

        <CardContent className="p-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

            {/* Image carousel */}
            <div className="rounded-xl overflow-hidden shadow-md bg-gray-100 max-w-sm mx-auto lg:mx-0">
              {selected.image_urls && selected.image_urls.length > 0 ? (
                <AutoCarousel key={selected.crop} images={selected.image_urls} alt={selected.crop} />
              ) : (
                <div className="aspect-square">
                  <img
                    src={selected.image_url || `https://via.placeholder.com/400x400?text=${selected.crop}`}
                    alt={selected.crop}
                    className="w-full h-full object-cover"
                    onError={e => { (e.target as HTMLImageElement).src = `https://via.placeholder.com/400x400?text=${selected.crop}`; }}
                  />
                </div>
              )}
            </div>

            {/* Nutrition */}
            {selected.nutrition && (
              <div className="bg-green-50/70 backdrop-blur-sm rounded-xl p-4 border border-green-200/60">
                <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Nutrition (per kg)
                </h3>
                <div className="space-y-1.5 text-sm">
                  {([
                    ["Energy", selected.nutrition.energy_kcal, "kcal"],
                    ["Protein", selected.nutrition.protein_g, "g"],
                    ["Carbs", selected.nutrition.carbs_g, "g"],
                    ["Fat", selected.nutrition.fat_g, "g"],
                    ["Fiber", selected.nutrition.fiber_g, "g"],
                  ] as const).map(([k, v, u]) => (
                    <div key={k} className="flex justify-between">
                      <span className="text-gray-600">{k}:</span>
                      <span className="font-medium text-gray-900">{v} {u}</span>
                    </div>
                  ))}
                  <div className="h-px bg-green-200 my-1.5" />
                  {([
                    ["Iron", selected.nutrition.iron_mg, "mg"],
                    ["Calcium", selected.nutrition.calcium_mg, "mg"],
                    ["Vitamin A", selected.nutrition.vitamin_a_mcg, "mcg"],
                    ["Vitamin C", selected.nutrition.vitamin_c_mg, "mg"],
                    ["Water", selected.nutrition.water_g, "g"],
                  ] as const).map(([k, v, u]) => (
                    <div key={k} className="flex justify-between">
                      <span className="text-gray-600">{k}:</span>
                      <span className="font-medium text-gray-900">{v} {u}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Details column */}
            <div className="space-y-4">
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">About {selected.crop}</h3>
                <p className="text-gray-600 text-sm">
                  Based on your soil nutrients and environmental conditions,{" "}
                  <strong className="capitalize">{selected.crop}</strong> is the best suited crop
                  with a {selected.confidence.toFixed(1)}% confidence match.
                </p>
              </div>

              <div className="flex items-center gap-2 text-sm">
                <Calendar className="w-4 h-4 text-green-600" />
                <span className="font-medium">Season:</span>
                <span className="text-gray-700">{selected.season || "Not specified"}</span>
              </div>

              <div className="flex items-center gap-2 text-sm">
                <TrendingUp className="w-4 h-4 text-green-600" />
                <span className="font-medium">Expected Yield:</span>
                <span className="text-gray-700">{selected.expected_yield || "Varies by conditions"}</span>
              </div>

              {/* Confidence bar */}
              <div className="pt-2">
                <ConfidenceBar value={selected.confidence} />
              </div>

              {/* Model coverage pill */}
              <div className="flex items-center gap-2 pt-1">
                <span className="text-xs text-gray-500">Model coverage:</span>
                <Badge variant="outline" className="text-[10px] border-gray-300 text-gray-600">
                  {model_info.coverage} crops &middot; {model_info.type}
                </Badge>
              </div>
            </div>
          </div>

          {/* Info alert */}
          <div className="mt-6 bg-amber-50/70 backdrop-blur-sm border border-amber-200/60 rounded-xl p-4 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-amber-800">
              <p className="font-semibold mb-1">Important Note</p>
              <p>
                This recommendation is based on the parameters you provided. For best results,
                consult with local agricultural experts and consider regional factors.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ── Top-3 Ranked List ─────────────────────────────────────── */}
      <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
        <CardHeader className="bg-gradient-to-r from-green-50/80 to-emerald-50/80">
          <CardTitle className="text-xl text-green-900 flex items-center gap-2">
            <TrendingUp className="w-6 h-6" />
            Top 3 Recommended Crops
          </CardTitle>
          <p className="text-sm text-green-700 mt-1">Click a crop to view details above</p>
        </CardHeader>
        <CardContent className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {top_3.slice(0, 3).map((crop, i) => (
              <button
                key={crop.crop}
                type="button"
                onClick={() => { setSelectedIdx(i); window.scrollTo({ top: 0, behavior: "smooth" }); }}
                className={`text-left rounded-xl border-2 p-4 transition-all duration-200 hover:shadow-md hover:-translate-y-0.5
                  ${i === selectedIdx
                    ? "border-green-500 bg-green-50/70 ring-2 ring-green-200 shadow-md"
                    : "border-gray-200 bg-white/70 hover:border-green-300"
                  }`}
              >
                {/* Image */}
                <div className="w-full h-32 bg-gray-100 rounded-lg mb-3 overflow-hidden">
                  <img
                    src={crop.image_url || `https://via.placeholder.com/200x150?text=${crop.crop}`}
                    alt={crop.crop}
                    className="w-full h-full object-cover"
                    onError={e => { (e.target as HTMLImageElement).src = `https://via.placeholder.com/200x150?text=${crop.crop}`; }}
                  />
                </div>

                {/* Rank + confidence */}
                <div className="flex items-center justify-between mb-2">
                  <Badge
                    variant="outline"
                    className={
                      i === 0 ? "border-yellow-400 text-yellow-700 bg-yellow-50"
                      : i === 1 ? "border-gray-400 text-gray-600 bg-gray-50"
                      : "border-orange-400 text-orange-700 bg-orange-50"
                    }
                  >
                    #{i + 1}
                  </Badge>
                  <Badge className={`text-xs border ${
                    crop.confidence >= 75 ? 'bg-green-100 text-green-700 border-green-200'
                    : crop.confidence >= 50 ? 'bg-yellow-100 text-yellow-700 border-yellow-200'
                    : 'bg-red-100 text-red-700 border-red-200'
                  }`}>
                    {crop.confidence.toFixed(1)}%
                  </Badge>
                </div>

                <h4 className="font-semibold text-lg text-gray-900 mb-2 capitalize">{crop.crop}</h4>

                <ConfidenceBar value={crop.confidence} size="sm" />

                <div className="mt-3 space-y-1 text-xs text-gray-500">
                  <div className="flex justify-between">
                    <span>Yield:</span>
                    <span className="text-gray-700">{crop.expected_yield || "—"}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Season:</span>
                    <span className="text-gray-700">{crop.season || "—"}</span>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Try another */}
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
