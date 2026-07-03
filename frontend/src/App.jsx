import { useState, useRef, useEffect } from "react";
import axios from "axios";
import ReactMarkdown from "react-markdown";

const API = "http://localhost:8000";

// ─── Source chunk card ───────────────────────────────────────────────────────
function SourceCard({ chunk, index }) {
  const [open, setOpen] = useState(false);
  const score = Math.round(chunk.score * 100);
  const path = chunk.rel_path.replace(/\\/g, "/");

  return (
    <div className="mt-3 rounded-lg border border-gray-700 overflow-hidden">
      <div
        className="flex items-center justify-between px-3 py-2 bg-blue-950 cursor-pointer select-none"
        onClick={() => setOpen(!open)}
      >
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs px-2 py-0.5 rounded bg-blue-900 text-blue-300 border border-blue-700">#{index + 1}</span>
          <span className="text-xs font-semibold text-blue-400">{path}</span>
          <span className="text-xs text-gray-500">:{chunk.start_line}–{chunk.end_line}</span>
          <span className="text-xs px-2 py-0.5 rounded bg-gray-800 text-gray-400 border border-gray-700">{chunk.type}: {chunk.name}</span>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className={`text-xs px-2 py-0.5 rounded border ${score > 50 ? "bg-green-900 text-green-400 border-green-700" : "bg-gray-800 text-gray-400 border-gray-700"}`}>
            {score}% match
          </span>
          <span className="text-gray-500 text-xs">{open ? "▲" : "▼"}</span>
        </div>
      </div>
      {open && (
        <pre className="p-4 text-xs text-blue-200 bg-gray-950 overflow-x-auto whitespace-pre-wrap break-words leading-relaxed font-mono">
          {chunk.content}
        </pre>
      )}
    </div>
  );
}

