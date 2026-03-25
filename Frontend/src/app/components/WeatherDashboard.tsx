// ============================================================
// WeatherDashboard.tsx — Location-based weather for Indian farmers
// Uses cascading dropdowns: State → District → Sub-district → Village/City
// Uses OpenCage (via backend proxy) for geocoding, Open-Meteo for weather
// ============================================================

import React, { useState, useEffect, useRef, useCallback } from "react";
import {
  CloudSun,
  Loader2,
  MapPin,
  Droplets,
  Thermometer,
  CloudRain,
  Wind,
  Sun,
  CloudOff,
  ChevronDown,
  Search,
  X,
  Building2,
  Map as MapIcon,
  Home,
} from "lucide-react";
import { useTranslation } from "react-i18next";
import {
  API_BASE_URL,
  getLocationStates,
  getLocationDistricts,
  getLocationSubDistricts,
  getLocationVillages,
  type StateItem,
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

interface GeoResult {
  lat: number;
  lng: number;
}

// ── Helpers ────────────────────────────────────────────────────

/** Format ISO date string to readable day label */
function formatDayLabel(dateStr: string, isToday: boolean, isPast: boolean): string {
  if (isToday) return "Today";
  const date = new Date(dateStr + "T00:00:00");
  const now = new Date();
  const yesterday = new Date(now);
  yesterday.setDate(yesterday.getDate() - 1);
  if (
    isPast &&
    date.getDate() === yesterday.getDate() &&
    date.getMonth() === yesterday.getMonth()
  ) {
    return "Yesterday";
  }
  return date.toLocaleDateString("en-IN", { weekday: "short", month: "short", day: "numeric" });
}

/** Pick a weather icon based on conditions */
function WeatherIcon({ temp, rain, className }: { temp: number; rain: number; className?: string }) {
  if (rain > 5) return <CloudRain className={className} />;
  if (rain > 0.5) return <Droplets className={className} />;
  if (temp > 35) return <Sun className={className} />;
  return <CloudSun className={className} />;
}

/** Debounce hook */
function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}

// ── Searchable Dropdown ────────────────────────────────────────
interface SearchableDropdownProps {
  options: string[];
  value: string;
  onChange: (val: string) => void;
  placeholder: string;
  disabled?: boolean;
  icon?: React.ReactNode;
  loading?: boolean;
}

