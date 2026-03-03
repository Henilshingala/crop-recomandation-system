import { Card, CardContent, CardHeader, CardTitle } from "@/app/components/ui/card";
import { Badge } from "@/app/components/ui/badge";
import {
  Sprout, TrendingUp, AlertCircle, Calendar, ChevronDown,
  ShieldAlert, Info,
} from "lucide-react";
import { type PredictionResponse, type CropRecommendation } from "@/app/services/api";
import { useEffect, useState, useMemo } from "react";
import { useTranslation } from "react-i18next";

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

/* ── Animated confidence bar ──────────────────────────────────────── */

function ConfidenceBar({ value, size = "md" }: { value: number; size?: "sm" | "md" }) {
  const { t } = useTranslation();
  const [width, setWidth] = useState(0);
  useEffect(() => {
    const timer = setTimeout(() => setWidth(Math.min(value, 100)), 100);
    return () => clearTimeout(timer);
  }, [value]);

  const h = size === "sm" ? "h-2.5" : "h-3.5";
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
      <div className="flex justify-between text-sm mb-1.5">
        <span className="font-medium text-gray-600">{t("results.confidence")}</span>
        <span className={`font-bold ${textColor}`}>{value.toFixed(1)}%</span>
      </div>
      <div className={`w-full bg-gray-200 rounded-full ${h} overflow-hidden`}>
        <div
          className={`bg-gradient-to-r ${color} ${h} rounded-full transition-all duration-1000 ease-out`}
          style={{ width: `${width}%` }}
        />
      </div>
    </div>
  );
}

/* ── Advisory tier badge ──────────────────────────────────────────── */

function AdvisoryBadge({ tier }: { tier?: string }) {
  const { t } = useTranslation();
  if (!tier) return null;
  const tl = tier.toLowerCase();

  // Map API tier value to i18n key
  const tierLabel = tl.includes("strongly") ? t("tiers.stronglyRecommended")
    : tl === "recommended" ? t("tiers.recommended")
    : tl.includes("conditional") ? t("tiers.conditional")
    : t("tiers.notRecommended");

  if (tl.includes("strongly")) {
    return (
      <Badge className="bg-emerald-100 text-emerald-800 border border-emerald-300 gap-1.5 px-3 py-1 text-xs font-semibold shadow-sm">
        {tierLabel}
      </Badge>
    );
  }
  if (tl === "recommended") {
    return (
      <Badge className="bg-blue-100 text-blue-800 border border-blue-300 gap-1.5 px-3 py-1 text-xs font-semibold shadow-sm">
        {tierLabel}
      </Badge>
    );
  }
  if (tl.includes("conditional")) {
    return (
      <Badge className="bg-amber-100 text-amber-800 border border-amber-300 gap-1.5 px-3 py-1 text-xs font-semibold shadow-sm">
        {tierLabel}
      </Badge>
    );
  }
  return (
    <Badge className="bg-red-100 text-red-800 border border-red-300 gap-1.5 px-3 py-1 text-xs font-semibold shadow-sm">
      {tierLabel}
    </Badge>
  );
}

/* ── Consensus pill ───────────────────────────────────────────────── */

function ConsensusPill({ consensus }: { consensus?: string }) {
  const { t } = useTranslation();
  if (!consensus) return null;
  const cls =
    consensus === "strong" ? "bg-green-100 text-green-700 border-green-200"
    : consensus === "moderate" ? "bg-yellow-100 text-yellow-700 border-yellow-200"
    : "bg-gray-100 text-gray-600 border-gray-200";

  const label = consensus === "strong" ? t("consensus.strong")
    : consensus === "moderate" ? t("consensus.moderate")
    : t("consensus.weak");

  return (
    <Badge variant="outline" className={`text-[10px] px-2 py-0.5 capitalize ${cls}`}>
      {label}
    </Badge>
  );
}

/* ── Stress indicator badge with tooltip ──────────────────────────── */

