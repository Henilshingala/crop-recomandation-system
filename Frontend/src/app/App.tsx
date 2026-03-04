import { useState } from "react";
import { useTranslation } from "react-i18next";
import { InputForm } from "@/app/components/InputForm";
import { ResultsSection } from "@/app/components/ResultsSection";
import { Sprout, Wheat, Loader2, ShieldAlert, Globe } from "lucide-react";
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
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-emerald-50/60 to-teal-50/40">
      {/* Header */}
      <header className="bg-white/90 backdrop-blur-md shadow-md border-b-4 border-green-600 sticky top-0 z-30">
        <div className="container mx-auto px-4 py-5">
          <div className="flex items-center justify-between gap-4">
            {/* Left spacer for centering */}
            <div className="hidden sm:block w-[160px]" />

            <div className="flex items-center gap-4 flex-1 justify-center">
              <div className="bg-green-600 p-3 rounded-full shadow-lg">
                <Wheat className="w-7 h-7 text-white" />
              </div>
              <div className="text-center">
                <h1 className="text-3xl md:text-4xl font-bold text-gray-900 tracking-tight">{t("app.title")}</h1>
                <p className="text-gray-600 mt-1 text-sm">{t("app.subtitle")}</p>
              </div>
              <div className="bg-green-600 p-3 rounded-full shadow-lg">
                <Sprout className="w-7 h-7 text-white" />
              </div>
            </div>

            {/* Language Switcher */}
            <div className="flex items-center gap-2">
              <Globe className="w-4 h-4 text-green-700 hidden sm:block" />
              <select
                value={i18n.language}
                onChange={(e) => i18n.changeLanguage(e.target.value)}
                className="bg-green-50 border border-green-300 text-green-800 text-sm rounded-lg px-2 py-1.5 focus:ring-2 focus:ring-green-500 focus:border-green-500 cursor-pointer"
                aria-label={t("nav.language")}
              >
                {LANGUAGES.map((lang) => (
                  <option key={lang.code} value={lang.code}>
                    {lang.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8 max-w-6xl">
        <div className="space-y-8">
          <InputForm onSubmit={handleSubmit} isLoading={isLoading} />

          {isLoading && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 text-green-600 animate-spin" />
              <span className="ml-3 text-lg text-gray-600">{t("loading")}</span>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
              <p className="font-semibold">{t("errors.title")}</p>
              <p>{error}</p>
              <p className="text-sm mt-2">{t("errors.serverHint")}</p>
            </div>
          )}

          {results && !isLoading && <ResultsSection data={results} userInput={lastInput} />}

          {!results && !isLoading && (
            <div className="bg-white/80 backdrop-blur-sm rounded-lg shadow-md p-6 border-l-4 border-green-600">
              <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <Sprout className="w-5 h-5 text-green-600" />
                {t("howItWorks.title")}
              </h3>
              <div className="text-sm text-gray-700 space-y-2">
                <p>{t("howItWorks.description")}</p>
                <p className="pt-2" dangerouslySetInnerHTML={{ __html: t("howItWorks.getStarted") }} />
              </div>
            </div>
          )}
        </div>
      </main>

      <footer className="bg-green-800 text-white mt-16 py-6">
        <div className="container mx-auto px-4 space-y-3">
          {/* Safety Disclaimer — always visible */}
          <div className="flex items-start justify-center gap-2 text-green-200 text-xs leading-relaxed max-w-2xl mx-auto">
            <ShieldAlert className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <p>{t("disclaimer")}</p>
          </div>
          <p className="text-sm text-center text-green-300">
            {t("footer.copyright")}
          </p>
        </div>
      </footer>
    </div>
  );
}
