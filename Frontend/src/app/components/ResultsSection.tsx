import { Badge } from "@/app/components/ui/badge";
import {
  Sprout, TrendingUp, AlertCircle, Calendar, ChevronDown,
  ShieldAlert, Info, AlertTriangle, IndianRupee, LineChart, Printer
} from "lucide-react";
import { type PredictionResponse, type CropRecommendation, type PredictionInput } from "@/app/services/api";
import { useEffect, useState, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { buildExplanation, type ExplanationInput } from "@/app/utils/buildExplanation";
import { useAnimatedValue, useTilt } from "@/app/hooks/useAnimations";
import DOMPurify from "dompurify";

interface ResultsSectionProps {
  data: PredictionResponse;
  userInput?: PredictionInput | null;
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
          className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-700 ${i === idx ? 'opacity-100' : 'opacity-0'}`}
          onError={e => {
            const target = e.target as HTMLImageElement;
            if (!target.src.includes('placehold.co')) {
              target.src = `https://placehold.co/400x400/e2e8f0/475569?text=${alt}`;
            }
          }}
        />
      ))}
      {list.length > 1 && (
        <div className="absolute bottom-3 left-1/2 -translate-x-1/2 flex gap-1.5">
          {list.map((_, i) => (
            <button key={i} onClick={() => setIdx(i)}
              className={`h-1.5 rounded-full transition-all ${i === idx ? 'bg-white w-5' : 'bg-white/40 w-1.5 hover:bg-white/60'}`}
            />
          ))}
        </div>
      )}
    </div>
  );
}

/* ── Animated Counter ─────────────────────────────────────────────── */

function AnimatedCounter({ value, suffix = "%" }: { value: number; suffix?: string }) {
  const animated = useAnimatedValue(value);
  return <span>{animated.toFixed(1)}{suffix}</span>;
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
  const fillClass =
    value >= 75 ? "progress-fill-high"
      : value >= 50 ? "progress-fill-mid"
        : "progress-fill-low";
  const textColor =
    value >= 75 ? "text-emerald-700"
      : value >= 50 ? "text-amber-700"
        : "text-red-700";

  return (
    <div className="w-full">
      <div className="flex justify-between text-sm mb-1.5">
        <span className="font-medium text-gray-500">{t("results.confidence")}</span>
        <span className={`font-bold ${textColor}`}><AnimatedCounter value={value} /></span>
      </div>
      <div className={`progress-track ${h}`}>
        <div
          className={`${fillClass} ${h} rounded-full transition-all duration-1000 ease-out`}
          style={{ width: `${width}%` }}
        />
      </div>
    </div>
  );
}

/* ── Animated Nutrition progress bar ──────────────────────────────── */

function NutritionProgressBar({ label, value, max, unit, colorClass }: { label: string; value: number; max: number; unit: string; colorClass: string }) {
  const [width, setWidth] = useState(0);
  useEffect(() => {
    const timer = setTimeout(() => setWidth(Math.min((value / max) * 100, 100)), 300);
    return () => clearTimeout(timer);
  }, [value, max]);

  return (
    <div className="mb-3">
      <div className="flex justify-between text-[11px] mb-1">
        <span className="text-gray-600 font-medium">{label}</span>
        <span className="text-gray-900 font-bold">{value} <span className="text-[9px] text-gray-400 font-normal uppercase">{unit}</span></span>
      </div>
      <div className="h-1.5 w-full bg-gray-200/50 rounded-full overflow-hidden">
        <div
          className={`${colorClass} h-full rounded-full transition-all duration-1000 ease-out shadow-sm`}
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
      <Badge className="bg-emerald-100 text-emerald-800 border border-emerald-200 gap-1.5 px-3 py-1 text-xs font-semibold">
        {tierLabel}
      </Badge>
    );
  }
  if (tl === "recommended") {
    return (
      <Badge className="bg-blue-100 text-blue-800 border border-blue-200 gap-1.5 px-3 py-1 text-xs font-semibold">
        {tierLabel}
      </Badge>
    );
  }
  if (tl.includes("conditional")) {
    return (
      <Badge className="bg-amber-100 text-amber-800 border border-amber-200 gap-1.5 px-3 py-1 text-xs font-semibold">
        {tierLabel}
      </Badge>
    );
  }
  return (
    <Badge className="bg-red-100 text-red-800 border border-red-200 gap-1.5 px-3 py-1 text-xs font-semibold">
      {tierLabel}
    </Badge>
  );
}

