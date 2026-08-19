// WeatherDashboard.tsx — Themed to match AgriMitra design system
// Warm earth tones: paper/ink/agri-green/mustard/clay
// Responsive: mobile-first cascading dropdowns

import React, { useState, useEffect, useRef } from "react";
import {
  CloudSun, Loader2, MapPin, Droplets, Thermometer,
  CloudRain, Sun, CloudOff, ChevronDown, Search, X,
  Building2, Map as MapIcon, Home, AlertTriangle,
} from "lucide-react";
import { useTranslation } from "react-i18next";
import {
  API_BASE_URL,
  getLocationStates,
  getLocationDistricts,
  getLocationSubDistricts,
  getLocationVillages,
} from "../services/api";

// ── Types ──────────────────────────────────────────────────────
interface DayWeather {
  date: string;
  label: string;
  tempMax: number;
  tempMin: number;
  humidity: number;
  precipitation: number;
  isToday: boolean;
  isPast: boolean;
}

interface GeoResult { lat: number; lng: number; }

// ── Helpers ────────────────────────────────────────────────────
function formatDayLabel(dateStr: string, isToday: boolean, isPast: boolean): string {
  if (isToday) return "Today";
  const date = new Date(dateStr + "T00:00:00");
  const now = new Date();
  const yesterday = new Date(now);
  yesterday.setDate(yesterday.getDate() - 1);
  if (isPast && date.getDate() === yesterday.getDate() && date.getMonth() === yesterday.getMonth()) {
    return "Yesterday";
  }
  return date.toLocaleDateString("en-IN", { weekday: "short", month: "short", day: "numeric" });
}

function WeatherIcon({ temp, rain, size = "md" }: { temp: number; rain: number; size?: "sm"|"md"|"lg" }) {
  const cls = size === "lg" ? "w-12 h-12" : size === "sm" ? "w-4 h-4" : "w-6 h-6";
  const color = "text-[var(--color-agri-green)]";
  if (rain > 5) return <CloudRain className={`${cls} ${color}`} />;
  if (rain > 0.5) return <Droplets className={`${cls} ${color}`} />;
  if (temp > 35) return <Sun className={`${cls} text-[var(--color-mustard)]`} />;
  return <CloudSun className={`${cls} ${color}`} />;
}

function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(t);
  }, [value, delay]);
  return debounced;
}

