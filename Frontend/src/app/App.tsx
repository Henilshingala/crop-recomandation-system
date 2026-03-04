import { useState } from "react";
import { useTranslation } from "react-i18next";
import { InputForm } from "@/app/components/InputForm";
import { ResultsSection } from "@/app/components/ResultsSection";
import { Sprout, Wheat, ShieldAlert, Globe } from "lucide-react";
import { getPrediction, type PredictionResponse, type PredictionInput } from "@/app/services/api";

const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "hi", label: "हिन्दी" },
  { code: "gu", label: "ગુજરાતી" },
  { code: "mr", label: "मराठी" },
  { code: "pa", label: "ਪੰਜਾਬੀ" },
  { code: "ta", label: "தமிழ்" },
  { code: "te", label: "తెలుగు" },
  { code: "kn", label: "ಕನ್ನಡ" },
  { code: "bn", label: "বাংলা" },
  { code: "or", label: "ଓଡ଼ିଆ" },
];

export default function App() {
  const { t, i18n } = useTranslation();
  const [results, setResults] = useState<PredictionResponse | null>(null);
  const [lastInput, setLastInput] = useState<PredictionInput | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setResults(null);

    const form = e.target as HTMLFormElement;
    const fd = new FormData(form);

    const input: PredictionInput = {
      N: parseFloat(fd.get('nitrogen') as string),
      P: parseFloat(fd.get('phosphorus') as string),
      K: parseFloat(fd.get('potassium') as string),
      temperature: parseFloat(fd.get('temperature') as string),
      humidity: parseFloat(fd.get('humidity') as string),
      ph: parseFloat(fd.get('ph') as string),
      rainfall: parseFloat(fd.get('rainfall') as string),
    };
    setLastInput(input);

    try {
      const response = await getPrediction(input);
      if (response && response.top_1 && response.top_3) {
        setResults(response);
      } else {
        throw new Error('Invalid response structure from API');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : t('errors.generic');
      setError(errorMessage);
      setResults(null);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-animated-gradient min-h-screen">
      {/* ── Sticky Glass Header ── */}
      <header className="glass-header sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between gap-4">
            <div className="hidden sm:block w-[140px]" />

            <div className="flex items-center gap-3 flex-1 justify-center">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center shadow-lg shadow-emerald-500/20">
                <Wheat className="w-5 h-5 text-white" />
              </div>
              <div className="text-center">
                <h1 className="text-2xl md:text-3xl font-bold text-white tracking-tight">{t("app.title")}</h1>
                <p className="text-emerald-300/60 text-xs mt-0.5">{t("app.subtitle")}</p>
              </div>
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-teal-500 to-emerald-600 flex items-center justify-center shadow-lg shadow-teal-500/20">
                <Sprout className="w-5 h-5 text-white" />
              </div>
            </div>

            {/* Language Switcher */}
            <div className="flex items-center gap-2">
              <Globe className="w-4 h-4 text-emerald-400/60 hidden sm:block" />
              <select
                value={i18n.language}
                onChange={(e) => i18n.changeLanguage(e.target.value)}
                className="bg-white/[0.06] backdrop-blur border border-white/10 text-emerald-200 text-sm rounded-lg px-3 py-1.5 focus:ring-1 focus:ring-emerald-500/50 focus:border-emerald-500/30 cursor-pointer outline-none transition-all"
                aria-label={t("nav.language")}
              >
                {LANGUAGES.map((lang) => (
                  <option key={lang.code} value={lang.code} className="bg-gray-900 text-white">
                    {lang.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </header>

      {/* ── Main Content ── */}
      <main className="container mx-auto px-4 py-10 max-w-6xl">
        <div className="space-y-8">
          <InputForm onSubmit={handleSubmit} isLoading={isLoading} />

          {/* Loading */}
          {isLoading && (
            <div className="glass-card p-12 flex flex-col items-center justify-center gap-4 animate-fade-in">
              <div className="flex gap-3">
                <div className="loading-dot" />
                <div className="loading-dot" />
                <div className="loading-dot" />
              </div>
              <p className="text-emerald-300/70 text-sm font-medium">{t("loading")}</p>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="glass-card !border-red-500/20 p-6 animate-fade-in-up">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-xl bg-red-500/15 flex items-center justify-center flex-shrink-0">
                  <ShieldAlert className="w-5 h-5 text-red-400" />
                </div>
                <div>
                  <p className="font-semibold text-red-300">{t("errors.title")}</p>
                  <p className="text-red-200/70 text-sm mt-1">{error}</p>
                  <p className="text-red-200/40 text-xs mt-2">{t("errors.serverHint")}</p>
                </div>
              </div>
            </div>
          )}

          {/* Results */}
          {results && !isLoading && <ResultsSection data={results} userInput={lastInput} />}

          {/* How It Works */}
          {!results && !isLoading && (
            <div className="glass-card p-6 animate-fade-in-up delay-200">
              <h3 className="font-semibold text-white mb-3 flex items-center gap-2">
                <Sprout className="w-5 h-5 text-emerald-400" />
                {t("howItWorks.title")}
              </h3>
              <div className="text-sm text-gray-300/70 space-y-2">
                <p>{t("howItWorks.description")}</p>
                <p className="pt-2 text-emerald-300/60" dangerouslySetInnerHTML={{ __html: t("howItWorks.getStarted") }} />
              </div>
            </div>
          )}
        </div>
      </main>

      {/* ── Footer ── */}
      <footer className="mt-20 border-t border-white/[0.05]">
        <div className="container mx-auto px-4 py-6 space-y-3">
          <div className="flex items-start justify-center gap-2 text-gray-400/70 text-xs leading-relaxed max-w-2xl mx-auto">
            <ShieldAlert className="w-4 h-4 flex-shrink-0 mt-0.5 text-emerald-500/40" />
            <p>{t("disclaimer")}</p>
          </div>
          <p className="text-xs text-center text-gray-500/50">
            {t("footer.copyright")}
          </p>
        </div>
      </footer>
    </div>
  );
}
