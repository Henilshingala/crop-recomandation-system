import { useState } from "react";
import { InputForm } from "@/app/components/InputForm";
import { ResultsSection } from "@/app/components/ResultsSection";
import { Sprout, Wheat, Loader2 } from "lucide-react";
import { getPrediction, type PredictionResponse } from "@/app/services/api";

export default function App() {
  const [results, setResults] = useState<PredictionResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setResults(null);

    const form = e.target as HTMLFormElement;
    const fd = new FormData(form);

    const input = {
      N: parseFloat(fd.get('nitrogen') as string),
      P: parseFloat(fd.get('phosphorus') as string),
      K: parseFloat(fd.get('potassium') as string),
      temperature: parseFloat(fd.get('temperature') as string),
      humidity: parseFloat(fd.get('humidity') as string),
      ph: parseFloat(fd.get('ph') as string),
      rainfall: parseFloat(fd.get('rainfall') as string),
    };

    try {
      const response = await getPrediction(input);
      if (response && response.top_1 && response.top_3) {
        setResults(response);
      } else {
        throw new Error('Invalid response structure from API');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get recommendations';
      setError(errorMessage);
      setResults(null);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md shadow-md border-b-4 border-green-600">
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
          <InputForm onSubmit={handleSubmit} isLoading={isLoading} />

          {isLoading && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 text-green-600 animate-spin" />
              <span className="ml-3 text-lg text-gray-600">Analyzing your soil data...</span>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
              <p className="font-semibold">Error</p>
              <p>{error}</p>
              <p className="text-sm mt-2">Make sure the backend server is reachable. If you're running locally, ensure Django is started.</p>
            </div>
          )}

          {results && !isLoading && <ResultsSection data={results} />}

          {!results && !isLoading && (
            <div className="bg-white/80 backdrop-blur-sm rounded-lg shadow-md p-6 border-l-4 border-green-600">
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

      <footer className="bg-green-800 text-white mt-16 py-6">
        <div className="container mx-auto px-4 text-center">
          <p className="text-sm">
            &copy; 2026 Crop Recommendation System &bull; Empowering farmers with data-driven decisions
          </p>
        </div>
      </footer>
    </div>
  );
}
