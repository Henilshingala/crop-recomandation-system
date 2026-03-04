import { Badge } from "@/app/components/ui/badge";
import {
  Sprout, TrendingUp, AlertCircle, Calendar, ChevronDown,
  ShieldAlert, Info, AlertTriangle,
} from "lucide-react";
import { type PredictionResponse, type CropRecommendation, type PredictionInput } from "@/app/services/api";
import { useEffect, useState, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { buildExplanation, type ExplanationInput } from "@/app/utils/buildExplanation";
import { useAnimatedValue, useTilt } from "@/app/hooks/useAnimations";

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
          onError={e => { (e.target as HTMLImageElement).src = `https://via.placeholder.com/400x400?text=${alt}`; }}
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
    value >= 75 ? "text-emerald-400"
    : value >= 50 ? "text-amber-400"
    : "text-red-400";

  return (
    <div className="w-full">
      <div className="flex justify-between text-sm mb-1.5">
        <span className="font-medium text-gray-400">{t("results.confidence")}</span>
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
      <Badge className="bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 gap-1.5 px-3 py-1 text-xs font-semibold">
        {tierLabel}
      </Badge>
    );
  }
  if (tl === "recommended") {
    return (
      <Badge className="bg-blue-500/15 text-blue-300 border border-blue-500/30 gap-1.5 px-3 py-1 text-xs font-semibold">
        {tierLabel}
      </Badge>
    );
  }
  if (tl.includes("conditional")) {
    return (
      <Badge className="bg-amber-500/15 text-amber-300 border border-amber-500/30 gap-1.5 px-3 py-1 text-xs font-semibold">
        {tierLabel}
      </Badge>
    );
  }
  return (
    <Badge className="bg-red-500/15 text-red-300 border border-red-500/30 gap-1.5 px-3 py-1 text-xs font-semibold">
      {tierLabel}
    </Badge>
  );
}

/* ── Consensus pill ───────────────────────────────────────────────── */

function ConsensusPill({ consensus }: { consensus?: string }) {
  const { t } = useTranslation();
  if (!consensus) return null;
  const cls =
    consensus === "strong" ? "bg-emerald-500/15 text-emerald-300 border-emerald-500/25"
    : consensus === "moderate" ? "bg-amber-500/15 text-amber-300 border-amber-500/25"
    : "bg-white/[0.06] text-gray-400 border-white/10";

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
    stressIndex < 0.2 ? "bg-emerald-500/15 text-emerald-300 border-emerald-500/30"
    : stressIndex < 0.4 ? "bg-amber-500/15 text-amber-300 border-amber-500/30"
    : stressIndex < 0.6 ? "bg-orange-500/15 text-orange-300 border-orange-500/30"
    : "bg-red-500/15 text-red-300 border-red-500/30";

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
        <div className="absolute z-20 bottom-full left-1/2 -translate-x-1/2 mb-2 w-56 bg-gray-900/95 backdrop-blur-xl text-white text-xs rounded-xl p-3 shadow-2xl border border-white/10 pointer-events-none">
          <p className="font-medium mb-1">{t("stress.indexLabel", { value: (stressIndex * 100).toFixed(0) })}</p>
          <p className="text-gray-300 leading-relaxed">
            {t("stress.description")}
          </p>
          <div className="tooltip-arrow" />
        </div>
      )}
    </div>
  );
}

/* ── Confidence interpretation label (V8 FINAL STABLE) ────────────── */

