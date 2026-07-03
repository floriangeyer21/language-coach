"use client";
import { useEffect, useState } from "react";
import Shell from "../../components/Shell";
import { api } from "../../lib/api";

export default function MemoryPage() {
  const [memory, setMemory] = useState({ summary: "", facts: [] });
  const [summary, setSummary] = useState("");
  const [newFact, setNewFact] = useState("");
  const [saved, setSaved] = useState(false);

  async function load() {
    const d = await api.getMemory();
    setMemory(d);
    setSummary(d.summary || "");
  }
  useEffect(() => { load(); }, []);

  async function saveSummary() {
    await api.setSummary(summary);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
    load();
  }
  async function addFact(e) {
    e.preventDefault();
    if (!newFact.trim()) return;
    await api.addFact(newFact.trim());
    setNewFact("");
    load();
  }
  async function deleteFact(id) {
    await api.deleteFact(id);
    load();
  }
  async function wipe() {
    if (!confirm("Wipe all AI memory (summary + facts)? This cannot be undone.")) return;
    await api.wipeMemory();
    load();
  }

  return (
    <Shell>
      <div className="row between">
        <h1>Memory</h1>
        <button className="danger" onClick={wipe}>Reset memory</button>
      </div>
      <p className="muted">What your coach remembers about you. Edit freely — the AI keeps this updated automatically.</p>

      <div className="card stack" style={{ marginBottom: 20 }}>
        <h3 style={{ margin: 0 }}>Summary</h3>
        <textarea rows={5} value={summary} onChange={(e) => setSummary(e.target.value)}
          placeholder="No summary yet — it builds as you chat." />
        <div className="row">
          <button onClick={saveSummary}>Save summary</button>
          {saved && <span className="toast">✓ Saved</span>}
          {memory.summary_updated_at && <span className="muted" style={{ fontSize: 13 }}>
            updated {new Date(memory.summary_updated_at).toLocaleString()}
          </span>}
        </div>
      </div>

      <div className="card stack">
        <h3 style={{ margin: 0 }}>Facts</h3>
        <form className="row" onSubmit={addFact}>
          <input placeholder="Add a fact about yourself" value={newFact} onChange={(e) => setNewFact(e.target.value)} />
          <button className="secondary">Add</button>
        </form>
        {memory.facts.length === 0 && <p className="muted">No facts yet.</p>}
        {memory.facts.map((f) => (
          <div className="word-row" key={f.id}>
            <span>{f.text}</span>
            <button className="ghost" onClick={() => deleteFact(f.id)}>✕</button>
          </div>
        ))}
      </div>
    </Shell>
  );
}
