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