// ── Searchable Dropdown ────────────────────────────────────────
function SearchableDropdown({
  options, value, onChange, placeholder, disabled = false, icon, loading = false, label,
}: {
  options: string[]; value: string; onChange: (v: string) => void;
  placeholder: string; disabled?: boolean; icon?: React.ReactNode;
  loading?: boolean; label: string;
}) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const ref = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const filtered = options.filter(o => o.toLowerCase().includes(search.toLowerCase()));

  useEffect(() => {
    const h = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) { setOpen(false); setSearch(""); }
    };
    document.addEventListener("mousedown", h);
    return () => document.removeEventListener("mousedown", h);
  }, []);

  return (
    <div ref={ref} className="relative">
      <label className="eyebrow block mb-1.5 flex items-center gap-1">
        <span className="text-[var(--color-agri-green)]">{icon}</span>
        {label}
      </label>
      <button
        type="button"
        disabled={disabled || loading}
        onClick={() => { if (!disabled && !loading) { setOpen(!open); setTimeout(() => inputRef.current?.focus(), 50); } }}
        className={`agri-input w-full flex items-center gap-2 text-left px-3 py-2.5 text-sm
          ${disabled || loading ? "opacity-50 cursor-not-allowed" : "cursor-pointer hover:border-[var(--color-agri-green)]"}
          ${open ? "!border-[var(--color-agri-green)] ring-2 ring-[var(--color-agri-green)]/20" : ""}
        `}
      >
        {loading ? (
          <Loader2 className="w-4 h-4 text-[var(--color-ink-soft)] animate-spin flex-shrink-0" />
        ) : null}
        <span className={`flex-1 truncate ${!value ? "text-[var(--color-ink-soft)]" : "text-[var(--color-ink)] font-medium"}`}>
          {loading ? "Loading…" : (value || placeholder)}
        </span>
        {value && !disabled && !loading && (
          <X className="w-3.5 h-3.5 text-[var(--color-ink-soft)] hover:text-[var(--color-clay)] flex-shrink-0"
            onClick={e => { e.stopPropagation(); onChange(""); setSearch(""); }} />
        )}
        <ChevronDown className={`w-4 h-4 text-[var(--color-ink-soft)] flex-shrink-0 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>

      {open && !disabled && !loading && (
        <div className="absolute z-50 mt-1 w-full bg-[var(--color-card)] border border-[var(--color-border-line)] rounded-xl shadow-xl shadow-[var(--color-ink)]/10 overflow-hidden animate-fade-in-up">
          <div className="p-2 border-b border-[var(--color-border-line)]">
            <div className="flex items-center gap-2 px-2 py-1.5 bg-[var(--color-paper)] rounded-lg">
              <Search className="w-3.5 h-3.5 text-[var(--color-ink-soft)]" />
              <input ref={inputRef} type="text"
                className="flex-1 bg-transparent text-sm text-[var(--color-ink)] placeholder:text-[var(--color-ink-soft)] outline-none"
                placeholder="Search…" value={search} onChange={e => setSearch(e.target.value)} />
            </div>
          </div>
          <div className="max-h-52 overflow-y-auto overscroll-contain">
            {filtered.length === 0 ? (
              <p className="px-4 py-5 text-center text-sm text-[var(--color-ink-soft)]">No results</p>
            ) : filtered.map(opt => (
              <button key={opt} type="button" onClick={() => { onChange(opt); setOpen(false); setSearch(""); }}
                className={`w-full text-left px-4 py-2.5 text-sm transition-colors hover:bg-[var(--color-paper-deep)]/60
                  ${opt === value ? "text-[var(--color-agri-green-deep)] font-semibold bg-[var(--color-paper-deep)]/40" : "text-[var(--color-ink)]"}
                `}>{opt}</button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Main Component ─────────────────────────────────────────────
export function WeatherDashboard() {
  const { t } = useTranslation();

  const [states, setStates] = useState<string[]>([]);
  const [districts, setDistricts] = useState<string[]>([]);
  const [subDistricts, setSubDistricts] = useState<string[]>([]);
  const [villages, setVillages] = useState<string[]>([]);
  const [cities, setCities] = useState<string[]>([]);

  const [selectedState, setSelectedState] = useState("");
  const [selectedDistrict, setSelectedDistrict] = useState("");
  const [selectedSubDistrict, setSelectedSubDistrict] = useState("");
  const [selectedLocation, setSelectedLocation] = useState("");

  const [loadingStates, setLoadingStates] = useState(false);
  const [loadingDistricts, setLoadingDistricts] = useState(false);
  const [loadingSubDistricts, setLoadingSubDistricts] = useState(false);
  const [loadingVillages, setLoadingVillages] = useState(false);

  const [weatherData, setWeatherData] = useState<DayWeather[] | null>(null);
  const [locationLabel, setLocationLabel] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const geoCache = useRef<Map<string, GeoResult>>(new Map());
  const abortRef = useRef<AbortController | null>(null);
  const debouncedLocation = useDebounce(selectedLocation, 300);

  useEffect(() => {
    setLoadingStates(true);
    getLocationStates()
      .then(data => setStates(data.map(s => s.state).sort()))
      .catch(() => setError(t("weather.locationLoadError")))
      .finally(() => setLoadingStates(false));
  }, [t]);

  useEffect(() => {
    setDistricts([]); setCities([]); setSubDistricts([]); setVillages([]);
    setSelectedDistrict(""); setSelectedSubDistrict(""); setSelectedLocation("");
    setWeatherData(null);
    if (!selectedState) return;
    setLoadingDistricts(true);
    getLocationDistricts(selectedState)
      .then(data => { setDistricts(data.districts); setCities(data.cities); })
      .catch(() => setError("Failed to load districts"))
      .finally(() => setLoadingDistricts(false));
  }, [selectedState]);

  useEffect(() => {
    setSubDistricts([]); setVillages([]); setSelectedSubDistrict(""); setSelectedLocation(""); setWeatherData(null);
    if (!selectedState || !selectedDistrict) return;
    setLoadingSubDistricts(true);
    getLocationSubDistricts(selectedState, selectedDistrict)
      .then(data => setSubDistricts(data))
      .catch(() => setError("Failed to load sub-districts"))
      .finally(() => setLoadingSubDistricts(false));
  }, [selectedState, selectedDistrict]);

  useEffect(() => {
    setVillages([]); setSelectedLocation(""); setWeatherData(null);
    if (!selectedState || !selectedDistrict || !selectedSubDistrict) return;
    setLoadingVillages(true);
    getLocationVillages(selectedState, selectedDistrict, selectedSubDistrict)
      .then(data => setVillages(data))
      .catch(() => setError("Failed to load villages"))
      .finally(() => setLoadingVillages(false));
  }, [selectedState, selectedDistrict, selectedSubDistrict]);

  const locationOptions = React.useMemo(() => {
    const s = new Set<string>();
    villages.forEach(v => s.add(v));
    if (!selectedSubDistrict) cities.forEach(c => s.add(c));
    return [...s].sort();
  }, [villages, cities, selectedSubDistrict]);

  useEffect(() => {
    if (!debouncedLocation || !selectedState) return;
    const fetchWeather = async () => {
      if (abortRef.current) abortRef.current.abort();
      const controller = new AbortController();
      abortRef.current = controller;
      setLoading(true); setError(null);
      try {
        const parts = [debouncedLocation];
        if (selectedSubDistrict) parts.push(selectedSubDistrict);
        if (selectedDistrict) parts.push(selectedDistrict);
        parts.push(selectedState, "India");
        const locStr = parts.join(", ");
        setLocationLabel(locStr);
        let geo = geoCache.current.get(locStr);
        if (!geo) {
          const geoRes = await fetch(`${API_BASE_URL}/geocode/?q=${encodeURIComponent(locStr)}`, { signal: controller.signal });
          if (!geoRes.ok) throw new Error(t("weather.geocodeError"));
          const geoData = await geoRes.json();
          if (!geoData.results || geoData.results.length === 0) {
            const fb = selectedDistrict ? `${selectedDistrict}, ${selectedState}, India` : `${selectedState}, India`;
            const fbRes = await fetch(`${API_BASE_URL}/geocode/?q=${encodeURIComponent(fb)}`, { signal: controller.signal });
            const fbData = await fbRes.json();
            if (fbData.results?.length > 0) geo = fbData.results[0].geometry as GeoResult;
            else throw new Error(t("weather.locationNotFound"));
          } else {
            geo = geoData.results[0].geometry as GeoResult;
          }
          geoCache.current.set(locStr, geo!);
        }
        const wUrl = `https://api.open-meteo.com/v1/forecast?latitude=${geo!.lat}&longitude=${geo!.lng}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&hourly=relativehumidity_2m&past_days=1&forecast_days=7&timezone=Asia%2FKolkata`;
        const wRes = await fetch(wUrl, { signal: controller.signal });
        if (!wRes.ok) throw new Error(t("weather.fetchError"));
        const wData = await wRes.json();
        const todayStr = new Date().toISOString().split("T")[0];
        const humByDay = new Map<string, number[]>();
        (wData.hourly.time as string[]).forEach((ts, i) => {
          const d = ts.split("T")[0];
          if (!humByDay.has(d)) humByDay.set(d, []);
          humByDay.get(d)!.push(wData.hourly.relativehumidity_2m[i]);
        });
        const days: DayWeather[] = (wData.daily.time as string[]).map((date, i) => {
          const arr = humByDay.get(date) || [];
          const isToday = date === todayStr;
          const isPast = date < todayStr;
          return {
            date, label: formatDayLabel(date, isToday, isPast),
            tempMax: Math.round(wData.daily.temperature_2m_max[i] * 10) / 10,
            tempMin: Math.round(wData.daily.temperature_2m_min[i] * 10) / 10,
            humidity: arr.length ? Math.round(arr.reduce((a, b) => a + b, 0) / arr.length) : 0,
            precipitation: Math.round(wData.daily.precipitation_sum[i] * 10) / 10,
            isToday, isPast,
          };
        });
        if (!controller.signal.aborted) setWeatherData(days);
      } catch (err: unknown) {
        if ((err as { name?: string }).name === "AbortError") return;
        setError(err instanceof Error ? err.message : t("weather.genericError"));
        setWeatherData(null);
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    };
    fetchWeather();
    return () => { if (abortRef.current) abortRef.current.abort(); };
  }, [debouncedLocation, selectedState, selectedDistrict, selectedSubDistrict, t]);

  const todayData = weatherData?.find(d => d.isToday);
  const forecastDays = weatherData?.filter(d => !d.isToday) || [];

  return (
    <div className="space-y-6 animate-fade-in-up pb-12">

      {/* ── Page Header ── */}
      <div className="space-y-1">
        <span className="eyebrow">{t("weather.selectLocation")}</span>
        <h2 className="text-3xl font-bold text-[var(--color-ink)]" style={{ fontFamily: "var(--font-display)" }}>
          {t("tabs.weather")}
        </h2>
      </div>

      {/* ── Location Picker Card ── */}
      <div className="agri-card p-6 md:p-8 relative z-20 !overflow-visible">
        <div className="absolute inset-0 opacity-[0.025] pointer-events-none rounded-2xl"
          style={{ backgroundImage: "radial-gradient(circle, var(--color-ink) 1px, transparent 1px)", backgroundSize: "20px 20px" }} />

        <div className="relative z-10 grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
          <SearchableDropdown
            options={states} value={selectedState} onChange={setSelectedState}
            placeholder={t("weather.selectState")} loading={loadingStates}
            icon={<MapPin className="w-3.5 h-3.5" />} label={t("weather.state")}
          />
          <SearchableDropdown
            options={districts} value={selectedDistrict} onChange={setSelectedDistrict}
            placeholder={t("weather.selectDistrict") || "Select District"}
            disabled={!selectedState} loading={loadingDistricts}
            icon={<Building2 className="w-3.5 h-3.5" />} label={t("weather.district") || "District"}
          />
          <SearchableDropdown
            options={subDistricts} value={selectedSubDistrict} onChange={setSelectedSubDistrict}
            placeholder={t("weather.selectSubDistrict") || "Select Sub-district"}
            disabled={!selectedDistrict} loading={loadingSubDistricts}
            icon={<MapIcon className="w-3.5 h-3.5" />} label={t("weather.subDistrict") || "Sub-district"}
          />
          <SearchableDropdown
            options={locationOptions} value={selectedLocation} onChange={setSelectedLocation}
            placeholder={t("weather.selectVillage") || "Select Village / City"}
            disabled={!selectedSubDistrict} loading={loadingVillages}
            icon={<Home className="w-3.5 h-3.5" />} label={t("weather.village") || "Village / City"}
          />
        </div>
      </div>

      {/* ── Loading ── */}
      {loading && (
        <div className="agri-card p-12 flex flex-col items-center gap-4 animate-fade-in-up">
          <div className="w-16 h-16 rounded-2xl bg-[var(--color-agri-green-deep)] flex items-center justify-center">
            <Loader2 className="w-8 h-8 text-white animate-spin" />
          </div>
          <p className="text-[var(--color-ink-soft)] text-sm font-medium">{t("weather.loading")}</p>
        </div>
      )}

      {/* ── Error ── */}
      {error && !loading && (
        <div className="agri-card !border-[var(--color-clay)]/40 bg-[var(--color-clay)]/5 p-5 animate-fade-in-up">
          <div className="flex items-start gap-3">
            <div className="w-9 h-9 rounded-xl bg-[var(--color-clay)]/15 flex items-center justify-center flex-shrink-0">
              <AlertTriangle className="w-5 h-5 text-[var(--color-clay)]" />
            </div>
            <div>
              <p className="font-semibold text-[var(--color-ink)]" style={{ fontFamily: "var(--font-display)" }}>
                {t("weather.errorTitle")}
              </p>
              <p className="text-[var(--color-clay)] text-sm mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* ── Weather Results ── */}
      {weatherData && !loading && (
        <div className="space-y-5 animate-fade-in-up">

          {/* Location breadcrumb */}
          <div className="flex items-center gap-1.5 text-[var(--color-ink-soft)] text-sm">
            <MapPin className="w-3.5 h-3.5 text-[var(--color-agri-green)]" />
            <span>{locationLabel}</span>
          </div>

          {/* ── Today's Hero Card ── */}
          {todayData && (
            <div className="agri-card overflow-hidden p-0">
              {/* Mustard scan line accent */}
              <div className="h-1 w-full bg-gradient-to-r from-[var(--color-agri-green)] via-[var(--color-mustard)] to-[var(--color-clay)]" />
              <div className="p-6 md:p-8">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">

                  {/* Left: label + temp */}
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <span className="eyebrow">{t("weather.today")}</span>
                    </div>
                    <div className="flex items-start gap-1">
                      <span className="text-7xl md:text-8xl font-bold text-[var(--color-ink)] leading-none" style={{ fontFamily: "var(--font-display)" }}>
                        {Math.round((todayData.tempMax + todayData.tempMin) / 2)}
                      </span>
                      <span className="text-2xl text-[var(--color-ink-soft)] mt-3">°C</span>
                    </div>
                    <p className="text-[var(--color-ink-soft)] text-sm">
                      {todayData.tempMin}° / {todayData.tempMax}°
                    </p>
                  </div>

                  {/* Right: icon + stats */}
                  <div className="flex items-center gap-8">
                    <WeatherIcon temp={todayData.tempMax} rain={todayData.precipitation} size="lg" />
                    <div className="grid grid-cols-2 gap-x-8 gap-y-4">
                      <div>
                        <p className="eyebrow mb-0.5">{t("weather.humidity")}</p>
                        <div className="flex items-center gap-1.5">
                          <Droplets className="w-4 h-4 text-[var(--color-agri-green)]" />
                          <span className="text-xl font-bold text-[var(--color-ink)]">{todayData.humidity}%</span>
                        </div>
                      </div>
                      <div>
                        <p className="eyebrow mb-0.5">{t("weather.rain")}</p>
                        <div className="flex items-center gap-1.5">
                          <CloudRain className="w-4 h-4 text-[var(--color-agri-green)]" />
                          <span className="text-xl font-bold text-[var(--color-ink)]">{todayData.precipitation} mm</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ── Forecast Grid ── */}
          <div>
            <h3 className="text-lg font-bold text-[var(--color-ink)] mb-4 flex items-center gap-2" style={{ fontFamily: "var(--font-display)" }}>
              <Thermometer className="w-4 h-4 text-[var(--color-agri-green)]" />
              {t("weather.forecast")}
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
              {forecastDays.map(day => (
                <div key={day.date}
                  className={`agri-card p-4 flex flex-col items-center text-center transition-all hover:-translate-y-0.5 hover:shadow-lg cursor-default
                    ${day.isPast ? "opacity-60" : ""}
                  `}
                >
                  <p className={`text-[10px] font-semibold uppercase tracking-wider mb-2.5
                    ${day.isPast ? "text-[var(--color-ink-soft)]" : "text-[var(--color-agri-green-deep)]"}
                  `}>
                    {day.label}
                  </p>
                  <div className="w-9 h-9 rounded-xl bg-[var(--color-paper-deep)] flex items-center justify-center mb-3">
                    <WeatherIcon temp={day.tempMax} rain={day.precipitation} size="sm" />
                  </div>
                  <p className="text-lg font-bold text-[var(--color-ink)]">{day.tempMax}°</p>
                  <p className="text-xs text-[var(--color-ink-soft)] mb-3">{day.tempMin}°</p>
                  <div className="w-full space-y-1 border-t border-[var(--color-border-line)] pt-2.5 mt-auto">
                    <div className="flex items-center justify-center gap-1 text-[10px] text-[var(--color-agri-green)]">
                      <Droplets className="w-3 h-3" /><span>{day.humidity}%</span>
                    </div>
                    <div className="flex items-center justify-center gap-1 text-[10px] text-[var(--color-ink-soft)]">
                      <CloudRain className="w-3 h-3" /><span>{day.precipitation}mm</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── Empty State ── */}
      {!weatherData && !loading && !error && (
        <div className="agri-card p-12 md:p-16 flex flex-col items-center text-center animate-fade-in-up">
          <div className="absolute inset-0 opacity-[0.025] pointer-events-none rounded-2xl"
            style={{ backgroundImage: "radial-gradient(circle, var(--color-ink) 1px, transparent 1px)", backgroundSize: "20px 20px" }} />
          <div className="relative z-10 flex flex-col items-center gap-4 max-w-sm mx-auto">
            <div className="w-20 h-20 rounded-2xl bg-[var(--color-paper-deep)] flex items-center justify-center">
              <CloudSun className="w-10 h-10 text-[var(--color-agri-green)]/60" />
            </div>
            <h3 className="text-xl font-bold text-[var(--color-ink)]" style={{ fontFamily: "var(--font-display)" }}>
              {t("weather.emptyTitle")}
            </h3>
            <p className="text-[var(--color-ink-soft)] text-sm leading-relaxed">
              {t("weather.emptyDescription")}
            </p>
            <div className="flex items-center gap-2 text-xs text-[var(--color-ink-soft)] mt-2">
              <MapPin className="w-3.5 h-3.5 text-[var(--color-agri-green)]" />
              <span>{t("weather.state")} → {t("weather.district") || "District"} → {t("weather.village") || "Village"}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
