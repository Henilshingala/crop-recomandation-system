import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import DOMPurify from "dompurify";
import { InputForm } from "@/app/components/InputForm";
import { ResultsSection } from "@/app/components/ResultsSection";
import { SchemesRecommendation } from "@/app/components/SchemesRecommendation";
import { WeatherDashboard } from "@/app/components/WeatherDashboard";
import { DiseaseDetection } from "@/app/components/DiseaseDetection";
import ChatWidget from "@/app/components/ChatWidget";
import { Sprout, ShieldAlert, Loader2, Menu, X } from "lucide-react";
import { getPrediction, type PredictionResponse, type PredictionInput } from "@/app/services/api";

const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "as", label: "অসমীয়া" },
  { code: "bn", label: "বাংলা" },
  { code: "brx", label: "बड़ो" },
  { code: "doi", label: "डोगरी" },
  { code: "gu", label: "ગુજરાતી" },
  { code: "hi", label: "हिन्दी" },
  { code: "kn", label: "ಕನ್ನಡ" },
  { code: "ks", label: "कॉशुर" },
  { code: "gom", label: "कोंकणी" },
  { code: "mai", label: "मैथिली" },
  { code: "ml", label: "മലയാളം" },
  { code: "mni", label: "মৈতৈলোন্" },
  { code: "mr", label: "मराठी" },
  { code: "ne", label: "नेपाली" },
  { code: "or", label: "ଓଡ଼ିଆ" },
  { code: "pa", label: "ਪੰਜਾਬੀ" },
  { code: "sa", label: "संस्कृतम्" },
  { code: "sat", label: "ᱥᱟᱱᱛᱟᱲᱤ" },
  { code: "sd", label: "سنڌي" },
  { code: "ta", label: "தமிழ்" },
  { code: "te", label: "తెలుగు" },
  { code: "ur", label: "اردو" },
];

