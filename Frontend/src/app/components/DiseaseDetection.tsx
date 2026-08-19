import { useState, useEffect } from "react";
import { Upload, AlertCircle, CheckCircle2, Stethoscope, Leaf } from "lucide-react";
import { useTranslation } from "react-i18next";

function ComputerVisionScanner() {
  const { t } = useTranslation();
  const [step, setStep] = useState(0);
  
  const steps = [
    t("disease.steps.step1"),
    t("disease.steps.step2"),
    t("disease.steps.step3"),
    t("disease.steps.step4"),
    t("disease.steps.step5")
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
    <div className="bg-[var(--color-paper-deep)] p-6 md:p-8 flex flex-col justify-center animate-fade-in relative overflow-hidden rounded-2xl border border-[var(--color-border-line)]">
      <div className="relative z-10 w-full mx-auto space-y-4">
        {steps.map((text, i) => (
          <div key={i} className={`flex items-center gap-3 transition-all duration-500 ${i === step ? 'opacity-100 translate-x-0' : i < step ? 'opacity-40 translate-x-0' : 'opacity-0 -translate-x-4'}`}>
            {i < step ? (
              <div className="w-5 h-5 rounded-full bg-[var(--color-green-deep)] flex items-center justify-center flex-shrink-0 shadow-sm">
                <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>
              </div>
            ) : i === step ? (
              <div className="w-5 h-5 border-2 border-[var(--color-mustard)]/30 border-t-[var(--color-mustard)] rounded-full animate-spin flex-shrink-0" />
            ) : (
              <div className="w-5 h-5 rounded-full border-2 border-[var(--color-border-line)] flex-shrink-0" />
            )}
            <p className={`text-sm ${i === step ? 'font-bold text-[var(--color-ink)]' : 'text-[var(--color-ink-soft)]'}`}>{text}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export function DiseaseDetection() {
  const { t } = useTranslation();
  const [image, setImage] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<{ disease: string; confidence: number; treatment: string } | null>(null);

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setImage(reader.result as string);
        setResult(null); // Reset previous result
      };
      reader.readAsDataURL(file);
    }
  };

  const analyzeImage = () => {
    if (!image) return;
    
    setIsAnalyzing(true);
    setResult(null);

    // Mock analysis delay to match the 5 steps of 700ms each
    setTimeout(() => {
      setIsAnalyzing(false);
      // Hardcoded mock result for demonstration
      setResult({
        disease: "Early Blight (Alternaria solani)",
        confidence: 94.5,
        treatment: "1. Remove and destroy infected leaves.\n2. Apply copper-based fungicide.\n3. Ensure proper spacing for air circulation."
      });
    }, 4000);
  };

  return (
    <div className="space-y-8 animate-fade-in-up pb-10">
      <div className="agri-card p-8">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-[var(--color-agri-green-deep)] rounded-full flex items-center justify-center mx-auto mb-4">
            <Stethoscope className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-3xl font-bold text-[var(--color-ink)]" style={{fontFamily: 'var(--font-display)'}}>{t("disease.title")}</h2>
          <p className="text-[var(--color-ink-soft)] mt-2">{t("disease.subtitle")}</p>
        </div>

        <div className="max-w-2xl mx-auto">
          {/* Upload Area */}
          {!image ? (
            <div className="border-2 border-dashed border-[var(--color-border-line)] rounded-2xl p-12 text-center hover:bg-[var(--color-paper-deep)] transition-colors cursor-pointer relative">
              <input 
                type="file" 
                accept="image/*" 
                onChange={handleImageUpload}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
              <Upload className="w-12 h-12 text-[var(--color-ink-soft)] mx-auto mb-4" />
              <p className="text-[var(--color-ink)] font-bold text-lg" style={{fontFamily: 'var(--font-display)'}}>{t("disease.uploadText")}</p>
              <p className="text-[var(--color-ink-soft)] text-sm mt-2">{t("disease.uploadFormat")}</p>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="relative rounded-2xl overflow-hidden border border-[var(--color-border-line)] shadow-sm">
                <img src={image} alt="Uploaded crop" className={`w-full h-64 object-cover transition-all duration-700 ${isAnalyzing ? 'brightness-75' : ''}`} />
                
                {isAnalyzing && (
                  <div className="absolute inset-0 z-10 pointer-events-none">
                    <div className="absolute inset-0 bg-[var(--color-green-deep)]/10 mix-blend-overlay"></div>
                    <div className="w-full h-0.5 bg-[var(--color-mustard)] shadow-[0_0_15px_var(--color-mustard)] animate-pulse absolute top-1/2 -translate-y-1/2"></div>
                  </div>
                )}

                {!isAnalyzing && (
                  <button 
                    onClick={() => { setImage(null); setResult(null); }}
                    className="absolute top-4 right-4 bg-[var(--color-paper)]/80 backdrop-blur px-3 py-1.5 rounded-lg text-sm font-medium text-[var(--color-ink)] hover:bg-[var(--color-paper)] shadow-sm border border-[var(--color-border-line)]"
                  >
                    {t("disease.changeImage")}
                  </button>
                )}
              </div>

              {isAnalyzing ? (
                <ComputerVisionScanner />
              ) : !result ? (
                <button 
                  onClick={analyzeImage}
                  className="btn-primary w-full py-4 flex items-center justify-center gap-2 text-lg"
                >
                  <Leaf className="w-5 h-5" />
                  {t("disease.analyzeBtn")}
                </button>
              ) : null}
            </div>
          )}

          {/* Results Area */}
          {result && (
            <div className="mt-8 p-6 bg-[var(--color-paper-deep)] rounded-2xl border border-[var(--color-border-line)] animate-fade-in">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center flex-shrink-0">
                  <AlertCircle className="w-6 h-6 text-red-600" />
                </div>
                <div className="flex-1">
                  <h3 className="text-2xl font-bold text-[var(--color-ink)]" style={{fontFamily: 'var(--font-display)'}}>{result.disease}</h3>
                  <div className="flex items-center gap-2 mt-2">
                    <CheckCircle2 className="w-4 h-4 text-[var(--color-green-deep)]" />
                    <span className="text-sm font-bold text-[var(--color-green-deep)]">
                      {t("disease.confidence")} {result.confidence}%
                    </span>
                  </div>
                  
                  <div className="mt-6 pt-6 border-t border-[var(--color-border-line)]">
                    <h4 className="eyebrow block mb-3">{t("disease.treatmentTitle")}</h4>
                    <div className="bg-[var(--color-paper)] p-4 rounded-xl border border-[var(--color-border-line)]">
                      <p className="text-[var(--color-ink)] whitespace-pre-line leading-relaxed">
                        {result.treatment}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
