import { useState, useRef, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { askAssistant, type ChatResponse } from "@/app/services/assistant";

/* ── Types ──────────────────────────────────────────────────────────── */

interface Message {
  id: string;
  text: string;
  sender: "user" | "bot";
  matched?: boolean;
  score?: number;
  isError?: boolean;
  timestamp: Date;
}

/* ── Component ──────────────────────────────────────────────────────── */

export default function ChatWidget() {
  const { t, i18n } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  const sendMessage = async () => {
    const question = inputText.trim();
    if (!question || isLoading) return;

    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {}
      setIsRecording(false);
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      text: question,
      sender: "user",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputText("");
    setIsLoading(true);

    try {
      // Use the i18n language code (strip region if present)
      const langCode = (i18n.language || "en").split("-")[0];

      const response: ChatResponse = await askAssistant(question, langCode);

      let botText = "";
      let isError = false;

      if (response.error) {
        botText = t("chat.serverError");
        isError = true;
      } else if (!response.answer) {
        botText = t("chat.emptyResponse");
        isError = true;
      } else {
        botText = response.answer;
        if (!response.matched) {
          botText += `\n\n${t("chat.savedForReview")}`;
        }
      }

      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: botText,
        sender: "bot",
        matched: response.matched,
        score: response.score,
        isError,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch {
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: t("chat.serverError"),
        sender: "bot",
        isError: true,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, botMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const [isRecording, setIsRecording] = useState(false);
  const recognitionRef = useRef<any>(null);

  const startRecording = () => {
    // If already recording, stop it (toggle behavior)
    if (isRecording && recognitionRef.current) {
      recognitionRef.current.stop();
      return;
    }

    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Speech recognition is not supported in this browser.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognitionRef.current = recognition;
    recognition.lang = i18n.language || "en-US";
    recognition.continuous = true;
    recognition.interimResults = true; 
    
    // We clear the input box on new recording for a clean experience
    setInputText("");

    recognition.onstart = () => setIsRecording(true);
    
    recognition.onresult = (event: any) => {
      let currentTranscript = '';
      for (let i = 0; i < event.results.length; i++) {
        currentTranscript += event.results[i][0].transcript;
      }
      // Completely replace the text with the current session's transcript
      setInputText(currentTranscript);
    };

    recognition.onerror = (event: any) => {
      console.error("Speech recognition error", event.error);
      setIsRecording(false);
    };

    recognition.onend = () => setIsRecording(false);

    recognition.start();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="chat-widget-container">
      {/* ── Chat Panel ─────────────────────────────────────────── */}
      {isOpen && (
        <div className="chat-panel">
          {/* Header */}
          <div className="chat-header">
            <span className="chat-header-icon">🌾</span>
            <span className="chat-header-title">{t("chat.title")}</span>
            <button
              className="chat-close-btn"
              onClick={() => setIsOpen(false)}
              aria-label={t("chat.closeChat")}
            >
              ✕
            </button>
          </div>

          {/* Messages */}
          <div className="chat-messages">
            {messages.length === 0 && (
              <div className="chat-empty-state">
                <span>🌱</span>
                <p>{t("chat.placeholder")}</p>
              </div>
            )}
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`chat-message ${
                  msg.sender === "user"
                    ? "chat-message-user"
                    : msg.isError
                    ? "chat-message-error"
                    : msg.matched === false
                    ? "chat-message-unmatched"
                    : "chat-message-bot"
                }`}
              >
                <div className="chat-message-text">{msg.text}</div>
                {msg.sender === "bot" &&
                  msg.score !== undefined &&
                  msg.matched &&
                  import.meta.env.DEV && (
                    <div className="chat-message-score">
                      Score: {(msg.score * 100).toFixed(0)}%
                    </div>
                  )}
              </div>
            ))}
            {isLoading && (
              <div className="chat-message chat-message-bot">
                <div className="chat-typing">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="chat-input-area" style={{ display: 'flex', alignItems: 'center' }}>
            <button
              className={`chat-mic-btn ${isRecording ? "recording" : ""}`}
              onClick={startRecording}
              disabled={isLoading}
              title="Speak"
              style={{
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                fontSize: '1.2rem',
                padding: '0 8px',
                color: isRecording ? '#ef4444' : '#6b7280',
                transition: 'color 0.2s'
              }}
              aria-label="Voice input"
            >
              🎤
            </button>
            <input
              ref={inputRef}
              type="text"
              className="chat-input"
              style={{ flex: 1 }}
              placeholder={t("chat.placeholder")}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
            />
            <button
              className="chat-send-btn"
              onClick={sendMessage}
              disabled={isLoading || !inputText.trim()}
              aria-label={t("chat.send")}
            >
              ➤
            </button>
          </div>
        </div>
      )}

      {/* ── Floating Bubble ────────────────────────────────────── */}
      <button
        className={`chat-bubble-btn ${isOpen ? "chat-bubble-open" : ""}`}
        onClick={() => setIsOpen(!isOpen)}
        aria-label={isOpen ? t("chat.closeChat") : t("chat.openChat")}
      >
        {isOpen ? "✕" : "🌾"}
      </button>
    </div>
  );
}
