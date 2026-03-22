import React, { useState, useEffect } from "react";
import { Search, Loader2, Info, ExternalLink, Leaf, Globe } from "lucide-react";
import { getSchemes, getSchemeOptions, type Scheme, type SchemeOptions } from "../services/schemeApi";
import { useTranslation } from "react-i18next";

export function SchemesRecommendation() {
  const { t, i18n } = useTranslation();
  
  const [options, setOptions] = useState<SchemeOptions>({ states: [], categories: [] });
  const [schemes, setSchemes] = useState<Scheme[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [state, setState] = useState("");
  const [keyword, setKeyword] = useState("");

  const langCode = i18n.language.split("-")[0];

  useEffect(() => {
    // Fetch options and initial schemes
    const init = async () => {
      setLoading(true);
      try {
        const [optRes, schemeRes] = await Promise.all([
          getSchemeOptions(),
          getSchemes({ language: langCode })
        ]);
        setOptions(optRes);
        // Handle paginated response
        const results = Array.isArray(schemeRes) ? schemeRes : (schemeRes as any).results ?? [];
        setSchemes(results);
      } catch {
        setError(t("schemes.loadError"));
      } finally {
        setLoading(false);
      }
    };
    init();
  }, [i18n.language]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await getSchemes({ 
        state, 
        keyword,
        language: langCode
      });
      // Handle paginated response
      const results = Array.isArray(res) ? res : (res as any).results ?? [];
      setSchemes(results);
    } catch {
      setError(t("schemes.loadError"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 animate-fade-in pb-10">
      
      {/* ── Filters Section ── */}
      <div className="glass-card p-6 md:p-8 relative overflow-hidden">
        {/* Simple decoration */}
        <div className="absolute top-0 right-0 -mr-16 -mt-16 w-48 h-48 bg-emerald-500/10 rounded-full blur-2xl" />
        
        <h2 className="text-xl font-bold text-gray-800 mb-6 flex items-center gap-2">
          <Search className="w-5 h-5 text-emerald-600" />
          {t("schemes.findTitle")}
        </h2>
        
        <form onSubmit={handleSearch} className="relative z-10 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            {/* keyword */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700">{t("schemes.keywordLabel")}</label>
              <input
                type="text"
                placeholder={t("schemes.keywordLabel")}
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                className="w-full px-4 py-2 rounded-xl border border-gray-200 focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 outline-none transition-all placeholder:text-gray-400 bg-white/50 backdrop-blur-sm shadow-sm"
              />
            </div>

            {/* State */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700">{t("schemes.stateLabel")}</label>
              <select
                value={state}
                onChange={(e) => setState(e.target.value)}
                className="w-full px-4 py-2 rounded-xl border border-gray-200 focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 outline-none transition-all bg-white/50 backdrop-blur-sm shadow-sm"
              >
                <option value="">All India</option>
                {options.states.filter(s => s !== "All India").map(s => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
          </div>

          <button 
             type="submit" 
             disabled={loading}
             className="w-full h-11 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-medium transition-all shadow-sm hover:shadow active:scale-[0.98] disabled:opacity-70 flex items-center justify-center gap-2"
          >
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Search className="w-5 h-5" />}
            {t("schemes.searchButton")}
          </button>
        </form>
      </div>

      {/* ── Results Section ── */}
      <div className="space-y-6">
        {error && (
          <div className="p-4 bg-red-50 text-red-700 rounded-xl border border-red-200 flex items-center gap-3">
             <Info className="w-5 h-5 shrink-0" />
             <p>{error}</p>
          </div>
        )}

        {!loading && schemes.length === 0 && !error && (
          <div className="glass-card p-12 flex flex-col items-center justify-center text-center">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4 text-gray-400">
               <Leaf className="w-8 h-8 opacity-50" />
            </div>
            <h3 className="text-lg font-semibold text-gray-800">{t("schemes.noResults")}</h3>
            <p className="text-gray-500 mt-2">{t("schemes.noResultsHint")}</p>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {schemes.map((scheme, idx) => (
            <div key={idx} className="glass-card p-6 flex flex-col hover:border-emerald-300 transition-all hover:shadow-lg hover:shadow-emerald-500/5 group">
              <div className="flex-1">
                <div className="flex items-start justify-between gap-4">
                  <h3 className="text-lg font-bold text-gray-900 group-hover:text-emerald-700 transition-colors line-clamp-2">
                    {scheme.scheme_name}
                  </h3>
                </div>
                
                <div className="mt-4 text-sm text-gray-600 leading-relaxed min-h-[4.5rem]">
                  {scheme.short_description}
                </div>
                
                <div className="mt-4 flex flex-wrap gap-2">
                  {scheme.categories.slice(0, 3).map((cat, i) => (
                    <span key={i} className="px-2.5 py-1 text-xs font-medium bg-emerald-50 text-emerald-700 rounded-md border border-emerald-100/50">
                      {cat}
                    </span>
                  ))}
                  {scheme.categories.length > 3 && (
                    <span className="px-2.5 py-1 text-xs font-medium bg-gray-50 text-gray-600 rounded-md border border-gray-100">
                      +{scheme.categories.length - 3} more
                    </span>
                  )}
                </div>
              </div>
              
              <div className="mt-6 pt-5 border-t border-gray-100 flex items-center justify-between">
                <div className="text-xs text-gray-500 flex items-center gap-1.5">
                   {scheme.states.includes("All India") ? (
                      <>
                        <Globe className="w-3.5 h-3.5" /> All India
                      </>
                   ) : (
                      <>
                        <span className="font-medium text-gray-700">{scheme.states[0]}</span>
                        {scheme.states.length > 1 && ` +${scheme.states.length - 1} more`}
                      </>
                   )}
                </div>
                <a 
                  href={scheme.url || '#'} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="px-4 py-2 bg-gray-50 hover:bg-emerald-50 text-emerald-600 rounded-lg text-sm font-semibold inline-flex items-center gap-2 transition-colors border border-gray-200 hover:border-emerald-200"
                >
                  View Details
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