function SearchableDropdown({
  options,
  value,
  onChange,
  placeholder,
  disabled = false,
  icon,
  loading = false,
}: SearchableDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const filtered = options.filter((opt) =>
    opt.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Close on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
        setSearchTerm("");
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const handleSelect = (opt: string) => {
    onChange(opt);
    setIsOpen(false);
    setSearchTerm("");
  };

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        disabled={disabled || loading}
        onClick={() => {
          if (!disabled && !loading) {
            setIsOpen(!isOpen);
            setTimeout(() => inputRef.current?.focus(), 50);
          }
        }}
        className={`w-full flex items-center gap-2 px-4 py-3 rounded-xl border transition-all text-left
          ${disabled || loading
            ? "bg-gray-100/50 border-gray-200 text-gray-400 cursor-not-allowed"
            : "bg-white/60 backdrop-blur-sm border-gray-200 hover:border-emerald-300 text-gray-700 cursor-pointer shadow-sm"
          }
          ${isOpen ? "ring-2 ring-emerald-500/30 border-emerald-400" : ""}
        `}
      >
        {loading ? (
          <Loader2 className="w-4 h-4 text-emerald-500/70 animate-spin flex-shrink-0" />
        ) : (
          icon && <span className="text-emerald-500/70 flex-shrink-0">{icon}</span>
        )}
        <span className={`flex-1 truncate ${!value ? "text-gray-400" : "text-gray-800 font-medium"}`}>
          {loading ? "Loading..." : (value || placeholder)}
        </span>
        {value && !disabled && !loading && (
          <X
            className="w-4 h-4 text-gray-400 hover:text-red-500 transition-colors flex-shrink-0"
            onClick={(e) => {
              e.stopPropagation();
              onChange("");
              setSearchTerm("");
            }}
          />
        )}
        <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform flex-shrink-0 ${isOpen ? "rotate-180" : ""}`} />
      </button>

      {isOpen && !disabled && !loading && (
        <div className="absolute z-50 mt-2 w-full bg-white/95 backdrop-blur-xl border border-gray-200 rounded-xl shadow-2xl shadow-black/10 overflow-hidden animate-fade-in">
          {/* Search input */}
          <div className="p-2 border-b border-gray-100">
            <div className="flex items-center gap-2 px-3 py-2 bg-gray-50/80 rounded-lg">
              <Search className="w-4 h-4 text-gray-400" />
              <input
                ref={inputRef}
                type="text"
                className="flex-1 bg-transparent text-sm text-gray-700 placeholder:text-gray-400 outline-none"
                placeholder="Search..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>

          {/* Options list */}
          <div className="max-h-52 overflow-y-auto overscroll-contain">
            {filtered.length === 0 ? (
              <div className="px-4 py-6 text-center text-sm text-gray-400">No results found</div>
            ) : (
              filtered.map((opt) => (
                <button
                  key={opt}
                  type="button"
                  onClick={() => handleSelect(opt)}
                  className={`w-full text-left px-4 py-2.5 text-sm transition-colors hover:bg-emerald-50/80
                    ${opt === value ? "bg-emerald-50 text-emerald-700 font-medium" : "text-gray-700"}
                  `}
                >
                  {opt}
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Main Component ─────────────────────────────────────────────
export function WeatherDashboard() {
  const { t } = useTranslation();

  // Location data (fetched from backend)
  const [states, setStates] = useState<string[]>([]);
  const [districts, setDistricts] = useState<string[]>([]);
  const [cities, setCities] = useState<string[]>([]);
  const [subDistricts, setSubDistricts] = useState<string[]>([]);
  const [villages, setVillages] = useState<string[]>([]);

  // Selections
  const [selectedState, setSelectedState] = useState("");
  const [selectedDistrict, setSelectedDistrict] = useState("");
  const [selectedSubDistrict, setSelectedSubDistrict] = useState("");
  const [selectedLocation, setSelectedLocation] = useState("");

  // Loading states for each dropdown
  const [loadingStates, setLoadingStates] = useState(false);
  const [loadingDistricts, setLoadingDistricts] = useState(false);
  const [loadingSubDistricts, setLoadingSubDistricts] = useState(false);
  const [loadingVillages, setLoadingVillages] = useState(false);

  // Weather data
  const [weatherData, setWeatherData] = useState<DayWeather[] | null>(null);
  const [locationLabel, setLocationLabel] = useState("");

  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Caches
  const geoCache = useRef<Map<string, GeoResult>>(new Map());
  const abortRef = useRef<AbortController | null>(null);

  // Debounced location for triggering weather fetch
  const debouncedLocation = useDebounce(selectedLocation, 300);

  // ── Load states on mount ──
  useEffect(() => {
    setLoadingStates(true);
    getLocationStates()
      .then((data) => {
        setStates(data.map((s) => s.state).sort());
      })
      .catch(() => setError(t("weather.locationLoadError")))
      .finally(() => setLoadingStates(false));
  }, [t]);

  // ── Load districts + cities when state changes ──
  useEffect(() => {
    setDistricts([]);
    setCities([]);
    setSubDistricts([]);
    setVillages([]);
    setSelectedDistrict("");
    setSelectedSubDistrict("");
    setSelectedLocation("");
    setWeatherData(null);

    if (!selectedState) return;

    setLoadingDistricts(true);
    getLocationDistricts(selectedState)
      .then((data) => {
        setDistricts(data.districts);
        setCities(data.cities);
      })
      .catch(() => setError("Failed to load districts"))
      .finally(() => setLoadingDistricts(false));
  }, [selectedState]);

  // ── Load sub-districts when district changes ──
  useEffect(() => {
    setSubDistricts([]);
    setVillages([]);
    setSelectedSubDistrict("");
    setSelectedLocation("");
    setWeatherData(null);

    if (!selectedState || !selectedDistrict) return;

    setLoadingSubDistricts(true);
    getLocationSubDistricts(selectedState, selectedDistrict)
      .then((data) => {
        setSubDistricts(data);
      })
      .catch(() => setError("Failed to load sub-districts"))
      .finally(() => setLoadingSubDistricts(false));
  }, [selectedState, selectedDistrict]);

  // ── Load villages when sub-district changes ──
  useEffect(() => {
    setVillages([]);
    setSelectedLocation("");
    setWeatherData(null);

    if (!selectedState || !selectedDistrict || !selectedSubDistrict) return;

    setLoadingVillages(true);
    getLocationVillages(selectedState, selectedDistrict, selectedSubDistrict)
      .then((data) => {
        setVillages(data);
      })
      .catch(() => setError("Failed to load villages"))
      .finally(() => setLoadingVillages(false));
  }, [selectedState, selectedDistrict, selectedSubDistrict]);

  // ── Combined location options for final dropdown ──
  // Show villages from selected sub-district + cities from the state
  const locationOptions = React.useMemo(() => {
    const combined = new Set<string>();
    villages.forEach((v) => combined.add(v));
    // Only show cities if no sub-district selected (as a fallback)
    if (!selectedSubDistrict) {
      cities.forEach((c) => combined.add(c));
    }
    return [...combined].sort();
  }, [villages, cities, selectedSubDistrict]);

  // ── Geocode + fetch weather on location selection ──
  useEffect(() => {
    if (!debouncedLocation || !selectedState) return;

    const fetchWeather = async () => {
      // Cancel previous in-flight request
      if (abortRef.current) abortRef.current.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      setLoading(true);
      setError(null);

      try {
        // Build location string for geocoding (most specific first)
        const parts = [debouncedLocation];
        if (selectedSubDistrict) parts.push(selectedSubDistrict);
        if (selectedDistrict) parts.push(selectedDistrict);
        parts.push(selectedState, "India");
        const locationStr = parts.join(", ");
        setLocationLabel(locationStr);

        let geo = geoCache.current.get(locationStr);

        if (!geo) {
          const geoUrl = `${API_BASE_URL}/geocode/?q=${encodeURIComponent(locationStr)}`;
          const geoRes = await fetch(geoUrl, { signal: controller.signal });

          if (!geoRes.ok) {
            if (geoRes.status === 402 || geoRes.status === 429) {
              throw new Error(t("weather.rateLimitError"));
            }
            if (geoRes.status === 500) {
              throw new Error("Backend API key missing");
            }
            throw new Error(t("weather.geocodeError"));
          }

          const geoData = await geoRes.json();
          if (!geoData.results || geoData.results.length === 0) {
            // Fallback: try district-level, then state-level
            const fallbacks = [
              selectedDistrict ? `${selectedDistrict}, ${selectedState}, India` : null,
              `${selectedState}, India`,
            ].filter(Boolean) as string[];

            for (const fb of fallbacks) {
              const fbRes = await fetch(`${API_BASE_URL}/geocode/?q=${encodeURIComponent(fb)}`, {
                signal: controller.signal,
              });
              const fbData = await fbRes.json();
              if (fbData.results && fbData.results.length > 0) {
                geo = fbData.results[0].geometry as GeoResult;
                break;
              }
            }
            if (!geo) throw new Error(t("weather.locationNotFound"));
          } else {
            geo = geoData.results[0].geometry as GeoResult;
          }

          geoCache.current.set(locationStr, geo!);
        }

        // 2. Fetch weather from Open-Meteo
        const weatherUrl = `https://api.open-meteo.com/v1/forecast?latitude=${geo!.lat}&longitude=${geo!.lng}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&hourly=relativehumidity_2m&past_days=1&forecast_days=7&timezone=Asia%2FKolkata`;

        const weatherRes = await fetch(weatherUrl, { signal: controller.signal });
        if (!weatherRes.ok) throw new Error(t("weather.fetchError"));

        const wData = await weatherRes.json();

        // 3. Process data
        const todayStr = new Date().toISOString().split("T")[0];
        const dailyDates: string[] = wData.daily.time;
        const maxTemps: number[] = wData.daily.temperature_2m_max;
        const minTemps: number[] = wData.daily.temperature_2m_min;
        const precip: number[] = wData.daily.precipitation_sum;
        const hourlyTimes: string[] = wData.hourly.time;
        const hourlyHumidity: number[] = wData.hourly.relativehumidity_2m;

        // Average hourly humidity per day
        const humidityByDay = new Map<string, number[]>();
        hourlyTimes.forEach((ts, i) => {
          const day = ts.split("T")[0];
          if (!humidityByDay.has(day)) humidityByDay.set(day, []);
          humidityByDay.get(day)!.push(hourlyHumidity[i]);
        });

        const days: DayWeather[] = dailyDates.map((date, i) => {
          const dayHumArr = humidityByDay.get(date) || [];
          const avgHumidity =
            dayHumArr.length > 0
              ? Math.round(dayHumArr.reduce((a, b) => a + b, 0) / dayHumArr.length)
              : 0;

          const isToday = date === todayStr;
          const isPast = date < todayStr;

          return {
            date,
            label: formatDayLabel(date, isToday, isPast),
            tempMax: Math.round(maxTemps[i] * 10) / 10,
            tempMin: Math.round(minTemps[i] * 10) / 10,
            humidity: avgHumidity,
            precipitation: Math.round(precip[i] * 10) / 10,
            isToday,
            isPast,
          };
        });

        if (!controller.signal.aborted) {
          setWeatherData(days);
        }
      } catch (err: unknown) {
        if ((err as { name?: string }).name === "AbortError") return;
        setError(
          err instanceof Error ? err.message : t("weather.genericError")
        );
        setWeatherData(null);
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    };

    fetchWeather();

    return () => {
      if (abortRef.current) abortRef.current.abort();
    };
  }, [debouncedLocation, selectedState, selectedDistrict, selectedSubDistrict, t]);

  const todayData = weatherData?.find((d) => d.isToday);
  const forecastDays = weatherData?.filter((d) => !d.isToday) || [];

  // ── Render ──
  return (
    <div className="space-y-8 animate-fade-in pb-10">
      {/* ── Location Selection ── */}
      <div className="glass-card p-6 md:p-8 relative z-20">
        {/* Decorative blur */}
        <div className="absolute inset-0 overflow-hidden rounded-2xl pointer-events-none">
          <div className="absolute -top-20 -right-20 w-56 h-56 bg-sky-400/10 rounded-full blur-3xl" />
          <div className="absolute -bottom-16 -left-16 w-40 h-40 bg-emerald-400/10 rounded-full blur-2xl" />
        </div>

        <h2 className="text-xl font-bold text-gray-800 mb-6 flex items-center gap-2 relative z-10">
          <MapPin className="w-5 h-5 text-emerald-600" />
          {t("weather.selectLocation")}
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 relative z-10">
          {/* State */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-600 flex items-center gap-1.5">
              <MapPin className="w-3.5 h-3.5 text-emerald-500" />
              {t("weather.state")}
            </label>
            <SearchableDropdown
              options={states}
              value={selectedState}
              onChange={(v) => setSelectedState(v)}
              placeholder={t("weather.selectState")}
              icon={<MapPin className="w-4 h-4" />}
              loading={loadingStates}
            />
          </div>

          {/* District */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-600 flex items-center gap-1.5">
              <Building2 className="w-3.5 h-3.5 text-emerald-500" />
              {t("weather.district") || "District"}
            </label>
            <SearchableDropdown
              options={districts}
              value={selectedDistrict}
              onChange={(v) => setSelectedDistrict(v)}
              placeholder={t("weather.selectDistrict") || "Select District"}
              disabled={!selectedState}
              icon={<Building2 className="w-4 h-4" />}
              loading={loadingDistricts}
            />
          </div>

          {/* Sub-district */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-600 flex items-center gap-1.5">
              <MapIcon className="w-3.5 h-3.5 text-emerald-500" />
              {t("weather.subDistrict") || "Sub-district / Taluka"}
            </label>
            <SearchableDropdown
              options={subDistricts}
              value={selectedSubDistrict}
              onChange={(v) => setSelectedSubDistrict(v)}
              placeholder={t("weather.selectSubDistrict") || "Select Sub-district"}
              disabled={!selectedDistrict}
              icon={<MapIcon className="w-4 h-4" />}
              loading={loadingSubDistricts}
            />
          </div>

          {/* Village / City / Town */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-600 flex items-center gap-1.5">
              <Home className="w-3.5 h-3.5 text-emerald-500" />
              {t("weather.village") || "Village / City / Town"}
            </label>
            <SearchableDropdown
              options={locationOptions}
              value={selectedLocation}
              onChange={(v) => setSelectedLocation(v)}
              placeholder={t("weather.selectVillage") || "Select Village / City / Town"}
              disabled={!selectedSubDistrict}
              icon={<Home className="w-4 h-4" />}
              loading={loadingVillages}
            />
          </div>
        </div>
      </div>

      {/* ── Loading State ── */}
      {loading && (
        <div className="glass-card p-12 flex flex-col items-center justify-center gap-4 animate-fade-in">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-sky-100 to-emerald-100 flex items-center justify-center">
            <Loader2 className="w-8 h-8 text-emerald-600 animate-spin" />
          </div>
          <p className="text-emerald-700/70 text-sm font-medium">
            {t("weather.loading")}
          </p>
        </div>
      )}

      {/* ── Error State ── */}
      {error && !loading && (
        <div className="glass-card !border-red-200 p-6 animate-fade-in-up">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-xl bg-red-100 flex items-center justify-center flex-shrink-0">
              <CloudOff className="w-5 h-5 text-red-600" />
            </div>
            <div>
              <p className="font-semibold text-red-800">{t("weather.errorTitle")}</p>
              <p className="text-red-600/80 text-sm mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* ── Weather Data ── */}
      {weatherData && !loading && (
        <div className="space-y-6 animate-fade-in-up">
          {/* Location header */}
          <div className="flex items-center gap-2 text-gray-500 text-sm">
            <MapPin className="w-4 h-4 text-emerald-500" />
            <span>{locationLabel}</span>
          </div>

          {/* ── TODAY Hero Card ── */}
          {todayData && (
            <div className="relative overflow-hidden rounded-2xl border border-white/40 bg-gradient-to-br from-sky-500 via-emerald-500 to-teal-600 p-6 md:p-8 text-white shadow-xl shadow-emerald-500/15">
              {/* Glass overlay */}
              <div className="absolute inset-0 bg-white/[0.08] backdrop-blur-[1px]" />
              {/* Decorative shapes */}
              <div className="absolute -top-10 -right-10 w-40 h-40 bg-white/10 rounded-full blur-2xl" />
              <div className="absolute -bottom-8 -left-8 w-32 h-32 bg-white/5 rounded-full blur-xl" />

              <div className="relative z-10">
                <div className="flex items-center gap-2 text-white/80 mb-2">
                  <CloudSun className="w-5 h-5" />
                  <span className="text-sm font-medium uppercase tracking-wide">
                    {t("weather.today")}
                  </span>
                </div>

                <div className="flex flex-col sm:flex-row items-start sm:items-end justify-between gap-6">
                  {/* Temperature */}
                  <div>
                    <div className="flex items-start gap-1">
                      <span className="text-7xl md:text-8xl font-bold tracking-tighter leading-none">
                        {Math.round((todayData.tempMax + todayData.tempMin) / 2)}
                      </span>
                      <span className="text-3xl font-light mt-2">°C</span>
                    </div>
                    <p className="text-white/70 text-sm mt-2">
                      {todayData.tempMin}° / {todayData.tempMax}°
                    </p>
                  </div>

                  {/* Weather icon */}
                  <div className="hidden sm:flex items-center justify-center">
                    <WeatherIcon
                      temp={todayData.tempMax}
                      rain={todayData.precipitation}
                      className="w-20 h-20 text-white/30"
                    />
                  </div>

                  {/* Details */}
                  <div className="flex flex-wrap gap-6">
                    <div className="flex items-center gap-2.5">
                      <div className="w-10 h-10 rounded-xl bg-white/15 flex items-center justify-center">
                        <Droplets className="w-5 h-5" />
                      </div>
                      <div>
                        <p className="text-white/60 text-xs">{t("weather.humidity")}</p>
                        <p className="text-lg font-semibold">{todayData.humidity}%</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2.5">
                      <div className="w-10 h-10 rounded-xl bg-white/15 flex items-center justify-center">
                        <CloudRain className="w-5 h-5" />
                      </div>
                      <div>
                        <p className="text-white/60 text-xs">{t("weather.rain")}</p>
                        <p className="text-lg font-semibold">{todayData.precipitation} mm</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ── 7-Day Forecast Grid ── */}
          <div>
            <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
              <Thermometer className="w-5 h-5 text-emerald-600" />
              {t("weather.forecast")}
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-7 gap-3">
              {forecastDays.map((day) => (
                <div
                  key={day.date}
                  className={`glass-card p-4 flex flex-col items-center text-center transition-all hover:shadow-lg hover:border-emerald-300 hover:-translate-y-0.5 group
                    ${day.isPast ? "opacity-70" : ""}
                  `}
                >
                  {/* Day label */}
                  <p
                    className={`text-xs font-semibold uppercase tracking-wider mb-3
                    ${day.isPast ? "text-gray-400" : "text-emerald-600/80"}
                  `}
                  >
                    {day.label}
                  </p>

                  {/* Weather icon */}
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-sky-50 to-emerald-50 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                    <WeatherIcon
                      temp={day.tempMax}
                      rain={day.precipitation}
                      className="w-5 h-5 text-emerald-600"
                    />
                  </div>

                  {/* Temperature */}
                  <div className="mb-3">
                    <p className="text-lg font-bold text-gray-900">
                      {day.tempMax}°
                    </p>
                    <p className="text-xs text-gray-400">{day.tempMin}°</p>
                  </div>

                  {/* Humidity */}
                  <div className="flex items-center gap-1 text-xs text-sky-600 mb-1">
                    <Droplets className="w-3 h-3" />
                    <span>{day.humidity}%</span>
                  </div>

                  {/* Rain */}
                  <div className="flex items-center gap-1 text-xs text-blue-500">
                    <CloudRain className="w-3 h-3" />
                    <span>{day.precipitation}mm</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── Empty State ── */}
      {!weatherData && !loading && !error && (
        <div className="glass-card p-12 flex flex-col items-center justify-center text-center animate-fade-in-up">
          <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-sky-100 to-emerald-100 flex items-center justify-center mb-5">
            <CloudSun className="w-10 h-10 text-emerald-500/60" />
          </div>
          <h3 className="text-lg font-semibold text-gray-800">
            {t("weather.emptyTitle")}
          </h3>
          <p className="text-gray-500 mt-2 max-w-md text-sm">
            {t("weather.emptyDescription")}
          </p>
        </div>
      )}
    </div>
  );
}