function ConfidenceLabel({ label }: { label?: string }) {
  const { t } = useTranslation();
  if (!label) return null;
  const l = label.toLowerCase();
  const cls = l.includes("strong")
    ? "bg-emerald-500/15 text-emerald-300 border-emerald-500/30"
    : l.includes("moderate")
    ? "bg-blue-500/15 text-blue-300 border-blue-500/30"
    : "bg-white/[0.06] text-gray-400 border-white/10";
  const i18nKey = l.includes("strong") ? "match.strong"
    : l.includes("moderate") ? "match.moderate" : "match.weak";
  return (
    <Badge variant="outline" className={`text-[10px] px-2 py-0.5 ${cls}`}>
      {t(i18nKey, { defaultValue: label })}
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
    <div className="bg-red-500/10 border border-red-500/20 rounded-2xl p-4 flex items-start gap-3">
      <div className="p-1.5 rounded-lg bg-red-500/15">
        <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0" />
      </div>
      <div className="text-sm">
        <p className="font-semibold mb-1 text-red-300">{t("results.limitingFactorTitle")}</p>
        <p className="text-red-200/80">
          {t("results.limitingFactorDesc", { feature: featureLabel, deviation: devPct })}
        </p>
        {lf.all_deviations && Object.keys(lf.all_deviations).length > 1 && (
          <div className="mt-2 flex flex-wrap gap-2">
            {Object.entries(lf.all_deviations)
              .sort(([, a], [, b]) => Math.abs(b) - Math.abs(a))
              .map(([feat, dev]) => (
                <span key={feat} className={`inline-flex items-center px-2 py-0.5 rounded-lg text-xs font-medium ${
                  Math.abs(dev) > 0.3 ? "bg-red-500/15 text-red-300" : "bg-amber-500/15 text-amber-300"
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
    <div className="border border-white/[0.08] rounded-xl overflow-hidden bg-white/[0.03] mt-3">
      <button
        type="button"
        onClick={() => setOpen(v => !v)}
        className="w-full flex items-center justify-between px-4 py-2.5 text-sm font-medium text-gray-300 hover:bg-white/[0.05] transition-colors"
      >
        <span className="flex items-center gap-2">
          <Info className="w-4 h-4 text-emerald-400" />
          {t("results.whyCrop", { crop })}
        </span>
        <ChevronDown className={`w-4 h-4 transition-transform duration-300 ${open ? 'rotate-180' : ''}`} />
      </button>
      <div
        className={`overflow-hidden transition-all duration-300 ease-in-out ${
          open ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
        }`}
      >
        <div className="px-4 pb-3 text-sm text-gray-400 leading-relaxed border-t border-white/[0.08] pt-3">
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

    // "High agricultural stress detected (index=0.XX)."
    const stressMatch = warning.match(/High agricultural stress detected \(index=([\d.]+)\)/);
    if (stressMatch) {
      parts.push(t("warnings.highStress", { index: stressMatch[1] }));
    }
    // Also match the older format "High agricultural stress (index=0.XX). Confidence reduced."
    const stressOldMatch = warning.match(/High agricultural stress \(index=([\d.]+)\)/);
    if (stressOldMatch && !stressMatch) {
      parts.push(t("warnings.highStress", { index: stressOldMatch[1] }));
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

  const { top_1, top_3 } = data;
  const [selectedIdx, setSelectedIdx] = useState(0);
  const selected = top_3[selectedIdx] ?? top_1;
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setVisible(true), 50);
    return () => clearTimeout(timer);
  }, []);

  // V8 FINAL STABLE: Detect all-not-recommended / fallback / global-unsuitable
  const allNotRecommended = data.all_not_recommended
    ?? top_3.every(c => c.advisory_tier?.toLowerCase().includes("not recommended"));
  const fallbackMode = data.fallback_mode ?? false;
  const globalUnsuitable = data.global_unsuitable ?? false;
  const isUnsuitableState = globalUnsuitable || allNotRecommended || fallbackMode;

  // Collapsible top-3 when globally unsuitable (collapsed by default)
  const [top3Expanded, setTop3Expanded] = useState(!isUnsuitableState);

  if (!top_1 || !top_3?.length) {
    return (
      <div className="glass-card !border-amber-500/20 p-4 text-amber-300">
        {t("results.noRecommendations")}
      </div>
    );
  }

  // Dynamic header gradient / border colors based on suitability
  const heroClass = isUnsuitableState ? "hero-gradient-warn" : "hero-gradient";
  const cardSelectedBorder = isUnsuitableState
    ? "border-amber-500/40 bg-amber-500/10 ring-2 ring-amber-500/20 shadow-lg shadow-amber-500/5"
    : "border-emerald-500/40 bg-emerald-500/10 ring-2 ring-emerald-500/20 shadow-lg shadow-emerald-500/5";
  const cardHoverBorder = isUnsuitableState
    ? "border-white/[0.08] bg-white/[0.04] hover:border-amber-500/25 hover:bg-amber-500/5"
    : "border-white/[0.08] bg-white/[0.04] hover:border-emerald-500/25 hover:bg-emerald-500/5";

  return (
    <div className={`space-y-6 transition-all duration-700 ease-out ${visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>

      {/* ── Top-1 Hero Card ────────────────────────────────────────── */}
      <div className="glass-card !p-0 overflow-hidden animate-fade-in-up">
        {/* Header gradient */}
        <div className={`${heroClass} text-white px-6 py-8`}>
          <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
            <div className="flex items-center gap-3">
              {isUnsuitableState ? (
                <div className="p-2 rounded-xl bg-white/10 backdrop-blur">
                  <AlertCircle className="w-7 h-7" />
                </div>
              ) : (
                <div className="p-2 rounded-xl bg-white/10 backdrop-blur">
                  <Sprout className="w-7 h-7" />
                </div>
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
            <Badge className="bg-white/15 backdrop-blur text-white text-sm font-semibold px-3 py-1 border border-white/20">
              {t("results.match", { value: selected.confidence.toFixed(1) })}
            </Badge>
            <ConsensusPill consensus={selected.model_consensus} />
            <ConfidenceLabel label={selected.confidence_label} />
          </div>
        </div>

        {/* V8.1: Unsuitable conditions warning banner */}
        {isUnsuitableState && (
          <div className="bg-amber-900/30 border-t border-amber-400/40 px-6 py-3">
            <p className="text-amber-100 text-sm leading-relaxed">
              {globalUnsuitable
                ? t("results.globalUnsuitableBanner")
                : fallbackMode
                ? t("results.unsuitableWarningAll")
                : t("results.unsuitableWarningMost")}
            </p>
          </div>
        )}

        <div className="p-6">
          {/* V8 FINAL STABLE: Limiting factor banner */}
          {isUnsuitableState && data.limiting_factor && (
            <div className="mb-6">
              <LimitingFactorBanner data={data} />
            </div>
          )}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

            {/* Image carousel */}
            <div className="rounded-xl overflow-hidden bg-white/[0.04] border border-white/[0.06] max-w-sm mx-auto lg:mx-0">
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
              <div className="bg-emerald-500/[0.06] backdrop-blur-sm rounded-xl p-4 border border-emerald-500/15">
                <h3 className="font-semibold text-white mb-3 flex items-center gap-2">
                  <svg className="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
                      <span className="text-gray-400">{k}:</span>
                      <span className="font-medium text-white">{v} {u}</span>
                    </div>
                  ))}
                  <div className="h-px bg-emerald-500/15 my-1.5" />
                  {([
                    [t("results.iron"), selected.nutrition.iron_mg, "mg"],
                    [t("results.calcium"), selected.nutrition.calcium_mg, "mg"],
                    [t("results.water"), selected.nutrition.water_g, "g"],
                  ] as const).map(([k, v, u]) => (
                    <div key={k} className="flex justify-between">
                      <span className="text-gray-400">{k}:</span>
                      <span className="font-medium text-white">{v} {u}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Details column */}
            <div className="space-y-4">
              <div>
                <h3 className="font-semibold text-white mb-2">{t("results.aboutCrop", { crop: tc(selected.crop) })}</h3>
                <p className="text-gray-400 text-sm leading-relaxed"
                   dangerouslySetInnerHTML={{
                     __html: isUnsuitableState
                       ? t("results.aboutUnsuitable", { crop: tc(selected.crop), confidence: selected.confidence.toFixed(1) })
                       : t("results.aboutSuitable", { crop: tc(selected.crop), confidence: selected.confidence.toFixed(1) })
                   }}
                />
              </div>

              <div className="flex items-center gap-2 text-sm">
                <Calendar className="w-4 h-4 text-emerald-400" />
                <span className="font-medium text-gray-300">{t("results.season")}:</span>
                <span className="text-gray-400">{selected.season || t("results.seasonNotSpecified")}</span>
              </div>

              <div className="flex items-center gap-2 text-sm">
                <TrendingUp className="w-4 h-4 text-emerald-400" />
                <span className="font-medium text-gray-300">{t("results.expectedYield")}:</span>
                <span className="text-gray-400">{selected.expected_yield || t("results.yieldVaries")}</span>
              </div>

              {/* Animated confidence bar */}
              <div className="pt-2">
                <ConfidenceBar value={selected.confidence} />
              </div>

              {/* "Why this crop?" expandable explanation */}
              <WhyThisCrop explanation={explainCrop(selected.crop, selected.explanation, isUnsuitableState)} crop={tc(selected.crop)} />
            </div>
          </div>

          {/* Warning alert */}
          {data.warning && (
            <div className="mt-6 bg-amber-500/10 border border-amber-500/20 rounded-xl p-4 flex items-start gap-3">
              <div className="p-1.5 rounded-lg bg-amber-500/15">
                <AlertCircle className="w-5 h-5 text-amber-400 flex-shrink-0" />
              </div>
              <div className="text-sm">
                <p className="font-semibold mb-1 text-amber-300">{t("results.advisoryNotice")}</p>
                <p className="text-amber-200/80">{translateWarning(data.warning)}</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── Top-3 Ranked List ─────────────────────────────────────── */}
      <div className="glass-card !p-0 overflow-hidden animate-fade-in-up delay-100">
        <div
          className={`px-6 py-5 border-b border-white/[0.06] ${isUnsuitableState ? "cursor-pointer hover:bg-white/[0.02]" : ""}`}
          {...(isUnsuitableState ? { onClick: () => setTop3Expanded(v => !v) } : {})}
        >
          <h3 className={`text-xl font-bold flex items-center gap-2 ${
            isUnsuitableState ? "text-amber-300" : "text-emerald-300"
          }`}>
            {isUnsuitableState ? (
              <>
                <AlertCircle className="w-6 h-6" />
                {t("results.noSuitable")}
                <ChevronDown className={`w-5 h-5 ml-auto transition-transform duration-300 ${top3Expanded ? "rotate-180" : ""}`} />
              </>
            ) : (
              <>
                <TrendingUp className="w-6 h-6" />
                {t("results.topRecommended")}
              </>
            )}
          </h3>
          <p className={`text-sm mt-1 ${isUnsuitableState ? "text-amber-400/70" : "text-emerald-400/70"}`}>
            {isUnsuitableState
              ? t("results.rankedByLeast")
              : t("results.clickToView")}
          </p>
        </div>
        <div className={`overflow-hidden transition-all duration-300 ease-in-out ${
          top3Expanded ? "max-h-[2000px] opacity-100" : "max-h-0 opacity-0"
        }`}>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {top_3.slice(0, 3).map((crop, i) => (
              <button
                key={crop.crop}
                type="button"
                onClick={() => { setSelectedIdx(i); window.scrollTo({ top: 0, behavior: "smooth" }); }}
                className={`group text-left rounded-2xl border-2 p-4 transition-all duration-300
                  hover:shadow-lg hover:shadow-emerald-500/5 hover:scale-[1.02]
                  animate-fade-in-up ${i === 1 ? "delay-100" : i === 2 ? "delay-200" : ""}
                  ${i === selectedIdx
                    ? cardSelectedBorder
                    : cardHoverBorder
                  }`}
              >
                {/* Image */}
                <div className="w-full h-32 bg-white/[0.04] rounded-xl mb-3 overflow-hidden border border-white/[0.06]">
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
                      i === 0 ? "border-yellow-500/40 text-yellow-300 bg-yellow-500/10"
                      : i === 1 ? "border-gray-500/30 text-gray-400 bg-white/[0.05]"
                      : "border-orange-500/40 text-orange-300 bg-orange-500/10"
                    }
                  >
                    #{i + 1}
                  </Badge>
                  <AdvisoryBadge tier={crop.advisory_tier} />
                </div>

                <h4 className="font-semibold text-lg text-white mb-2 capitalize">{tc(crop.crop)}</h4>

                {/* Animated confidence bar */}
                <ConfidenceBar value={crop.confidence} size="sm" />

                {/* Consensus + confidence label */}
                <div className="mt-3 flex items-center gap-2 flex-wrap">
                  <ConsensusPill consensus={crop.model_consensus} />
                  <ConfidenceLabel label={crop.confidence_label} />
                </div>

                {/* Mini explanation preview */}
                {(crop.explanation || userInput) && (
                  <p className="mt-2 text-xs text-gray-500 line-clamp-2 leading-relaxed">
                    {explainCrop(crop.crop, crop.explanation, isUnsuitableState)}
                  </p>
                )}
              </button>
            ))}
          </div>
          {/* Fewer than 3 crops note */}
          {top_3.length < 3 && (
            <p className="mt-4 text-xs text-gray-500 italic text-center">
              {t("results.fewerThanThree", { count: top_3.length })}
            </p>
          )}
        </div>
        </div>
      </div>

      {/* ── Safety Disclaimer (V8 Phase 6 — non-removable) ────────── */}
      <div className="glass-card !border-blue-500/15 flex items-start gap-3 animate-fade-in-up delay-200">
        <div className="p-1.5 rounded-lg bg-blue-500/15">
          <ShieldAlert className="w-5 h-5 text-blue-400 flex-shrink-0" />
        </div>
        <p className="text-sm text-blue-200/80 leading-relaxed">
          <strong className="text-blue-300">{t("results.advisoryNotice")}:</strong> {t("disclaimer")}
        </p>
      </div>

      {/* Try another */}
      <div className="flex justify-center animate-fade-in-up delay-300">
        <button
          onClick={() => window.location.reload()}
          className="px-8 py-3 border-2 border-emerald-500/30 text-emerald-400 rounded-xl font-semibold hover:bg-emerald-500/10 hover:border-emerald-500/50 transition-all duration-300 hover:shadow-lg hover:shadow-emerald-500/5"
        >
          {t("results.tryAnother")}
        </button>
      </div>
    </div>
  );
}
