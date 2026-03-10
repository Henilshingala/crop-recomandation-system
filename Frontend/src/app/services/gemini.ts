/**
 * Gemini AI Service for Farmer Assistant
 *
 * ⚠️  SECURITY WARNING: This API key is exposed in client-side code.
 *     For production, proxy requests through your Django backend instead.
 */

const GEMINI_API_KEY = "AIzaSyCEgWrjAG0CKWrhK2t9N0mKpTvKLJp9MNA";
const GEMINI_API_URL =
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent";

export interface ChatMessage {
  role: "user" | "model";
  text: string;
}

const LANGUAGE_MAP: Record<string, string> = {
  en: "English",
  as: "Assamese",
  bn: "Bengali",
  brx: "Bodo",
  doi: "Dogri",
  gu: "Gujarati",
  hi: "Hindi",
  kn: "Kannada",
  ks: "Kashmiri",
  gom: "Konkani",
  mai: "Maithili",
  ml: "Malayalam",
  mni: "Manipuri",
  mr: "Marathi",
  ne: "Nepali",
  or: "Odia",
  pa: "Punjabi",
  sa: "Sanskrit",
  sat: "Santali",
  sd: "Sindhi",
  ta: "Tamil",
  te: "Telugu",
  ur: "Urdu",
};

function getLanguageName(code: string): string {
  return LANGUAGE_MAP[code] || "English";
}

function buildSystemPrompt(langCode: string): string {
  const lang = getLanguageName(langCode);
  return `You are "Krishi Mitra" (Farm Friend), an expert AI farming assistant for Indian farmers.

RULES:
1. You MUST reply ONLY in ${lang} language. Every word of your response must be in ${lang}.
2. You are specialized in agriculture, farming, crops, soil health, irrigation, pest control, weather, government schemes for farmers, organic farming, and related topics.
3. Give practical, actionable advice suited to Indian farming conditions.
4. Keep answers concise but helpful (2-4 paragraphs max).
5. If someone asks something unrelated to farming/agriculture, politely redirect them to farming topics — still in ${lang}.
6. Use simple language that a farmer can understand easily.
7. When discussing crops, mention seasons, soil types, and regional suitability when relevant.`;
}

export async function askGemini(
  userMessage: string,
  history: ChatMessage[],
  langCode: string,
): Promise<string> {
  const systemPrompt = buildSystemPrompt(langCode);

  const contents = [
    { role: "user", parts: [{ text: systemPrompt }] },
    { role: "model", parts: [{ text: getLanguageName(langCode) === "English"
        ? "I understand. I am Krishi Mitra, your farming assistant. I will respond only in English. How can I help you today?"
        : `समझ गया। मैं कृषि मित्र हूँ। मैं ${getLanguageName(langCode)} में जवाब दूंगा।` }] },
    ...history.map((msg) => ({
      role: msg.role === "user" ? "user" as const : "model" as const,
      parts: [{ text: msg.text }],
    })),
    { role: "user" as const, parts: [{ text: userMessage }] },
  ];

  const response = await fetch(`${GEMINI_API_URL}?key=${GEMINI_API_KEY}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      contents,
      generationConfig: {
        temperature: 0.7,
        topP: 0.9,
        maxOutputTokens: 1024,
      },
    }),
  });

  if (!response.ok) {
    const err = await response.text();
    throw new Error(`Gemini API error (${response.status}): ${err}`);
  }

  const data = await response.json();
  const text =
    data?.candidates?.[0]?.content?.parts?.[0]?.text;

  if (!text) throw new Error("Empty response from Gemini");
  return text;
}