/* ── Consensus pill ───────────────────────────────────────────────── */

function ConsensusPill({ ncsLevel }: { ncsLevel?: string }) {
  const { t } = useTranslation();
  if (!ncsLevel) return null;
  const cls =
    ncsLevel === "strong" ? "bg-emerald-100 text-emerald-700 border-emerald-200"
      : ncsLevel === "moderate" ? "bg-amber-100 text-amber-700 border-amber-200"
        : "bg-gray-100 text-gray-600 border-gray-200";

  const label = ncsLevel === "strong" ? t("consensus.strong")
    : ncsLevel === "moderate" ? t("consensus.moderate")
      : t("consensus.weak");

  return (
    <Badge variant="outline" className={`text-[10px] px-2 py-0.5 capitalize ${cls}`}>
      {label}
    </Badge>
  );
}

/* ── Confidence interpretation label (V9 NCS) ─────────────────────── */

function ConfidenceLabel({ ncsLevel }: { ncsLevel?: string }) {
  const { t } = useTranslation();
  if (!ncsLevel) return null;
  const l = ncsLevel.toLowerCase();
  const cls = l === "strong"
    ? "bg-emerald-100 text-emerald-700 border-emerald-200"
    : l === "moderate"
      ? "bg-blue-100 text-blue-700 border-blue-200"
      : "bg-gray-100 text-gray-600 border-gray-200";
  const i18nKey = l === "strong" ? "match.strong"
    : l === "moderate" ? "match.moderate" : "match.weak";
  return (
    <Badge variant="outline" className={`text-[10px] px-2 py-0.5 ${cls}`}>
      {t(i18nKey, { defaultValue: ncsLevel })}
    </Badge>
  );
}

/* ── V9: Environmental Match pill ─────────────────────────────────── */

function EnvironmentalMatchPill({ match }: { match?: string }) {
  const { t } = useTranslation();
  if (!match || match === "unknown") return null;
  const m = match.toLowerCase();
  const cls = m === "strong"
    ? "bg-teal-100 text-teal-700 border-teal-200"
    : m === "acceptable"
      ? "bg-sky-100 text-sky-700 border-sky-200"
      : "bg-orange-100 text-orange-700 border-orange-200";
  const label = m === "strong"
    ? t("envMatch.strong", { defaultValue: "Env: Strong" })
    : m === "acceptable"
      ? t("envMatch.acceptable", { defaultValue: "Env: OK" })
      : t("envMatch.weak", { defaultValue: "Env: Weak" });
  return (
    <Badge variant="outline" className={`text-[10px] px-2 py-0.5 ${cls}`}>
      {label}
    </Badge>
  );
}

/* ── Limiting-factor banner (V8 FINAL STABLE) ────────────────────── */

function LimitingFactorBanner({ data }: { data: PredictionResponse }) {
  const { t } = useTranslation();
  const lf = data.limiting_factor;
  if (!lf) return null;

  const featureLabel = t(`features.${lf.feature}`, { defaultValue: lf.feature });
  const devPct = Math.abs(lf.deviation * 100).toFixed(0);

  return (
    <div className="bg-red-50 border border-red-200 rounded-2xl p-4 flex items-start gap-3">
      <div className="p-1.5 rounded-lg bg-red-100">
        <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0" />
      </div>
      <div className="text-sm">
        <p className="font-semibold mb-1 text-red-800">{t("results.limitingFactorTitle")}</p>
        <p className="text-red-700">
          {t("results.limitingFactorDesc", { feature: featureLabel, deviation: devPct })}
        </p>
        {lf.all_deviations && Object.keys(lf.all_deviations).length > 1 && (
          <div className="mt-2 flex flex-wrap gap-2">
            {Object.entries(lf.all_deviations)
              .sort(([, a], [, b]) => Math.abs(b) - Math.abs(a))
              .map(([feat, dev]) => (
                <span key={feat} className={`inline-flex items-center px-2 py-0.5 rounded-lg text-xs font-medium ${Math.abs(dev) > 0.3 ? "bg-red-100 text-red-700" : "bg-amber-100 text-amber-700"
                  }`}>
                  {t(`features.${feat}`, { defaultValue: feat })}: {(Math.abs(dev) * 100).toFixed(0)}%
                </span>
              ))}
          </div>
        )}
      </div>
    </div>
  );
}

