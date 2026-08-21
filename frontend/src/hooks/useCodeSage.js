/**
 * hooks/useCodeSage.js
 *
 * Custom hook that owns all app state and business logic.
 * App.jsx imports this and uses the returned values to render UI.
 *
 * Separation of concerns:
 *   useCodeSage  → what data exists, what actions are possible
 *   App.jsx      → how it looks
 */

import { useState, useEffect, useRef } from "react";
import * as api from "../api/client";
import { nameFromUrl, buildHistory, saveChatSession, loadChatSession } from "../utils/helpers";

export default function useCodeSage() {

  // ── State ───────────────────────────────────────────────────────────────────

  const [indexes, setIndexes]           = useState([]);
  const [activeIndex, setActiveIndex]   = useState(null);
  const [messages, setMessages]         = useState([]);
  const [input, setInput]               = useState("");
  const [loading, setLoading]           = useState(false);

  const [repoUrl, setRepoUrl]           = useState("");
  const [indexing, setIndexing]         = useState(false);
  const [indexMsg, setIndexMsg]         = useState("");

  const [multiMode, setMultiMode]       = useState(false);

  // Which tab is showing: "chat" | "onboard" | "review" | "contribute".
  // Switching tabs never loses data or re-fetches — it just changes what's visible.
  const [activeTab, setActiveTab] = useState("chat");

  const [onboardReport, setOnboardReport] = useState(null);
  const [onboarding, setOnboarding]       = useState(false);

  const [reviewData, setReviewData]     = useState(null);
  const [reviewFocus, setReviewFocus]   = useState("general");
  const [reviewing, setReviewing]       = useState(false);

  const [contributeData, setContributeData] = useState(null);
  const [contributing, setContributing]     = useState(false);

  const bottomRef = useRef(null);

  // ── Effects ─────────────────────────────────────────────────────────────────

  useEffect(() => { loadIndexes(); }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Restore chat history on reload, but only once it's still valid — the
  // saved index has to still exist. Onboard/review/contribute data isn't
  // persisted, just the chat itself.
  useEffect(() => {
    if (!activeIndex) return;
    saveChatSession(activeIndex, messages);
  }, [activeIndex, messages]);

  // ── Helpers ──────────────────────────────────────────────────────────────────

  function addSystemMsg(content) {
    setMessages((prev) => [...prev, { role: "system", content }]);
  }

  async function loadIndexes() {
    try {
      const list = await api.fetchIndexes();
      setIndexes(list);

      const saved = loadChatSession();
      if (saved && list.includes(saved.activeIndex)) {
        setActiveIndex(saved.activeIndex);
        setMessages(saved.messages);
      }
    } catch { /* backend not ready yet */ }
  }

  // ── Index selection ──────────────────────────────────────────────────────────

  function selectIndex(name) {
    setActiveIndex(name);
    setActiveTab("chat");
    setOnboardReport(null);
    setReviewData(null);
    setContributeData(null);
    setMessages([{ role: "system", content: `Switched to: ${name}` }]);
    loadOnboardReport(name);
  }

  // Pre-fill the chat input from any card's "ask about this" button and
  // switch to the Chat tab — the originating panel's data is never lost.
  function askAbout(q) {
    setActiveTab("chat");
    setInput(q);
  }

  // ── Indexing ─────────────────────────────────────────────────────────────────

  function pollIndexStatus(name) {
    const interval = setInterval(async () => {
      try {
        const { status, chunk_count } = await api.fetchStatus(name);
        if (status === "done") {
          clearInterval(interval);
          setIndexing(false);
          setIndexMsg("");
          await loadIndexes();
          selectIndex(name);
          addSystemMsg(`✅ Indexed ${chunk_count} chunks. Ready to chat.`);
        } else if (status === "error") {
          clearInterval(interval);
          setIndexing(false);
          setIndexMsg("❌ Indexing failed. Check the backend terminal.");
        } else {
          setIndexMsg("Indexing... hang tight");
        }
      } catch {
        clearInterval(interval);
        setIndexing(false);
      }
    }, 2000);
  }

  async function handleIndexSubmit() {
    if (!repoUrl.trim()) return;
    setIndexing(true);
    setIndexMsg("Starting...");
    const name = nameFromUrl(repoUrl);
    try {
      const result = await api.startIndexing(repoUrl.trim());
      if (result.status === "already_exists") {
        setIndexing(false);
        setIndexMsg("");
        await loadIndexes();
        selectIndex(name);
        addSystemMsg(`Index '${name}' already exists — loaded.`);
      } else {
        pollIndexStatus(name);
      }
    } catch (e) {
      setIndexing(false);
      setIndexMsg("❌ " + (e.response?.data?.detail || e.message));
    }
  }

  // ── Chat ─────────────────────────────────────────────────────────────────────

  function updateLastMessage(updater) {
    setMessages((prev) => {
      const next = [...prev];
      next[next.length - 1] = updater(next[next.length - 1]);
      return next;
    });
  }

  async function handleAsk() {
    const question = input.trim();
    if (!question || !activeIndex || loading) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setLoading(true);

    const history = buildHistory(messages);

    // Multi-repo search merges results from several indexes before
    // generating one answer — not streamed, kept as a single request.
    if (multiMode) {
      try {
        const data = await api.askMulti(question, indexes, history);
        setMessages((prev) => [...prev, {
          role: "assistant",
          content: data.answer,
          sources: data.sources,
        }]);
      } catch (e) {
        setMessages((prev) => [...prev, {
          role: "assistant",
          content: `❌ ${e.response?.data?.detail || "Something went wrong."}`,
          sources: [],
        }]);
      } finally {
        setLoading(false);
      }
      return;
    }

    // Single-repo: stream the answer in token-by-token.
    setMessages((prev) => [...prev, { role: "assistant", content: "", sources: [] }]);

    let stillLoading = true;
    function stopLoadingOnce() {
      if (stillLoading) {
        stillLoading = false;
        setLoading(false);
      }
    }

    await api.streamAsk(question, activeIndex, history, 5, {
      onSources: (sources) => {
        stopLoadingOnce();
        updateLastMessage((m) => ({ ...m, sources }));
      },
      onToken: (token) => {
        stopLoadingOnce();
        updateLastMessage((m) => ({ ...m, content: m.content + token }));
      },
      onDone: () => setLoading(false),
      onError: (detail) => {
        updateLastMessage((m) => ({ ...m, content: `❌ ${detail || "Something went wrong."}` }));
        setLoading(false);
      },
    });
  }

  function handleKey(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleAsk();
    }
  }

  // ── Onboarding ────────────────────────────────────────────────────────────────

  async function loadOnboardReport(name) {
    setOnboarding(true);
    try {
      const data = await api.fetchOnboard(name);
      setOnboardReport(data);
      setActiveTab("onboard");
    } catch (e) {
      console.error("Onboard failed:", e);
    } finally {
      setOnboarding(false);
    }
  }

  // ── Review ────────────────────────────────────────────────────────────────────

  async function handleReview() {
    if (!activeIndex || reviewing) return;
    setReviewing(true);
    addSystemMsg(`🔍 Reviewing ${activeIndex} (focus: ${reviewFocus})...`);
    try {
      const [reviewResult, repoInfo] = await Promise.all([
        api.reviewCode(activeIndex, reviewFocus),
        api.fetchRepoInfo(activeIndex),
      ]);
      setReviewData({ ...reviewResult, repo_url: repoInfo.repo_url });
      setActiveTab("review");
    } catch (e) {
      addSystemMsg("❌ Review failed: " + (e.response?.data?.detail || e.message));
    } finally {
      setReviewing(false);
    }
  }

  // ── Contribute ────────────────────────────────────────────────────────────────

  async function handleContribute() {
    if (!activeIndex || contributing) return;
    setContributing(true);
    addSystemMsg(`🌱 Finding contribution opportunities in ${activeIndex}...`);
    try {
      const [contributeResult, repoInfo] = await Promise.all([
        api.fetchContributions(activeIndex),
        api.fetchRepoInfo(activeIndex),
      ]);
      setContributeData({ ...contributeResult, repo_url: repoInfo.repo_url });
      setActiveTab("contribute");
    } catch (e) {
      addSystemMsg("❌ Contribution search failed: " + (e.response?.data?.detail || e.message));
    } finally {
      setContributing(false);
    }
  }

  // ── Return everything App needs ───────────────────────────────────────────────

  return {
    // Refs
    bottomRef,

    // Index state
    indexes, activeIndex, selectIndex,

    // Messages
    messages, loading,

    // Input
    input, setInput, handleAsk, handleKey,

    // Repo indexer
    repoUrl, setRepoUrl,
    indexing, indexMsg,
    handleIndexSubmit,

    // Multi-repo
    multiMode, setMultiMode,

    // Tabs
    activeTab, setActiveTab, askAbout,

    // Onboarding
    onboardReport, onboarding,

    // Review
    reviewData, reviewFocus,
    reviewing, setReviewFocus,
    handleReview,

    // Contribute
    contributeData, contributing,
    handleContribute,
  };
}