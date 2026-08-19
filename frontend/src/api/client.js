/**
 * api/client.js
 * 
 * Single source of truth for all API calls.
 * If the backend URL changes, change it here only.
 */

import axios from "axios";

const BASE_URL = "http://localhost:8000";

const api = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
});

// ── Indexes ──────────────────────────────────────────────────────────────────

export const fetchIndexes = () =>
  api.get("/indexes").then((r) => r.data.indexes);

export const fetchStatus = (name) =>
  api.get(`/status/${name}`).then((r) => r.data);

export const fetchRepoInfo = (name) =>
  api.get(`/repo-info/${name}`).then((r) => r.data);

export const startIndexing = (repoUrl, force = false) =>
  api.post("/index", { repo_url: repoUrl, force }).then((r) => r.data);

// ── Chat ─────────────────────────────────────────────────────────────────────

export const askQuestion = (question, indexName, history = [], topK = 5) =>
  api
    .post("/ask", { question, index_name: indexName, history, top_k: topK })
    .then((r) => r.data);

/**
 * Streaming variant of askQuestion — calls back incrementally instead of
 * resolving once with the full answer. axios doesn't support reading a
 * streamed response body, so this uses fetch() + a ReadableStream reader
 * directly, parsing the backend's Server-Sent Events by hand.
 */
export async function streamAsk(question, indexName, history = [], topK = 5, { onSources, onToken, onDone, onError }) {
  let response;
  try {
    response = await fetch(`${BASE_URL}/ask/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, index_name: indexName, history, top_k: topK }),
    });
  } catch (e) {
    onError?.(e.message || "Network error");
    return;
  }

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    onError?.(body.detail || `Request failed (${response.status})`);
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const frames = buffer.split("\n\n");
    buffer = frames.pop(); // last piece may be incomplete — keep for next chunk

    for (const frame of frames) {
      let event = "message";
      let data = "";
      for (const line of frame.split("\n")) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        else if (line.startsWith("data:")) data = line.slice(5).trim();
      }
      if (!data) continue;

      const parsed = JSON.parse(data);
      if (event === "sources") onSources?.(parsed);
      else if (event === "done") onDone?.();
      else if (event === "error") onError?.(parsed.detail);
      else onToken?.(parsed.token);
    }
  }
}

export const askMulti = (question, indexNames, history = [], topK = 3) =>
  api
    .post("/ask-multi", {
      question,
      index_names: indexNames,
      history,
      top_k: topK,
    })
    .then((r) => r.data);

// ── Review ───────────────────────────────────────────────────────────────────

export const reviewCode = (indexName, focus = "general") =>
  api.post("/review", { index_name: indexName, focus }).then((r) => r.data);

// ── Onboard ──────────────────────────────────────────────────────────────────

export const fetchOnboard = (indexName) =>
  api.post("/onboard", { index_name: indexName }).then((r) => r.data);

// ── Contribute ───────────────────────────────────────────────────────────────

export const fetchContributions = (indexName) =>
  api.post("/contribute", { index_name: indexName }).then((r) => r.data);