function StressBadge({ stressIndex }: { stressIndex?: number }) {
  const { t } = useTranslation();
  if (stressIndex === undefined || stressIndex === null) return null;
  const [showTip, setShowTip] = useState(false);

  const label =
    stressIndex < 0.2 ? t("stress.low")
    : stressIndex < 0.4 ? t("stress.moderate")
    : stressIndex < 0.6 ? t("stress.high")
    : t("stress.extreme");

  const cls =
    stressIndex < 0.2 ? "bg-green-100 text-green-700 border-green-300"
    : stressIndex < 0.4 ? "bg-yellow-100 text-yellow-700 border-yellow-300"
    : stressIndex < 0.6 ? "bg-orange-100 text-orange-700 border-orange-300"
    : "bg-red-100 text-red-700 border-red-300";

  return (
    <div className="relative inline-block">
      <button
        onMouseEnter={() => setShowTip(true)}
        onMouseLeave={() => setShowTip(false)}
        onClick={() => setShowTip(v => !v)}
        className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium border ${cls} cursor-help transition-colors`}
      >
        <ShieldAlert className="w-3 h-3" />
        {label}
      </button>
      {showTip && (
        <div className="absolute z-20 bottom-full left-1/2 -translate-x-1/2 mb-2 w-56 bg-gray-900 text-white text-xs rounded-lg p-3 shadow-lg pointer-events-none">
          <p className="font-medium mb-1">{t("stress.indexLabel", { value: (stressIndex * 100).toFixed(0) })}</p>
          <p className="text-gray-300 leading-relaxed">
            {t("stress.description")}
          </p>
          <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900" />
        </div>
      )}
    </div>
  );
}

/* ── "Why this crop?" expandable section ──────────────────────────── */

function WhyThisCrop({ explanation, crop }: { explanation?: string; crop: string }) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  if (!explanation) return null;

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden bg-gray-50/50 mt-3">
      <button
        type="button"
        onClick={() => setOpen(v => !v)}
        className="w-full flex items-center justify-between px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-100 transition-colors"
      >
        <span className="flex items-center gap-2">
          <Info className="w-4 h-4 text-green-600" />
          {t("results.whyCrop", { crop })}
        </span>
        <ChevronDown className={`w-4 h-4 transition-transform duration-300 ${open ? 'rotate-180' : ''}`} />
      </button>
      <div
        className={`overflow-hidden transition-all duration-300 ease-in-out ${
          open ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
        }`}
      >
        <div className="px-4 pb-3 text-sm text-gray-600 leading-relaxed border-t border-gray-200 pt-3">
          {explanation}
        </div>
      </div>
    </div>
  );
}

/* ── Main component ───────────────────────────────────────────────── */

export function ResultsSection({ data }: ResultsSectionProps) {
  const { t } = useTranslation();
  /** Translate an API crop name (e.g. "finger_millet") to the active locale */
  const tc = (crop: string) => t(`crops.${crop}`, { defaultValue: crop });
  const { top_1, top_3 } = data;
  const [selectedIdx, setSelectedIdx] = useState(0);
  const selected = top_3[selectedIdx] ?? top_1;
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setVisible(true), 50);
    return () => clearTimeout(timer);
  }, []);

  // V8.1: Detect all-not-recommended / fallback states
  const allNotRecommended = data.all_not_recommended
    ?? top_3.every(c => c.advisory_tier?.toLowerCase().includes("not recommended"));
  const fallbackMode = data.fallback_mode ?? false;
  const isUnsuitableState = allNotRecommended || fallbackMode;

  if (!top_1 || !top_3?.length) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-yellow-700">
        {t("results.noRecommendations")}
      </div>
    );
  }

  // Dynamic header gradient / border colors based on suitability
  const heroGradient = isUnsuitableState
    ? "from-amber-600 via-orange-600 to-red-600"
    : "from-green-600 via-emerald-600 to-teal-600";
  const cardSelectedBorder = isUnsuitableState
    ? "border-amber-400 bg-amber-50/70 ring-2 ring-amber-200 shadow-md"
    : "border-green-500 bg-green-50/70 ring-2 ring-green-200 shadow-md";
  const cardHoverBorder = isUnsuitableState
    ? "border-gray-200 bg-white/70 hover:border-amber-300"
    : "border-gray-200 bg-white/70 hover:border-green-300";

  return (
    <div className={`space-y-6 transition-all duration-700 ease-out ${visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>

      {/* ── Top-1 Hero Card ────────────────────────────────────────── */}
      <Card className="shadow-xl border-0 overflow-hidden bg-white/80 backdrop-blur-sm">
        {/* Header gradient */}
        <div className={`bg-gradient-to-r ${heroGradient} text-white px-6 py-8`}>
          <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
            <div className="flex items-center gap-3">
              {isUnsuitableState ? (
                <AlertCircle className="w-8 h-8" />
              ) : (
                <Sprout className="w-8 h-8" />
              )}
              <h2 className="text-2xl font-bold">
                {isUnsuitableState
                  ? t("results.unsuitableDetected")
                  : selectedIdx === 0 ? t("results.topRecommendation") : t("results.selectedCrop")}
              </h2>
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              <AdvisoryBadge tier={selected.advisory_tier} />
              <StressBadge stressIndex={data.stress_index} />
            </div>
          </div>

          <div className="flex items-baseline gap-4 flex-wrap">
            <p className="text-5xl font-bold capitalize">{tc(selected.crop)}</p>
            <Badge className="bg-white/20 backdrop-blur text-white text-sm font-semibold px-3 py-1 border border-white/30">
              {t("results.match", { value: selected.confidence.toFixed(1) })}
            </Badge>
            <ConsensusPill consensus={selected.model_consensus} />
          </div>
        </div>

        {/* V8.1: Unsuitable conditions warning banner */}
        {isUnsuitableState && (
          <div className="bg-amber-900/30 border-t border-amber-400/40 px-6 py-3">
            <p className="text-amber-100 text-sm leading-relaxed">
              {fallbackMode
                ? t("results.unsuitableWarningAll")
                : t("results.unsuitableWarningMost")}
            </p>
          </div>
        )}

        <CardContent className="p-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

            {/* Image carousel */}
            <div className="rounded-xl overflow-hidden shadow-md bg-gray-100 max-w-sm mx-auto lg:mx-0">
              {selected.image_urls && selected.image_urls.length > 0 ? (
                <AutoCarousel key={selected.crop} images={selected.image_urls} alt={tc(selected.crop)} />
              ) : (
                <div className="aspect-square">
                  <img
                    src={selected.image_url || `https://via.placeholder.com/400x400?text=${selected.crop}`}
                    alt={tc(selected.crop)}
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
                  {t("results.nutritionTitle")}
                </h3>
                <div className="space-y-1.5 text-sm">
                  {([
                    [t("results.energy"), selected.nutrition.energy_kcal, "kcal"],
                    [t("results.protein"), selected.nutrition.protein_g, "g"],
                    [t("results.carbs"), selected.nutrition.carbs_g, "g"],
                    [t("results.fat"), selected.nutrition.fat_g, "g"],
                    [t("results.fiber"), selected.nutrition.fiber_g, "g"],
                  ] as const).map(([k, v, u]) => (
                    <div key={k} className="flex justify-between">
                      <span className="text-gray-600">{k}:</span>
                      <span className="font-medium text-gray-900">{v} {u}</span>
                    </div>
                  ))}
                  <div className="h-px bg-green-200 my-1.5" />
                  {([
                    [t("results.iron"), selected.nutrition.iron_mg, "mg"],
                    [t("results.calcium"), selected.nutrition.calcium_mg, "mg"],
                    [t("results.water"), selected.nutrition.water_g, "g"],
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
                <h3 className="font-semibold text-gray-900 mb-2">{t("results.aboutCrop", { crop: tc(selected.crop) })}</h3>
                <p className="text-gray-600 text-sm leading-relaxed"
                   dangerouslySetInnerHTML={{
                     __html: isUnsuitableState
                       ? t("results.aboutUnsuitable", { crop: tc(selected.crop), confidence: selected.confidence.toFixed(1) })
                       : t("results.aboutSuitable", { crop: tc(selected.crop), confidence: selected.confidence.toFixed(1) })
                   }}
                />
              </div>

              <div className="flex items-center gap-2 text-sm">
                <Calendar className="w-4 h-4 text-green-600" />
                <span className="font-medium">{t("results.season")}:</span>
                <span className="text-gray-700">{selected.season || t("results.seasonNotSpecified")}</span>
              </div>

              <div className="flex items-center gap-2 text-sm">
                <TrendingUp className="w-4 h-4 text-green-600" />
                <span className="font-medium">{t("results.expectedYield")}:</span>
                <span className="text-gray-700">{selected.expected_yield || t("results.yieldVaries")}</span>
              </div>

              {/* Animated confidence bar */}
              <div className="pt-2">
                <ConfidenceBar value={selected.confidence} />
              </div>

              {/* "Why this crop?" expandable explanation */}
              <WhyThisCrop explanation={selected.explanation} crop={tc(selected.crop)} />
            </div>
          </div>

          {/* Warning alert */}
          {data.warning && (
            <div className="mt-6 bg-amber-50/70 backdrop-blur-sm border border-amber-200/60 rounded-xl p-4 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-amber-800">
                <p className="font-semibold mb-1">{t("results.advisoryNotice")}</p>
                <p>{data.warning}</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* ── Top-3 Ranked List ─────────────────────────────────────── */}
      <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
        <CardHeader className={isUnsuitableState
          ? "bg-gradient-to-r from-amber-50/80 to-orange-50/80"
          : "bg-gradient-to-r from-green-50/80 to-emerald-50/80"
        }>
          <CardTitle className={`text-xl flex items-center gap-2 ${
            isUnsuitableState ? "text-amber-900" : "text-green-900"
          }`}>
            {isUnsuitableState ? (
              <>
                <AlertCircle className="w-6 h-6" />
                {t("results.noSuitable")}
              </>
            ) : (
              <>
                <TrendingUp className="w-6 h-6" />
                {t("results.topRecommended")}
              </>
            )}
          </CardTitle>
          <p className={`text-sm mt-1 ${isUnsuitableState ? "text-amber-700" : "text-green-700"}`}>
            {isUnsuitableState
              ? t("results.rankedByLeast")
              : t("results.clickToView")}
          </p>
        </CardHeader>
        <CardContent className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {top_3.slice(0, 3).map((crop, i) => (
              <button
                key={crop.crop}
                type="button"
                onClick={() => { setSelectedIdx(i); window.scrollTo({ top: 0, behavior: "smooth" }); }}
                className={`group text-left rounded-xl border-2 p-4 transition-all duration-200
                  hover:shadow-lg hover:scale-[1.02]
                  ${i === selectedIdx
                    ? cardSelectedBorder
                    : cardHoverBorder
                  }`}
              >
                {/* Image */}
                <div className="w-full h-32 bg-gray-100 rounded-lg mb-3 overflow-hidden">
                  <img
                    src={crop.image_url || `https://via.placeholder.com/200x150?text=${crop.crop}`}
                    alt={tc(crop.crop)}
                    className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                    onError={e => { (e.target as HTMLImageElement).src = `https://via.placeholder.com/200x150?text=${crop.crop}`; }}
                  />
                </div>

                {/* Rank + advisory */}
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
                  <AdvisoryBadge tier={crop.advisory_tier} />
                </div>

                <h4 className="font-semibold text-lg text-gray-900 mb-2 capitalize">{tc(crop.crop)}</h4>

                {/* Animated confidence bar */}
                <ConfidenceBar value={crop.confidence} size="sm" />

                {/* Consensus */}
                <div className="mt-3 flex items-center gap-2">
                  <ConsensusPill consensus={crop.model_consensus} />
                </div>

                {/* Mini explanation preview */}
                {crop.explanation && (
                  <p className="mt-2 text-xs text-gray-500 line-clamp-2 leading-relaxed">
                    {crop.explanation}
                  </p>
                )}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* ── Safety Disclaimer (V8 Phase 6 — non-removable) ────────── */}
      <div className="bg-blue-50/80 border border-blue-200 rounded-lg p-4 flex items-start gap-3">
        <ShieldAlert className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
        <p className="text-sm text-blue-800 leading-relaxed">
          <strong>{t("results.advisoryNotice")}:</strong> {t("disclaimer")}
        </p>
      </div>

      {/* Try another */}
      <div className="flex justify-center">
        <button
          onClick={() => window.location.reload()}
          className="px-6 py-3 border-2 border-green-600 text-green-700 rounded-lg font-semibold hover:bg-green-50 transition-all duration-200 hover:shadow-md"
        >
          {t("results.tryAnother")}
        </button>
      </div>
    </div>
  );
}
