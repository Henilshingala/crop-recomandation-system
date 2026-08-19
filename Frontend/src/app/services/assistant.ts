/**
 * AI Chat Assistant Service
 * Connects to Django backend chat endpoint
 */

import { API_BASE_URL } from "./api";

/* ── Types ──────────────────────────────────────────────────────────── */

export interface ChatMessage {
  role: "user" | "model";
  text: string;
}

export interface ChatResponse {
  answer: string;
  matched: boolean;
  score: number;
  matched_question?: string;
  language_used?: string;
  qna_key?: string;
  error?: string;
}

/* ── Fallback strings (per language, for network-level failures) ───── */

const FALLBACK: Record<string, string> = {
  en: "Sorry, I could not find an answer. Please try asking differently.",
  hi: "क्षमा करें, उत्तर नहीं मिला। कृपया अलग तरीके से पूछें।",
  gu: "માફ કરશો, જવાબ મળ્યો નહીં. કૃપા કરીને અલગ રીતે પૂછો.",
  mr: "माफ करा, उत्तर सापडले नाही.",
  ta: "மன்னிக்கவும், பதில் கிடைக்கவில்லை.",
  te: "క్షమించండి, సమాధానం దొరకలేదు.",
  kn: "ಕ್ಷಮಿಸಿ, ಉತ್ತರ ಸಿಗಲಿಲ್ಲ.",
  bn: "দুঃখিত, উত্তর পাওয়া যায়নি।",
  pa: "ਮਾਫ਼ ਕਰਨਾ, ਜਵਾਬ ਨਹੀਂ ਮਿਲਿਆ।",
  ml: "ക്ഷമിക്കണം, ഉത്തരം കിട്ടിയില്ല.",
  or: "ମାଫ କରନ୍ତୁ, ଉତ୍ତର ମିଳିଲାନି।",
  ur: "معذرت، جواب نہیں ملا۔",
  as: "দুঃখিত, উত্তৰ পোৱা নগ'ল।",
  ne: "माफ गर्नुहोस्, उत्तर भेटिएन।",
  sa: "क्षम्यताम्, उत्तरं न लब्धम्।",
  mai: "माफ करू, उत्तर नहि भेटल।",
  doi: "माफ़ करना, जवाब नेई मिलेया।",
  gom: "माफ करात, उत्तर मेळ्ळें नाय।",
  ks: "معاف کریو، جواب نہیں ملِیا۔",
  mni: "সরি, ꯄꯨꯛꯅꯤꯡ ꯄꯥꯝꯕꯤꯗꯦ।",
  sat: "ᱦᱚᱲᱚ, ᱡᱩᱣᱟᱹᱵ ᱵᱟᱹᱦᱤᱡ ᱠᱟᱱᱟ།",
  sd: "معاف ڪجو، جواب نه مليو.",
  brx: "माफ करनो, जोबाब नाथाय।",
};

/* ── API call ───────────────────────────────────────────────────────── */

export async function askAssistant(
  userInput: string,
  _history: ChatMessage[],
  language: string
): Promise<string>;
export async function askAssistant(
  userInput: string,
  language: string
): Promise<ChatResponse>;
export async function askAssistant(
  userInput: string,
  historyOrLang: ChatMessage[] | string,
  language?: string
): Promise<string | ChatResponse> {
  // Support both old (3-arg) and new (2-arg) signatures
  const isLegacy = Array.isArray(historyOrLang);
  const lang = isLegacy ? (language || "en") : (historyOrLang || "en");

  try {
    const res = await fetch(`${API_BASE_URL}/assistant/chat/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: userInput, lang: lang }),
    });

    if (!res.ok) throw new Error(`HTTP error: ${res.status}`);

    const data = await res.json();

    if (isLegacy) {
      // Legacy callers just expect a string answer
      return data.answer ?? FALLBACK[lang] ?? FALLBACK["en"];
    }

    return {
      answer: data.answer ?? "",
      matched: data.matched ?? false,
      score: data.score ?? 0,
      matched_question: data.matched_question,
      language_used: data.language_used,
      qna_key: data.qna_key,
    };
  } catch (err) {
    console.error("AI Assistant error:", err);

    if (isLegacy) {
      return FALLBACK[lang] ?? FALLBACK["en"];
    }

    return {
      answer: "",
      matched: false,
      score: 0,
      error: err instanceof Error ? err.message : "Unknown error",
    };
  }
}
