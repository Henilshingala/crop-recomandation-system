/**
 * AI Assistant Service
 * Sends user messages to the hybrid FAQ + OpenRouter backend.
 */

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ||
  "https://crop-recomandation-system.onrender.com/api"
).replace(/\/$/, "");

export interface ChatMessage {
  role: "user" | "model";
  text: string;
}

export async function askAssistant(
  userMessage: string,
  _history: ChatMessage[],
  langCode: string,
): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/assistant/chat/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: userMessage, lang: langCode }),
  });

  if (!response.ok) {
    const err = await response.text();
    throw new Error(`Assistant error (${response.status}): ${err}`);
  }

  const data = await response.json();
  const answer = data?.answer;

  if (!answer) throw new Error("Empty response from assistant");
  return answer;
}