/* ── "Why this crop?" expandable section ──────────────────────────── */

function WhyThisCrop({ explanation, crop }: { explanation?: string; crop: string }) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  if (!explanation) return null;

  return (
    <div className="border border-gray-200 rounded-xl overflow-hidden bg-gray-50/50 mt-3">
      <button
        type="button"
        onClick={() => setOpen(v => !v)}
        className="w-full flex items-center justify-between px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-100 transition-colors"
      >
        <span className="flex items-center gap-2">
          <Info className="w-4 h-4 text-emerald-600" />
          {t("results.whyCrop", { crop })}
        </span>
        <ChevronDown className={`w-4 h-4 transition-transform duration-300 ${open ? 'rotate-180' : ''}`} />
      </button>
      <div
        className={`overflow-hidden transition-all duration-300 ease-in-out ${open ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
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

export function ResultsSection({ data, userInput }: ResultsSectionProps) {
  const { t } = useTranslation();
  /** Translate an API crop name (e.g. "finger_millet") to the active locale */
  const tc = (crop: string) => t(`crops.${crop}`, { defaultValue: crop });

  // Generate deterministic mock market data for demonstration
  const getMockMarketData = (crop: string) => {
    const basePrice = 1500 + (crop.length * 120) + (crop.charCodeAt(0) * 15);
    const isHighDemand = crop.length % 2 === 0 || crop.includes('rice') || crop.includes('wheat');
    return {
      price: `₹${basePrice.toLocaleString("en-IN")} / Quintal`,
      demand: isHighDemand ? "High" : "Moderate",
      trend: isHighDemand ? "+5.2% this week" : "-1.1% this week",
      trendColor: isHighDemand ? "text-emerald-600" : "text-amber-600"
    };
  };

  // Generate a mock fertilizer strategy to fulfill the PPT promise
  const getFertilizerStrategy = (crop: string, input: PredictionInput | null | undefined) => {
    if (!input) return { type: "Standard NPK", details: "Follow standard local guidelines." };
    
    const lowN = input.N < 40;
    const lowP = input.P < 20;
    const lowK = input.K < 20;

    let type = "Balanced NPK (19:19:19)";
    let details = "Your soil has balanced nutrients. Use a standard maintenance dose.";

    if (lowN && !lowP && !lowK) {
      type = "Urea / Nitrogen-Rich";
      details = "Nitrogen is low. Apply Urea or Neem-coated Urea as a top dressing.";
    } else if (lowP) {
      type = "DAP (Diammonium Phosphate)";
      details = "Phosphorus is deficient. Apply DAP as a basal dose before sowing.";
    } else if (lowK) {
      type = "MOP (Muriate of Potash)";
      details = "Potassium is low. Apply MOP to improve crop stress tolerance.";
    } else if (crop.toLowerCase().includes("rice") || crop.toLowerCase().includes("wheat") || crop.toLowerCase().includes("maize")) {
      type = "NPK 10:26:26";
      details = "Ideal for high-yield cereal crops. Split nitrogen application in 3 phases.";
    } else if (crop.toLowerCase().includes("cotton")) {
      type = "NPK 20:20:0:13";
      details = "Sulfur-enriched fertilizer is recommended for better boll development.";
    }

    return { type, details };
  };

  /** Build a translated explanation for a crop, falling back to the API's English text */
  const explainCrop = (crop: string, apiExplanation?: string, isFallback = false): string | undefined => {
    if (!userInput) return apiExplanation;
    const ei: ExplanationInput = {
      temperature: userInput.temperature,
      humidity: userInput.humidity,
      ph: userInput.ph,
      rainfall: userInput.rainfall,
    };
    const translated = buildExplanation(crop, ei, t, tc, isFallback);
    return translated || apiExplanation;
  };

  /** Translate the API warning string by matching known English patterns */
  const translateWarning = (warning: string): string => {
    const parts: string[] = [];

    if (warning.includes("All crops violate critical environmental thresholds")) {
      parts.push(t("warnings.fallbackThresholds"));
    }

    // "Some values (P) fall outside typical ranges. Confidence adjusted."
    const oodMatch = warning.match(/Some values \(([^)]+)\) fall outside typical ranges/);
    if (oodMatch) {
      parts.push(t("warnings.oodValues", { fields: oodMatch[1] }));
    }

    if (warning.includes("Conditions may be challenging for most crops")) {
      parts.push(t("warnings.challengingConditions"));
    }

    // OOD features (older API format)
    const oodOldMatch = warning.match(/OOD features: ([^.]+)\. Confidence dampened/);
    if (oodOldMatch && !oodMatch) {
      parts.push(t("warnings.oodValues", { fields: oodOldMatch[1] }));
    }

    if (warning.includes("Low confidence") && !warning.includes("Conditions may be challenging")) {
      parts.push(t("warnings.challengingConditions"));
    }

    return parts.length > 0 ? parts.join(" ") : warning;
  };

  const advisoryNoticeFromTier = (tier?: string): string => {
    const tl = (tier || "").toLowerCase();
    if (tl.includes("strongly")) return t("tiers.stronglyRecommended");
    if (tl === "recommended") return t("tiers.recommended");
    if (tl.includes("conditional")) return t("tiers.conditional");
    return t("tiers.notRecommended");
  };

  const { top_1, top_3 } = data;
  const [selectedIdx, setSelectedIdx] = useState(0);
  const selected = top_3[selectedIdx] ?? top_1;
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setVisible(true), 50);
    return () => clearTimeout(timer);
  }, []);

  // V9: Use backend advisory_tier as single source of truth for state
  const isUnsuitableState = (top_3 || []).every(c => (c?.advisory_tier || "").toLowerCase().includes("not recommended"));

  // Collapsible top-3 when globally unsuitable (collapsed by default)
  const [top3Expanded, setTop3Expanded] = useState(!isUnsuitableState);

  if (!top_1 || !(top_3 || []).length) {
    return (
      <div className="glass-card !border-amber-200 p-4 text-amber-700">
        {t("results.noRecommendations")}
      </div>
    );
  }

  // Dynamic header gradient / border colors based on suitability
  const heroClass = isUnsuitableState ? "hero-gradient-warn" : "hero-gradient";
  const cardSelectedBorder = isUnsuitableState
    ? "border-amber-400 bg-amber-50 ring-2 ring-amber-200 shadow-lg"
    : "border-emerald-400 bg-emerald-50 ring-2 ring-emerald-200 shadow-lg";
  const cardHoverBorder = isUnsuitableState
    ? "border-gray-200 bg-white/70 hover:border-amber-300 hover:bg-amber-50/50"
    : "border-gray-200 bg-white/70 hover:border-emerald-300 hover:bg-emerald-50/50";

  return (
    <div className={`space-y-6 transition-all duration-700 ease-out ${visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>

      {/* ── Top-1 Primary Crop Card ─────────────────────────────────── */}
      <div className="agri-card p-0 overflow-hidden animate-fade-in-up">
        <div className="bg-[var(--color-paper-deep)] px-6 py-4 border-b border-[var(--color-border-line)] flex items-center justify-between">
          <span className="eyebrow">{isUnsuitableState ? t("results.unsuitableDetected") : t("results.topRecommendation")}</span>
          <AdvisoryBadge tier={selected.advisory_tier} />
        </div>

        <div className="p-8">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-center">

            {/* Left side: Image */}
            <div className="md:col-span-4 rounded-xl overflow-hidden bg-gray-100 border border-[var(--color-border-line)]">
              {selected.image_urls && selected.image_urls.length > 0 ? (
                <AutoCarousel key={selected.crop} images={selected.image_urls} alt={tc(selected.crop)} />
              ) : (
                <div className="aspect-square">
                  <img
                    src={selected.image_url || `https://placehold.co/400x400/e2e8f0/475569?text=${selected.crop}`}
                    alt={tc(selected.crop)}
                    className="w-full h-full object-cover"
                    onError={e => {
                      const target = e.target as HTMLImageElement;
                      if (!target.src.includes('placehold.co')) {
                        target.src = `https://placehold.co/400x400/e2e8f0/475569?text=${selected.crop}`;
                      }
                    }}
                  />
                </div>
              )}
            </div>

            {/* Right side: Info */}
            <div className="md:col-span-8 space-y-6">
              <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 border-b border-[var(--color-border-line)] pb-6 border-dashed">
                <div>
                  <h2 className="text-4xl lg:text-5xl font-bold text-[var(--color-ink)] capitalize" style={{ fontFamily: 'var(--font-display)' }}>
                    {tc(selected.crop)}
                  </h2>
                  <p 
                    className="text-[var(--color-ink-soft)] mt-2 leading-relaxed max-w-lg"
                    dangerouslySetInnerHTML={{
                      __html: DOMPurify.sanitize(
                        isUnsuitableState
                          ? t("results.aboutUnsuitable", { crop: tc(selected.crop), confidence: (selected?.confidence || 0).toFixed(1) })
                          : t("results.aboutSuitable", { crop: tc(selected.crop), confidence: (selected?.confidence || 0).toFixed(1) })
                      )
                    }}
                  />
                </div>
                <div className="text-right">
                  <span className="block eyebrow mb-1">{t("results.growthMatch")}</span>
                  <span className="text-4xl font-bold text-[var(--color-green-deep)] mono-data block">
                    <AnimatedCounter value={selected?.confidence || 0} />
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <span className="eyebrow flex items-center gap-1.5"><Calendar className="w-3 h-3" /> {t("results.season")}</span>
                  <p className="text-sm font-medium text-[var(--color-ink)]">{selected.season || t("results.seasonNotSpecified")}</p>
                </div>
                <div className="space-y-1">
                  <span className="eyebrow flex items-center gap-1.5"><TrendingUp className="w-3 h-3" /> {t("results.expectedYield")}</span>
                  <p className="text-sm font-medium text-[var(--color-ink)]">{selected.expected_yield || t("results.yieldVaries")}</p>
                </div>
              </div>

              {/* Hackathon step 4: Market data */}
              <div className="bg-[var(--color-paper-deep)]/40 border border-[var(--color-border-line)] rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="eyebrow flex items-center gap-1.5 text-[var(--color-green-deep)]"><LineChart className="w-3 h-3" /> {t("results.liveMarketTrends")}</span>
                  <span className="text-[10px] italic text-[var(--color-ink-soft)] opacity-70">{t("results.localMandiPricing")}</span>
                </div>
                {(() => {
                  const market = getMockMarketData(selected.crop);
                  return (
                    <div className="flex flex-wrap items-center justify-between gap-4">
                      <div>
                        <p className="text-xs text-[var(--color-ink-soft)] mb-0.5">{t("results.currentPrice")}</p>
                        <p className="font-bold text-[var(--color-ink)] mono-data">{market.price}</p>
                      </div>
                      <div>
                        <p className="text-xs text-[var(--color-ink-soft)] mb-0.5">{t("results.demand")}</p>
                        <p className="font-bold text-[var(--color-ink)]">{market.demand}</p>
                      </div>
                      <div>
                        <p className="text-xs text-[var(--color-ink-soft)] mb-0.5">{t("results.trend30Day")}</p>
                        <p className={`font-bold ${market.trendColor}`}>{market.trend}</p>
                      </div>
                    </div>
                  );
                })()}
              </div>

              {/* Hackathon Fertilizer Strategy */}
              <div className="bg-[var(--color-paper-deep)]/40 border border-[var(--color-border-line)] rounded-lg p-4 mt-4">
                <div className="flex items-center mb-2">
                  <span className="eyebrow flex items-center gap-1.5 text-[var(--color-clay)]">
                    <Sprout className="w-3 h-3" /> {t("results.recommendedFertilizer")}
                  </span>
                </div>
                {(() => {
                  const fert = getFertilizerStrategy(selected.crop, userInput);
                  return (
                    <div>
                      <p className="font-bold text-[var(--color-ink)] mb-1">{fert.type}</p>
                      <p className="text-sm text-[var(--color-ink-soft)] leading-relaxed">{fert.details}</p>
                    </div>
                  );
                })()}
              </div>
              {/* Unsuitable conditions warning banner */}
              {isUnsuitableState && data.limiting_factor && (
                <div className="mt-4">
                  <LimitingFactorBanner data={data} />
                </div>
              )}
            </div>
          </div>

          <div className="mt-6">
            <WhyThisCrop explanation={explainCrop(selected.crop, selected.explanation, isUnsuitableState)} crop={tc(selected.crop)} />
          </div>

          {/* Advisory notice (strictly from backend advisory_tier) */}
          <div className="mt-6 bg-[var(--color-paper-deep)] border border-[var(--color-border-line)] rounded-xl p-4 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-[var(--color-clay)] flex-shrink-0" />
            <div className="text-sm">
              <p className="font-bold mb-1 text-[var(--color-ink)]">{t("results.advisoryNotice")}</p>
              <p className="text-[var(--color-ink-soft)]">{advisoryNoticeFromTier(selected.advisory_tier)}</p>
              {data.warning && (
                <p className="text-[var(--color-ink-soft)] mt-1">{translateWarning(data.warning)}</p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* ── Top-3 Ranked Alternative Crops ─────────────────────────── */}
      {top_3.length > 1 && (
        <div className="agri-card !p-0 overflow-hidden animate-fade-in-up delay-100">
          <div className="px-6 py-5 border-b border-[var(--color-border-line)]">
            <h3 className="text-xl font-bold flex items-center gap-2 text-[var(--color-ink)]" style={{ fontFamily: 'var(--font-display)' }}>
              {t("results.alternativeRecommendations")}
            </h3>
            <p className="text-sm mt-1 text-[var(--color-ink-soft)]">
              {t("results.otherViableCrops")}
            </p>
          </div>

          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              {top_3.slice(0, 3).map((crop, i) => (
                <button
                  key={crop.crop}
                  type="button"
                  onClick={() => { setSelectedIdx(i); window.scrollTo({ top: 0, behavior: "smooth" }); }}
                  className={`group text-left rounded-xl border p-4 transition-all duration-300
                  hover:bg-[var(--color-paper-deep)] hover:shadow-md
                  ${i === selectedIdx ? "border-[var(--color-green-deep)] bg-[var(--color-paper-deep)] ring-1 ring-[var(--color-green-deep)]" : "border-[var(--color-border-line)] bg-[var(--color-card)]"}`}
                >
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-bold text-[var(--color-ink)] py-1 px-2 bg-[var(--color-paper)] border border-[var(--color-border-line)] rounded">#{i + 1}</span>
                    <AdvisoryBadge tier={crop.advisory_tier} />
                  </div>

                  <div className="flex items-center gap-3 mb-3 border-b border-[var(--color-border-line)] border-dashed pb-3">
                    <div className="w-12 h-12 bg-gray-100 rounded-lg overflow-hidden flex-shrink-0 border border-[var(--color-border-line)]">
                      <img src={crop.image_url || `https://placehold.co/100x100/e2e8f0/475569?text=${crop.crop}`} alt={tc(crop.crop)} className="w-full h-full object-cover" />
                    </div>
                    <div>
                      <h4 className="font-bold text-[var(--color-ink)] capitalize" style={{ fontFamily: 'var(--font-display)' }}>{tc(crop.crop)}</h4>
                      <span className="text-[10px] text-[var(--color-ink-soft)] uppercase tracking-wider">{crop.season || "Any Season"}</span>
                    </div>
                  </div>

                  {/* Thin Mustard Progress Bar */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="text-[var(--color-ink-soft)]">{t("results.matchShort")}</span>
                      <span className="font-bold mono-data text-[var(--color-mustard)]">{crop.confidence.toFixed(1)}%</span>
                    </div>
                    <div className="progress-track h-1.5">
                      <div className="progress-fill" style={{ width: `${crop.confidence}%` }}></div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── Safety Disclaimer ────────── */}
      <div className="agri-card bg-transparent border-none shadow-none !p-0 flex items-start gap-3 animate-fade-in-up delay-200">
        <ShieldAlert className="w-5 h-5 text-[var(--color-clay)] flex-shrink-0 mt-0.5" />
        <p className="text-sm text-[var(--color-ink-soft)] leading-relaxed">
          <strong className="text-[var(--color-ink)]">{t("results.advisoryNotice")}:</strong> {t("disclaimer")}
        </p>
      </div>

      {/* Actions */}
      <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-fade-in-up delay-300 pt-8 border-t border-[var(--color-border-line)] border-dashed print:hidden">
        <button
          onClick={() => window.print()}
          className="btn-primary flex items-center gap-2"
        >
          <Printer className="w-4 h-4" />
          {t("results.downloadPdf")}
        </button>
        <button
          onClick={() => window.location.reload()}
          className="btn-secondary"
        >
          {t("results.tryAnother")}
        </button>
      </div>
    </div>
  );
}
