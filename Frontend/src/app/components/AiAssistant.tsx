import { useState, useRef, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { MessageCircle, X, Send, Loader2, Trash2, Bot, User } from "lucide-react";
import { askGemini, type ChatMessage } from "@/app/services/gemini";

export function AiAssistant() {
  const { t, i18n } = useTranslation();
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading]);

  // focus input when opened
  useEffect(() => {
    if (open) inputRef.current?.focus();
  }, [open]);

  const handleSend = useCallback(async () => {
    const text = input.trim();
    if (!text || loading) return;

    setInput("");
    const userMsg: ChatMessage = { role: "user", text };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const reply = await askGemini(text, messages, i18n.language);
      setMessages((prev) => [...prev, { role: "model", text: reply }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "model", text: t("assistant.error") },
      ]);
    } finally {
      setLoading(false);
    }
  }, [input, loading, messages, i18n.language, t]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const clearChat = () => {
    setMessages([]);
  };

  return (
    <>
      {/* ── Floating Action Button ── */}
      {!open && (
        <button
          onClick={() => setOpen(true)}
          className="chat-fab"
          aria-label={t("assistant.open")}
        >
          <MessageCircle className="w-6 h-6" />
          <span className="chat-fab-pulse" />
        </button>
      )}

      {/* ── Chat Panel ── */}
      {open && (
        <div className="chat-panel animate-chat-in">
          {/* Header */}
          <div className="chat-header">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-white/20 flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="text-white font-semibold text-sm leading-tight">
                  {t("assistant.title")}
                </h3>
                <p className="text-emerald-100/70 text-[10px]">
                  {t("assistant.subtitle")}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              {messages.length > 0 && (
                <button
                  onClick={clearChat}
                  className="p-1.5 rounded-lg hover:bg-white/15 transition-colors"
                  aria-label={t("assistant.clear")}
                  title={t("assistant.clear")}
                >
                  <Trash2 className="w-4 h-4 text-white/70" />
                </button>
              )}
              <button
                onClick={() => setOpen(false)}
                className="p-1.5 rounded-lg hover:bg-white/15 transition-colors"
                aria-label={t("assistant.close")}
              >
                <X className="w-4 h-4 text-white/70" />
              </button>
            </div>
          </div>

          {/* Messages */}
          <div ref={scrollRef} className="chat-messages">
            {messages.length === 0 && !loading && (
              <div className="flex flex-col items-center justify-center h-full text-center px-4 gap-3">
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-emerald-100 to-teal-100 flex items-center justify-center">
                  <Bot className="w-7 h-7 text-emerald-600" />
                </div>
                <p className="text-gray-500 text-sm leading-relaxed max-w-[220px]">
                  {t("assistant.welcome")}
                </p>
                <div className="flex flex-wrap justify-center gap-1.5 mt-1">
                  {(t("assistant.suggestions", { returnObjects: true }) as string[]).map(
                    (s: string, i: number) => (
                      <button
                        key={i}
                        onClick={() => { setInput(s); inputRef.current?.focus(); }}
                        className="text-[11px] px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 hover:bg-emerald-100 transition-colors border border-emerald-200/60"
                      >
                        {s}
                      </button>
                    ),
                  )}
                </div>
              </div>
            )}

            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`chat-bubble ${msg.role === "user" ? "chat-bubble-user" : "chat-bubble-bot"}`}
              >
                <div className={`chat-avatar ${msg.role === "user" ? "chat-avatar-user" : "chat-avatar-bot"}`}>
                  {msg.role === "user" ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
                </div>
                <div className={`chat-msg ${msg.role === "user" ? "chat-msg-user" : "chat-msg-bot"}`}>
                  {msg.text}
                </div>
              </div>
            ))}

            {loading && (
              <div className="chat-bubble chat-bubble-bot">
                <div className="chat-avatar chat-avatar-bot">
                  <Bot className="w-3.5 h-3.5" />
                </div>
                <div className="chat-msg chat-msg-bot">
                  <div className="flex gap-1.5 items-center py-1">
                    <span className="chat-typing-dot" />
                    <span className="chat-typing-dot delay-150" />
                    <span className="chat-typing-dot delay-300" />
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Input */}
          <div className="chat-input-bar">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={t("assistant.placeholder")}
              rows={1}
              className="chat-textarea"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || loading}
              className="chat-send-btn"
              aria-label={t("assistant.send")}
            >
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </button>
          </div>
        </div>
      )}
    </>
  );
}
