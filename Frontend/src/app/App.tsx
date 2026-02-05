import { useState } from "react";
import { InputForm } from "@/app/components/InputForm";
import { ResultsSection } from "@/app/components/ResultsSection";
import { Sprout, Wheat } from "lucide-react";

export default function App() {
  const [showResults, setShowResults] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: Backend API call will go here
    setShowResults(true);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50">
      {/* Header */}
      <header className="bg-white shadow-md border-b-4 border-green-600">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-center gap-4">
            <div className="bg-green-600 p-3 rounded-full">
              <Wheat className="w-8 h-8 text-white" />
            </div>
            <div className="text-center">
              <h1 className="text-4xl font-bold text-gray-900">Crop Recommendation System</h1>
              <p className="text-gray-600 mt-1">Smart farming decisions based on soil and climate analysis</p>
            </div>
            <div className="bg-green-600 p-3 rounded-full">
              <Sprout className="w-8 h-8 text-white" />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8 max-w-6xl">
        <div className="space-y-8">
          {/* Input Form */}
          <InputForm onSubmit={handleSubmit} />

          {/* Results Section - Hidden until submission */}
          {showResults && <ResultsSection />}

          {/* Info Section */}
          {!showResults && (
            <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-green-600">
              <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <Sprout className="w-5 h-5 text-green-600" />
                How It Works
              </h3>
              <div className="text-sm text-gray-700 space-y-2">
                <p>
                  Our intelligent system analyzes your soil nutrients (N, P, K), environmental conditions (temperature, humidity, rainfall), 
                  and soil pH to recommend the most suitable crop for your field.
                </p>
                <p className="pt-2">
                  <strong>Get started:</strong> Fill in the form above with your field measurements and click the submit button to receive 
                  personalized crop recommendations along with cultivation tips and expected yield information.
                </p>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-green-800 text-white mt-16 py-6">
        <div className="container mx-auto px-4 text-center">
          <p className="text-sm">
            © 2026 Crop Recommendation System • Empowering farmers with data-driven decisions
          </p>
        </div>
      </footer>
    </div>
  );
}
