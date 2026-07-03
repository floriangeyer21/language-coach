"use client";
import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import Link from "next/link";
import { api, clearToken, getToken } from "../lib/api";

const NAV = [
  { href: "/chat", label: "Chat" },
  { href: "/vocabulary", label: "Vocabulary" },
  { href: "/memory", label: "Memory" },
];

export default function Shell({ children }) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    api.me().then(setUser).catch(() => {
      clearToken();
      router.replace("/login");
    }).finally(() => setReady(true));
  }, [router]);

  function logout() {
    clearToken();
    router.replace("/login");
  }

  if (!ready) return <div className="content muted">Loading…</div>;

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">🗣️ LanguageCoach</div>
        <nav>
          {NAV.map((n) => (
            <Link key={n.href} href={n.href}
              className={`navlink ${pathname === n.href ? "active" : ""}`}>
              {n.label}
            </Link>
          ))}
        </nav>
        <div className="account">
          {user && <div className="muted" style={{ padding: "4px 12px", fontSize: 14 }}>
            {user.display_name}<br />
            <span style={{ fontSize: 12 }}>learning {user.learning_language}</span>
          </div>}
          <button className="ghost" onClick={logout}>Log out</button>
        </div>
      </aside>
      <main className="main">
        <div className="content">{children}</div>
      </main>
    </div>
  );
}