// ─── Single message bubble ───────────────────────────────────────────────────
function Message({ msg }) {
  const [showSources, setShowSources] = useState(false);

  if (msg.role === "system") {
    return (
      <div className="self-center text-xs text-gray-500 bg-gray-800 border border-gray-700 rounded-full px-4 py-1">
        {msg.content}
      </div>
    );
  }

  if (msg.role === "user") {
    return (
      <div className="self-end bg-blue-950 border border-blue-800 rounded-tl-xl rounded-tr-xl rounded-bl-xl px-4 py-2 max-w-[70%] text-sm leading-relaxed">
        {msg.content}
      </div>
    );
  }

  return (
    <div className="self-start bg-gray-800 border border-gray-700 rounded-tr-xl rounded-br-xl rounded-bl-xl px-4 py-3 max-w-[80%] text-sm leading-relaxed">
      <div className="prose prose-invert prose-sm max-w-none">
        <ReactMarkdown
          components={{
            code({ children, className }) {
              const isBlock = className?.includes("language-");
              return isBlock ? (
                <pre className="bg-gray-950 text-blue-200 rounded-md p-3 my-2 overflow-x-auto text-xs font-mono">
                  <code>{children}</code>
                </pre>
              ) : (
                <code className="bg-gray-950 text-blue-300 rounded px-1.5 py-0.5 text-xs font-mono">
                  {children}
                </code>
              );
            },
          }}
        >
          {msg.content}
        </ReactMarkdown>
      </div>

      {msg.sources?.length > 0 && (
        <div className="mt-3">
          <button
            onClick={() => setShowSources(!showSources)}
            className="text-xs text-gray-400 border border-gray-600 rounded px-3 py-1 hover:border-gray-400 transition-colors cursor-pointer bg-transparent font-mono"
          >
            {showSources ? "▲ hide" : "▼ show"} {msg.sources.length} source{msg.sources.length > 1 ? "s" : ""}
          </button>
          {showSources && msg.sources.map((chunk, i) => (
            <SourceCard key={i} chunk={chunk} index={i} />
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Main app ────────────────────────────────────────────────────────────────
export default function App() {
  const [indexes, setIndexes]         = useState([]);
  const [activeIndex, setActiveIndex] = useState(null);
  const [messages, setMessages]       = useState([]);
  const [input, setInput]             = useState("");
  const [loading, setLoading]         = useState(false);
  const [repoUrl, setRepoUrl]         = useState("");
  const [indexing, setIndexing]       = useState(false);
  const [indexMsg, setIndexMsg]       = useState("");
  const bottomRef = useRef(null);

  useEffect(() => { fetchIndexes(); }, []);
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  async function fetchIndexes() {
    try {
      const res = await axios.get(`${API}/indexes`);
      setIndexes(res.data.indexes);
    } catch { }
  }

  function selectIndex(name) {
    setActiveIndex(name);
    setMessages([{ role: "system", content: `Switched to: ${name}` }]);
  }

  function addSystemMsg(content) {
    setMessages(prev => [...prev, { role: "system", content }]);
  }

  function pollStatus(name) {
    const interval = setInterval(async () => {
      try {
        const res = await axios.get(`${API}/status/${name}`);
        const { status, chunk_count } = res.data;
        if (status === "done") {
          clearInterval(interval);
          setIndexing(false);
          setIndexMsg("");
          await fetchIndexes();
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

  async function handleIndex() {
    if (!repoUrl.trim()) return;
    setIndexing(true);
    setIndexMsg("Starting...");
    const name = repoUrl.trim().split("/").pop().replace(".git", "");
    try {
      const res = await axios.post(`${API}/index`, { repo_url: repoUrl.trim(), force: false });
      if (res.data.status === "already_exists") {
        setIndexing(false);
        setIndexMsg("");
        await fetchIndexes();
        selectIndex(name);
        addSystemMsg(`Index '${name}' already exists — loaded.`);
      } else {
        pollStatus(name);
      }
    } catch (e) {
      setIndexing(false);
      setIndexMsg("❌ " + (e.response?.data?.detail || e.message));
    }
  }

  async function handleAsk() {
    const question = input.trim();
    if (!question || !activeIndex || loading) return;
    setInput("");
    setMessages(prev => [...prev, { role: "user", content: question }]);
    setLoading(true);
    try {
      const res = await axios.post(`${API}/ask`, { question, index_name: activeIndex, top_k: 5 });
      setMessages(prev => [...prev, { role: "assistant", content: res.data.answer, sources: res.data.sources }]);
    } catch (e) {
      setMessages(prev => [...prev, { role: "assistant", content: `❌ ${e.response?.data?.detail || "Something went wrong."}`, sources: [] }]);
    } finally {
      setLoading(false);
    }
  }

  function handleKey(e) {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleAsk(); }
  }

  return (
    <div className="flex h-screen bg-gray-950 text-gray-100 font-mono overflow-hidden">

      {/* Sidebar */}
      <div className="w-72 bg-gray-900 border-r border-gray-700 flex flex-col shrink-0">
        <div className="px-5 py-4 border-b border-gray-700">
          <span className="text-lg font-bold text-blue-400 tracking-tight">⚡ CodeSage</span>
        </div>

        <div className="px-4 py-4 border-b border-gray-700">
          <div className="text-xs text-gray-500 uppercase tracking-widest mb-2">Index a repo</div>
          <input
            className="w-full bg-gray-950 border border-gray-700 rounded-lg px-3 py-2 text-xs text-gray-100 placeholder-gray-600 outline-none focus:border-blue-500 transition-colors font-mono"
            placeholder="https://github.com/user/repo"
            value={repoUrl}
            onChange={e => setRepoUrl(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleIndex()}
          />
          <button
            className="mt-2 w-full bg-blue-500 hover:bg-blue-400 text-gray-950 font-bold text-xs py-2 rounded-lg transition-colors disabled:opacity-50 cursor-pointer"
            onClick={handleIndex}
            disabled={indexing}
          >
            {indexing ? indexMsg : "Index repo"}
          </button>
          {indexMsg && !indexing && (
            <div className="text-xs text-gray-500 mt-2">{indexMsg}</div>
          )}
        </div>

        <div className="flex-1 overflow-y-auto">
          <div className="text-xs text-gray-500 uppercase tracking-widest px-5 py-3">Indexed repos</div>
          {indexes.length === 0 && <div className="text-xs text-gray-600 px-5">No indexes yet.</div>}
          {indexes.map(name => (
            <div
              key={name}
              onClick={() => selectIndex(name)}
              className={`px-5 py-2.5 text-xs cursor-pointer border-l-2 transition-all break-all ${
                name === activeIndex
                  ? "text-blue-400 bg-blue-950 border-blue-400"
                  : "text-gray-400 border-transparent hover:text-gray-200 hover:bg-gray-800"
              }`}
            >
              {name}
            </div>
          ))}
        </div>

        <div className="px-5 py-3 border-t border-gray-700 text-xs text-gray-600">
          RAG · FAISS · Groq · Llama 3.3
        </div>
      </div>

      {/* Main */}
      <div className="flex flex-col flex-1 overflow-hidden">
        <div className="px-6 py-3 border-b border-gray-700 bg-gray-900 flex items-center gap-3">
          {activeIndex ? (
            <>
              <span className="text-xs px-2 py-0.5 rounded bg-green-900 text-green-400 border border-green-700">● live</span>
              <span className="text-sm font-semibold">{activeIndex}</span>
              <span className="text-xs text-gray-500">— ask anything about this codebase</span>
            </>
          ) : (
            <span className="text-xs text-gray-500">Select or index a repo to start chatting</span>
          )}
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-6 flex flex-col gap-5">
          {messages.length === 0 && (
            <div className="flex-1 flex flex-col items-center justify-center text-center gap-4 text-gray-500">
              <div className="text-5xl">⚡</div>
              <div className="text-lg font-semibold text-gray-300">Ask anything about your codebase</div>
              <div className="text-sm max-w-md leading-relaxed">
                Index a GitHub repo on the left, then ask:<br />
                <span className="text-blue-400">"How does the diagnosis agent work?"</span><br />
                <span className="text-blue-400">"Where is authentication handled?"</span>
              </div>
            </div>
          )}
          {messages.map((msg, i) => <Message key={i} msg={msg} />)}
          {loading && (
            <div className="self-start bg-gray-800 border border-gray-700 rounded-tr-xl rounded-br-xl rounded-bl-xl px-4 py-3 text-sm text-gray-400">
              Searching codebase and generating answer...
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <div className="px-6 py-4 border-t border-gray-700 bg-gray-900 flex gap-3">
          <input
            className="flex-1 bg-gray-950 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-gray-100 placeholder-gray-600 outline-none focus:border-blue-500 transition-colors font-mono disabled:opacity-50"
            placeholder={activeIndex ? `Ask about ${activeIndex}...` : "Select a repo first"}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
            disabled={!activeIndex || loading}
          />
          <button
            className="bg-blue-500 hover:bg-blue-400 text-gray-950 font-bold text-sm px-5 rounded-lg transition-colors disabled:opacity-50 cursor-pointer"
            onClick={handleAsk}
            disabled={!activeIndex || loading || !input.trim()}
          >
            Ask
          </button>
        </div>
      </div>
    </div>
  );
}