function AILoadingSequence() {
  const { t } = useTranslation();
  const [step, setStep] = useState(0);
  
  const steps = [
    t("app.loading.step1"),
    t("app.loading.step2"),
    t("app.loading.step3"),
    t("app.loading.step4"),
    t("app.loading.step5")
  ];

  useEffect(() => {
    if (step < steps.length - 1) {
      const timer = setTimeout(() => {
        setStep(s => s + 1);
      }, 700);
      return () => clearTimeout(timer);
    }
  }, [step]);

  return (
    <div className="agri-card p-8 md:p-12 flex flex-col justify-center animate-fade-in relative overflow-hidden min-h-[300px]">
      <div className="absolute inset-0 opacity-[0.03] pointer-events-none" style={{ backgroundImage: 'radial-gradient(circle at center, var(--color-ink) 1px, transparent 1px)', backgroundSize: '24px 24px' }}></div>
      <div className="relative z-10 w-full max-w-md mx-auto space-y-5">
        {steps.map((text, i) => (
          <div key={i} className={`flex items-center gap-4 transition-all duration-500 ${i === step ? 'opacity-100 translate-x-0' : i < step ? 'opacity-40 translate-x-0' : 'opacity-0 -translate-x-4'}`}>
            {i < step ? (
              <div className="w-6 h-6 rounded-full bg-[var(--color-green-deep)] flex items-center justify-center flex-shrink-0 shadow-sm">
                <svg className="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>
              </div>
            ) : i === step ? (
              <Loader2 className="w-6 h-6 animate-spin text-[var(--color-mustard)] flex-shrink-0" />
            ) : (
              <div className="w-6 h-6 rounded-full border-2 border-[var(--color-border-line)] flex-shrink-0" />
            )}
            <p className={`text-sm md:text-base ${i === step ? 'font-bold text-[var(--color-ink)]' : 'text-[var(--color-ink-soft)]'}`}>{text}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function App() {
  const { t, i18n } = useTranslation();
  const [activeTab, setActiveTab] = useState<'crop' | 'schemes' | 'weather' | 'disease'>('crop');
  const [results, setResults] = useState<PredictionResponse | null>(null);
  const [lastInput, setLastInput] = useState<PredictionInput | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const tabs = [
    { id: 'crop' as const, label: t("tabs.cropRecommendation") },
    { id: 'schemes' as const, label: t("tabs.governmentSchemes") },
    { id: 'weather' as const, label: t("tabs.weather") },
    { id: 'disease' as const, label: t("tabs.disease") },
  ];

  const switchTab = (tab: typeof activeTab) => { setActiveTab(tab); setMobileMenuOpen(false); };


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
    <div className="min-h-screen">
      {/* ── Sticky Header ── */}
      <header className="sticky top-0 z-50 bg-[var(--color-paper)]/90 backdrop-blur-md border-b border-[var(--color-border-line)]">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between gap-4 py-3">
            {/* Brand */}
            <div className="flex items-center gap-3 flex-shrink-0">
              <div className="w-9 h-9 rounded-xl bg-[var(--color-agri-green-deep)] flex items-center justify-center">
                <Sprout className="w-5 h-5 text-white" />
              </div>
              <div className="flex flex-col">
                <span className="font-bold text-lg leading-none text-[var(--color-ink)]" style={{fontFamily: 'var(--font-display)'}}>{t("app.brandName")}</span>
                <span className="text-[9px] text-[var(--color-ink-soft)] font-medium uppercase tracking-widest mt-0.5 hidden sm:block">{t("app.brandSub")}</span>
              </div>
            </div>

            {/* Desktop Nav */}
            <nav className="hidden md:flex items-center gap-1">
              {tabs.map(tab => (
                <button key={tab.id} onClick={() => switchTab(tab.id)}
                  className={`relative px-4 py-2 text-sm font-medium rounded-lg transition-all
                    ${activeTab === tab.id
                      ? 'text-[var(--color-agri-green-deep)] bg-[var(--color-agri-green-deep)]/8'
                      : 'text-[var(--color-ink-soft)] hover:text-[var(--color-ink)] hover:bg-[var(--color-paper-deep)]/50'}
                  `}>
                  {tab.label}
                  {activeTab === tab.id && (
                    <span className="absolute bottom-0 left-3 right-3 h-0.5 bg-[var(--color-agri-green-deep)] rounded-full" />
                  )}
                </button>
              ))}
            </nav>

            {/* Right side */}
            <div className="flex items-center gap-3">
              <select value={i18n.language} onChange={(e) => i18n.changeLanguage(e.target.value)}
                className="bg-transparent text-[var(--color-ink)] text-sm font-medium cursor-pointer outline-none max-w-[90px] truncate"
                aria-label={t("nav.language")}>
                {LANGUAGES.map((lang) => (
                  <option key={lang.code} value={lang.code}>{lang.label}</option>
                ))}
              </select>
              <button className="btn-primary hidden lg:flex px-4 py-2 text-sm"
                onClick={() => { switchTab('crop'); window.scrollTo({top: 0, behavior: 'smooth'}); }}>
                {t("app.analyzeSoil")}
              </button>
              {/* Mobile menu button */}
              <button className="md:hidden w-9 h-9 rounded-lg border border-[var(--color-border-line)] flex items-center justify-center"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
                {mobileMenuOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {/* Mobile Nav Dropdown */}
          {mobileMenuOpen && (
            <div className="md:hidden border-t border-[var(--color-border-line)] py-2 space-y-0.5 animate-fade-in-up">
              {tabs.map(tab => (
                <button key={tab.id} onClick={() => switchTab(tab.id)}
                  className={`w-full text-left px-4 py-3 text-sm font-medium rounded-lg transition-colors
                    ${activeTab === tab.id
                      ? 'text-[var(--color-agri-green-deep)] bg-[var(--color-agri-green-deep)]/8'
                      : 'text-[var(--color-ink-soft)] hover:text-[var(--color-ink)] hover:bg-[var(--color-paper-deep)]/50'}
                  `}>
                  {tab.label}
                </button>
              ))}
            </div>
          )}
        </div>
      </header>

      {/* ── Main Content ── */}
      <main className="container mx-auto px-4 py-12 max-w-6xl w-full">
        {activeTab === 'crop' ? (
          <div className="space-y-24 animate-fade-in-up">
            
            {/* ── Hero Section ── */}
            <section className="grid grid-cols-1 lg:grid-cols-2 gap-10 lg:gap-12 items-center">
              <div className="space-y-5 min-w-0">
                <span className="eyebrow">{t("app.advisoryTitle")}</span>
                <h1
                  className="text-[var(--color-ink)] leading-tight"
                  style={{
                    fontSize: 'clamp(1.75rem, 4.5vw, 3.25rem)',
                    wordBreak: 'break-word',
                    overflowWrap: 'break-word',
                    hyphens: 'auto',
                  }}
                >
                  {t("app.heroTitle1")}<i>{t("app.heroTitle2")}</i>{t("app.heroTitle3")}
                </h1>
                <p className="text-base md:text-lg text-[var(--color-ink-soft)] leading-relaxed">
                  {t("app.heroDesc")}
                </p>
                <div className="flex flex-wrap items-center gap-3 pt-1">
                   <button className="btn-primary" onClick={() => {
                     const form = document.getElementById('soil-form');
                     if(form) form.scrollIntoView({behavior: 'smooth'});
                   }}>{t("app.uploadReportBtn")}</button>
                   <button className="btn-secondary" onClick={() => switchTab('schemes')}>{t("app.viewSchemesBtn")}</button>
                </div>
                <p className="text-xs text-[var(--color-ink-soft)] opacity-70 font-medium">
                  {t("app.offlineNotice")}
                </p>
              </div>
              
              <div className="relative min-w-0" id="soil-form">
                <InputForm onSubmit={handleSubmit} isLoading={isLoading} />
              </div>
            </section>

            {/* Error */}
            {error && (
              <div className="agri-card !border-red-300 bg-red-50 p-6 animate-fade-in-up">
                <div className="flex items-start gap-3">
                  <ShieldAlert className="w-5 h-5 text-red-600 mt-0.5" />
                  <div>
                    <p className="font-bold text-red-800" style={{fontFamily: 'var(--font-display)'}}>{t("errors.title")}</p>
                    <p className="text-red-700 text-sm mt-1">{error}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Results */}
            {results && !isLoading && (
              <div className="animate-fade-in-up scroll-mt-24" id="results-view">
                <ResultsSection data={results} userInput={lastInput} />
              </div>
            )}

            {/* Loading */}
            {isLoading && (
              <div className="animate-fade-in-up scroll-mt-24 mt-8">
                <AILoadingSequence />
              </div>
            )}

            {/* ── How It Works ── */}
            {!results && !isLoading && (
              <section className="agri-card p-0 overflow-hidden">
                <div className="grid grid-cols-1 md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-[var(--color-border-line)]">
                  <div className="p-8">
                    <span className="eyebrow mb-2 block">{t("app.step1")}</span>
                    <h3 className="text-xl font-bold mb-3">{t("app.step1Title")}</h3>
                    <p className="text-sm text-[var(--color-ink-soft)] leading-relaxed">{t("app.step1Desc")}</p>
                  </div>
                  <div className="p-8 bg-[var(--color-paper-deep)]/30">
                    <span className="eyebrow mb-2 block">{t("app.step2")}</span>
                    <h3 className="text-xl font-bold mb-3">{t("app.step2Title")}</h3>
                    <p className="text-sm text-[var(--color-ink-soft)] leading-relaxed">{t("app.step2Desc")}</p>
                  </div>
                  <div className="p-8">
                    <span className="eyebrow mb-2 block">{t("app.step3")}</span>
                    <h3 className="text-xl font-bold mb-3">{t("app.step3Title")}</h3>
                    <p className="text-sm text-[var(--color-ink-soft)] leading-relaxed">{t("app.step3Desc")}</p>
                  </div>
                </div>
              </section>
            )}

            {/* ── Accessibility / Access Tiers ── */}
            <section className="space-y-8">
              <div className="text-center max-w-2xl mx-auto space-y-3">
                <h2 className="text-3xl font-bold text-[var(--color-ink)]">{t("app.accessibilityTitle")}</h2>
                <p className="text-[var(--color-ink-soft)]">{t("app.accessibilityDesc")}</p>
              </div>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="agri-card p-6">
                  <span className="eyebrow mb-3 block">{t("app.tier1")}</span>
                  <h4 className="font-bold text-lg mb-2">{t("app.tier1Title")}</h4>
                  <p className="text-sm text-[var(--color-ink-soft)]">{t("app.tier1Desc")}</p>
                </div>
                <div className="agri-card p-6 bg-[var(--color-paper-deep)]/20">
                  <span className="eyebrow mb-3 block">{t("app.tier2")}</span>
                  <h4 className="font-bold text-lg mb-2">{t("app.tier2Title")}</h4>
                  <p className="text-sm text-[var(--color-ink-soft)]">{t("app.tier2Desc")}</p>
                </div>
                <div className="agri-card p-6">
                  <span className="eyebrow mb-3 block">{t("app.tier3")}</span>
                  <h4 className="font-bold text-lg mb-2">{t("app.tier3Title")}</h4>
                  <p className="text-sm text-[var(--color-ink-soft)]">{t("app.tier3Desc")}</p>
                </div>
                <div className="agri-card p-6 bg-[var(--color-paper-deep)]/20">
                  <span className="eyebrow mb-3 block">{t("app.tier4")}</span>
                  <h4 className="font-bold text-lg mb-2">{t("app.tier4Title")}</h4>
                  <p className="text-sm text-[var(--color-ink-soft)]">{t("app.tier4Desc")}</p>
                </div>
              </div>
            </section>

          </div>
        ) : activeTab === 'schemes' ? (
          <SchemesRecommendation />
        ) : activeTab === 'disease' ? (
          <DiseaseDetection />
        ) : (
          <WeatherDashboard />
        )}
      </main>

      {/* ── Closing CTA Band ── */}
      {activeTab === 'crop' && (
        <section className="container mx-auto px-4 py-12 max-w-6xl">
          <div className="rounded-2xl p-10 md:p-16 bg-gradient-to-br from-[var(--color-agri-green)] to-[var(--color-agri-green-deep)] text-center text-white shadow-xl relative overflow-hidden">
             <div className="absolute inset-0 opacity-10" style={{backgroundImage: 'radial-gradient(#fff 1px, transparent 1px)', backgroundSize: '20px 20px'}}></div>
             <div className="relative z-10 max-w-2xl mx-auto space-y-6">
               <h2 className="text-3xl md:text-4xl font-bold" style={{fontFamily: 'var(--font-display)'}}>{t("app.ctaTitle")}</h2>
               <p className="text-green-50 text-lg">{t("app.ctaDesc")}</p>
               <button className="bg-white text-[var(--color-agri-green-deep)] font-semibold py-3 px-8 rounded-lg mt-4 hover:bg-[var(--color-paper)] transition-colors shadow-lg" onClick={() => window.scrollTo({top: 0, behavior: 'smooth'})}>{t("app.ctaBtn")}</button>
             </div>
          </div>
        </section>
      )}

      {/* ── Footer ── */}
      <footer className="border-t border-[var(--color-border-line)] bg-[var(--color-paper-deep)]/30 mt-12">
        <div className="container mx-auto px-4 py-8 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="font-bold text-lg text-[var(--color-ink)]" style={{fontFamily: 'var(--font-display)'}}>{t("app.brandName")}</div>
          <p className="text-xs text-[var(--color-ink-soft)]">
            {t("app.footerDisclaimer")}
          </p>
        </div>
      </footer>

      {/* ── Chat Widget ── */}
      <ChatWidget />
    </div>
  );
}
