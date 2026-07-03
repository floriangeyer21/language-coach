"use client";
import { useEffect, useState } from "react";
import Shell from "../../components/Shell";
import { api } from "../../lib/api";

export default function VocabularyPage() {
  const [groups, setGroups] = useState([]);
  const [activeGroup, setActiveGroup] = useState(null);
  const [words, setWords] = useState([]);
  const [term, setTerm] = useState("");
  const [translation, setTranslation] = useState("");
  const [newGroup, setNewGroup] = useState("");
  const [error, setError] = useState("");
  const [reviewing, setReviewing] = useState(false);

  async function loadGroups() {
    const d = await api.groups();
    setGroups(d.items);
    if (!activeGroup && d.items.length) setActiveGroup(d.items[0].id);
    return d.items;
  }

  async function loadWords(gid) {
    const d = await api.words(gid);
    setWords(d.items);
  }

  useEffect(() => { loadGroups(); }, []);
  useEffect(() => { if (activeGroup) loadWords(activeGroup); }, [activeGroup]);

  async function addWord(e) {
    e.preventDefault();
    setError("");
    if (!term.trim()) return;
    try {
      await api.createWord({ term: term.trim(), translation: translation.trim() || null, group_id: activeGroup });
      setTerm(""); setTranslation("");
      await loadWords(activeGroup);
      await loadGroups();
    } catch (err) { setError(err.message); }
  }

  async function addGroup(e) {
    e.preventDefault();
    setError("");
    if (!newGroup.trim()) return;
    try {
      const g = await api.createGroup(newGroup.trim());
      setNewGroup("");
      await loadGroups();
      setActiveGroup(g.id);
    } catch (err) { setError(err.message); }
  }

  async function removeWord(id) {
    await api.deleteWord(id);
    await loadWords(activeGroup);
    await loadGroups();
  }

  async function removeGroup(g) {
    if (g.is_default) return;
    if (!confirm(`Delete "${g.name}"? Its words move to your default group.`)) return;
    await api.deleteGroup(g.id);
    const gs = await loadGroups();
    setActiveGroup(gs[0]?.id || null);
  }

  const current = groups.find((g) => g.id === activeGroup);

  if (reviewing && current) {
    return <Shell><Review group={current} onExit={() => setReviewing(false)} /></Shell>;
  }

  return (
    <Shell>
      <h1>Vocabulary</h1>

      <div className="row" style={{ flexWrap: "wrap", gap: 6, marginBottom: 16 }}>
        {groups.map((g) => (
          <button key={g.id}
            className={g.id === activeGroup ? "" : "secondary"}
            onClick={() => setActiveGroup(g.id)}>
            {g.name} ({g.word_count})
          </button>
        ))}
      </div>

      <form className="row" onSubmit={addGroup} style={{ marginBottom: 20 }}>
        <input placeholder="New group name" value={newGroup} onChange={(e) => setNewGroup(e.target.value)} />
        <button className="secondary">Add group</button>
      </form>

      {current && (
        <div className="card stack">
          <div className="row between">
            <h2 style={{ margin: 0 }}>{current.name}</h2>
            <div className="row">
              <button onClick={() => setReviewing(true)} disabled={!words.length}>Review ▶</button>
              {!current.is_default && <button className="danger" onClick={() => removeGroup(current)}>Delete group</button>}
            </div>
          </div>

          <form className="row" onSubmit={addWord}>
            <input placeholder="Word (learning language)" value={term} onChange={(e) => setTerm(e.target.value)} />
            <input placeholder="English (optional, auto-translated)" value={translation} onChange={(e) => setTranslation(e.target.value)} />
            <button>Add</button>
          </form>
          {error && <div className="error">{error}</div>}

          <div>
            {words.length === 0 && <p className="muted">No words yet in this group.</p>}
            {words.map((w) => (
              <div className="word-row" key={w.id}>
                <div><strong>{w.term}</strong> <span className="muted">— {w.translation}</span></div>
                <button className="ghost" onClick={() => removeWord(w.id)}>✕</button>
              </div>
            ))}
          </div>
        </div>
      )}
    </Shell>
  );
}

function Review({ group, onExit }) {
  const [cards, setCards] = useState([]);
  const [idx, setIdx] = useState(0);
  const [flipped, setFlipped] = useState(false);

  useEffect(() => {
    api.review(group.id).then((d) => setCards(d.cards)).catch(() => {});
  }, [group.id]);

  if (!cards.length) return <p className="muted">Loading cards…</p>;

  const card = cards[idx];
  function next() { setFlipped(false); setIdx((i) => (i + 1) % cards.length); }

  return (
    <div>
      <div className="row between">
        <h1>Review — {group.name}</h1>
        <button className="ghost" onClick={onExit}>✕ Exit</button>
      </div>
      <p className="muted center">{idx + 1} / {cards.length}</p>
      <div className={`flashcard ${flipped ? "flipped" : ""}`} onClick={() => setFlipped((f) => !f)}>
        <div className="flashcard-inner">
          <div className="flashcard-face front">{card.front}</div>
          <div className="flashcard-face back">{card.back}</div>
        </div>
      </div>
      <div className="row center" style={{ justifyContent: "center", gap: 12 }}>
        <button className="secondary" onClick={() => setFlipped((f) => !f)}>Flip</button>
        <button onClick={next}>Next ▶</button>
      </div>
      <p className="muted center" style={{ marginTop: 12 }}>Click the card or Flip to reveal.</p>
    </div>
  );
}
