import { useState, useRef, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { X, Send, Loader2, Trash2, Bot, User } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import { askAssistant, type ChatMessage } from "@/app/services/assistant";

/* ── Leaf SVG icon for FAB ─────────────────────────────────────────── */
function LeafIcon() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M11 20A7 7 0 0 1 9.8 6.9C15.5 4.9 17 3.5 19 2c1 2 2 4.5 2 8 0 5.5-4.78 10-10 10Z" />
      <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12" />
    </svg>
  );
}

/* ── Animation variants ────────────────────────────────────────────── */
const panelVariants = {
  hidden: { opacity: 0, y: 80, scale: 0.95 },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { type: "spring" as const, stiffness: 300, damping: 28, mass: 0.8 },
  },
  exit: {
    opacity: 0,
    y: 60,
    scale: 0.95,
    transition: { duration: 0.2, ease: "easeIn" as const },
  },
};

const messageVariants = {
  hidden: { opacity: 0, y: 12, scale: 0.96 },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { type: "spring" as const, stiffness: 400, damping: 25 },
  },
};

const fabVariants = {
  hidden: { opacity: 0, scale: 0 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: { type: "spring" as const, stiffness: 400, damping: 15 },
  },
  exit: { opacity: 0, scale: 0, transition: { duration: 0.15 } },
  tap: { scale: 0.9 },
};

const backdropVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { duration: 0.2 } },
  exit: { opacity: 0, transition: { duration: 0.15 } },
};

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
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 350);
    }
  }, [open]);

  const handleSend = useCallback(async () => {
    const text = input.trim();
    if (!text || loading) return;

    setInput("");
    const userMsg: ChatMessage = { role: "user", text };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const reply = await askAssistant(text, messages, i18n.language);
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

  const suggestions = t("assistant.suggestions", { returnObjects: true }) as string[];
  const suggestionsEn = t("assistant.suggestionsEn", { returnObjects: true }) as string[];

  return (
    <>
      {/* ── Floating Action Button ── */}
      <AnimatePresence>
        {!open && (
          <motion.button
            key="fab"
            variants={fabVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            whileTap="tap"
            onClick={() => setOpen(true)}
            className="chat-fab"
            aria-label={t("assistant.open")}
          >
            <LeafIcon />
            <span className="chat-fab-pulse" />
          </motion.button>
        )}
      </AnimatePresence>

      {/* ── Chat Panel ── */}
      <AnimatePresence>
        {open && (
          <>
            {/* Mobile backdrop */}
            <motion.div
              key="backdrop"
              className="chat-backdrop"
              variants={backdropVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
              onClick={() => setOpen(false)}
            />

            <motion.div
              key="panel"
              className="chat-panel"
              variants={panelVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
            >
              {/* Header */}
              <div className="chat-header">
                <div className="chat-header-info">
                  <div className="chat-header-avatar">
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <div className="chat-header-title">
                      {t("assistant.title")}
                    </div>
                    <div className="chat-header-subtitle">
                      {t("assistant.subtitle")}
                    </div>
                  </div>
                </div>
                <div className="chat-header-actions">
                  {messages.length > 0 && (
                    <button
                      onClick={clearChat}
                      className="chat-header-btn"
                      aria-label={t("assistant.clear")}
                      title={t("assistant.clear")}
                    >
                      <Trash2 className="w-4.5 h-4.5" />
                    </button>
                  )}
                  <button
                    onClick={() => setOpen(false)}
                    className="chat-header-btn"
                    aria-label={t("assistant.close")}
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* Messages */}
              <div ref={scrollRef} className="chat-messages">
                {messages.length === 0 && !loading && (
                  <motion.div
                    className="chat-welcome"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.15, duration: 0.4 }}
                  >
                    <div className="chat-welcome-icon">
                      <Bot className="w-8 h-8 text-emerald-600" />
                    </div>
                    <p className="chat-welcome-text">
                      {t("assistant.welcome")}
                    </p>
                    <div className="chat-suggestions">
                      {suggestions.map((s: string, i: number) => (
                        <motion.button
                          key={i}
                          className="chat-suggestion-btn"
                          onClick={() => { setInput(suggestionsEn[i] ?? s); inputRef.current?.focus(); }}
                          initial={{ opacity: 0, x: 20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: 0.25 + i * 0.08 }}
                          whileTap={{ scale: 0.95 }}
                        >
                          {s}
                        </motion.button>
                      ))}
                    </div>
                  </motion.div>
                )}

                <AnimatePresence mode="popLayout">
                  {messages.map((msg, idx) => (
                    <motion.div
                      key={idx}
                      variants={messageVariants}
                      initial="hidden"
                      animate="visible"
                      layout
                      className={`chat-bubble ${msg.role === "user" ? "chat-bubble-user" : "chat-bubble-bot"}`}
                    >
                      <div className={`chat-avatar ${msg.role === "user" ? "chat-avatar-user" : "chat-avatar-bot"}`}>
                        {msg.role === "user" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                      </div>
                      <div className={`chat-msg ${msg.role === "user" ? "chat-msg-user" : "chat-msg-bot"} ${msg.role === "model" ? "chat-msg-bot-glow" : ""}`}>
                        {msg.text}
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>

                {/* Typing indicator */}
                <AnimatePresence>
                  {loading && (
                    <motion.div
                      className="chat-bubble chat-bubble-bot"
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -5 }}
                      transition={{ duration: 0.2 }}
                    >
                      <div className="chat-avatar chat-avatar-bot">
                        <Bot className="w-4 h-4" />
                      </div>
                      <div className="chat-msg chat-msg-bot">
                        <div className="flex gap-1.5 items-center py-1">
                          <span className="chat-typing-dot" />
                          <span className="chat-typing-dot" />
                          <span className="chat-typing-dot" />
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
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
                <motion.button
                  onClick={handleSend}
                  disabled={!input.trim() || loading}
                  className="chat-send-btn"
                  aria-label={t("assistant.send")}
                  whileTap={{ scale: 0.85 }}
                >
                  {loading ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <Send className="w-5 h-5" />
                  )}
                </motion.button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
