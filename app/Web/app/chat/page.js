"use client";
import { useEffect, useRef, useState } from "react";
import Shell from "../../components/Shell";
import { api } from "../../lib/api";

export default function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");
  const endRef = useRef(null);

  useEffect(() => {
    api.messages().then((d) => setMessages(d.items)).catch(() => {});
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, toast]);

  async function send(e) {
    e.preventDefault();
    const content = input.trim();
    if (!content || busy) return;
    setError("");
    setToast("");
    setInput("");
    setMessages((m) => [...m, { id: `tmp-${Date.now()}`, role: "user", content }]);
    setBusy(true);
    try {
      const res = await api.sendMessage(content);
      setMessages((m) => [...m, res.message]);
      const added = (res.actions || []).filter((a) => a.type === "vocabulary_added");
      if (added.length) {
        setToast(`Added ${added.map((a) => a.term).join(", ")} to your vocabulary`);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function clearChat() {
    if (!confirm("Clear the conversation? Your memory (facts/summary) is kept.")) return;
    await api.clearChat();
    setMessages([]);
  }

  return (
    <Shell>
      <div className="row between">
        <h1>Chat</h1>
        <button className="ghost" onClick={clearChat}>Clear conversation</button>
      </div>
      <div className="chat-list">
        {messages.length === 0 && <p className="muted">Say hello to your coach to get started.</p>}
        {messages.map((m) => (
          <div key={m.id} className={`bubble ${m.role}`}>{m.content}</div>
        ))}
        {busy && <div className="bubble assistant muted">…</div>}
        {toast && <div className="toast">✓ {toast}</div>}
        {error && <div className="error">{error}</div>}
        <div ref={endRef} />
      </div>
      <form className="composer" onSubmit={send}>
        <textarea
          rows={2}
          placeholder="Type a message…  (Enter to send, Shift+Enter for newline)"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(e); }
          }}
        />
        <button disabled={busy || !input.trim()}>Send</button>
      </form>
    </Shell>
  );
}
