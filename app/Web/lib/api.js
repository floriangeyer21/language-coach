"use client";
// Thin client for the LanguageCoach API. Token stored in localStorage.

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";
const TOKEN_KEY = "lc_token";

export function getToken() {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}
export function setToken(t) {
  window.localStorage.setItem(TOKEN_KEY, t);
}
export function clearToken() {
  window.localStorage.removeItem(TOKEN_KEY);
}

async function request(path, { method = "GET", body, auth = true } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth) {
    const t = getToken();
    if (t) headers["Authorization"] = `Bearer ${t}`;
  }
  const res = await fetch(`${BASE}/api${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = data?.error || { code: "error", message: `HTTP ${res.status}` };
    throw new Error(err.message || err.code);
  }
  return data;
}

export const api = {
  // auth
  register: (b) => request("/auth/register", { method: "POST", body: b, auth: false }),
  login: (b) => request("/auth/login", { method: "POST", body: b, auth: false }),
  me: () => request("/users/me"),
  updateMe: (b) => request("/users/me", { method: "PATCH", body: b }),
  // chat
  messages: () => request("/chat/messages?limit=200"),
  sendMessage: (content) => request("/chat/messages", { method: "POST", body: { content } }),
  clearChat: () => request("/chat/messages", { method: "DELETE" }),
  // memory
  getMemory: () => request("/memory"),
  setSummary: (summary) => request("/memory/summary", { method: "PUT", body: { summary } }),
  addFact: (text) => request("/memory/facts", { method: "POST", body: { text } }),
  deleteFact: (id) => request(`/memory/facts/${id}`, { method: "DELETE" }),
  wipeMemory: () => request("/memory", { method: "DELETE" }),
  // vocabulary
  groups: () => request("/vocabulary/groups"),
  createGroup: (name) => request("/vocabulary/groups", { method: "POST", body: { name } }),
  deleteGroup: (id) => request(`/vocabulary/groups/${id}`, { method: "DELETE" }),
  words: (groupId) => request(`/vocabulary/words${groupId ? `?group_id=${groupId}` : ""}`),
  createWord: (b) => request("/vocabulary/words", { method: "POST", body: b }),
  updateWord: (id, b) => request(`/vocabulary/words/${id}`, { method: "PATCH", body: b }),
  deleteWord: (id) => request(`/vocabulary/words/${id}`, { method: "DELETE" }),
  review: (groupId) => request(`/vocabulary/groups/${groupId}/review`),
};
