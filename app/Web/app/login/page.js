"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, setToken } from "../../lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState("login"); // "login" | "register"
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [language, setLanguage] = useState("German");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const res = mode === "login"
        ? await api.login({ email, password })
        : await api.register({ email, password, display_name: displayName, learning_language: language });
      setToken(res.access_token);
      router.replace("/chat");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="content" style={{ maxWidth: 420 }}>
      <h1>🗣️ LanguageCoach</h1>
      <p className="muted">{mode === "login" ? "Welcome back." : "Create your account."}</p>
      <form className="stack card" onSubmit={submit}>
        {mode === "register" && (
          <>
            <input placeholder="Display name" value={displayName}
              onChange={(e) => setDisplayName(e.target.value)} required />
            <input placeholder="Language you're learning (e.g. German)" value={language}
              onChange={(e) => setLanguage(e.target.value)} required />
          </>
        )}
        <input type="email" placeholder="Email" value={email}
          onChange={(e) => setEmail(e.target.value)} required />
        <input type="password" placeholder="Password" value={password}
          onChange={(e) => setPassword(e.target.value)} required minLength={6} />
        {error && <div className="error">{error}</div>}
        <button disabled={busy}>{busy ? "…" : mode === "login" ? "Log in" : "Sign up"}</button>
      </form>
      <p className="muted" style={{ marginTop: 16 }}>
        {mode === "login" ? "No account?" : "Already have an account?"}{" "}
        <a href="#" onClick={(e) => { e.preventDefault(); setError(""); setMode(mode === "login" ? "register" : "login"); }}>
          {mode === "login" ? "Sign up" : "Log in"}
        </a>
      </p>
    </div>
  );
}
