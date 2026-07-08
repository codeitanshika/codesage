import { useState, useRef, useEffect } from "react";
import axios from "axios";
import ReactMarkdown from "react-markdown";


const API = "http://localhost:8000";

// ─── Utilities ───────────────────────────────────────────────────────────────
function downloadReview(content, indexName, focus) {
    const text = `# CodeSage Review — ${indexName}\nFocus: ${focus}\nDate: ${new Date().toLocaleDateString()}\n\n${content}`;
    const blob = new Blob([text], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `review-${indexName}-${focus}.md`;
    a.click();
    URL.revokeObjectURL(url);
}

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
          {chunk.github_url ? (
              
                <a href={chunk.github_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs font-semibold text-blue-400 hover:text-blue-300 hover:underline"
                  onClick={e => e.stopPropagation()}
              >
                  {path} ↗
              </a>
          ) : (
              <span className="text-xs font-semibold text-blue-400">{path}</span>
          )}
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

      {msg.isReview && (
        <button
            onClick={() => downloadReview(msg.content, msg.reviewMeta.indexName, msg.reviewMeta.focus)}
            className="mt-3 text-xs text-purple-400 border border-purple-700 rounded px-3 py-1 hover:border-purple-400 transition-colors cursor-pointer bg-transparent font-mono"
        >
            ↓ download review
        </button>
    )}
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


function IssueCard({ issue, idx, copied, onCopy, onAsk, repoUrl }) {
  const [expanded, setExpanded] = useState(false);
  const githubUrl = issue.file && repoUrl
    ? `${repoUrl}/blob/main/${issue.file.replace(/\\/g, "/")}#L${issue.line_start}`
    : null;

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl overflow-hidden">
      <div
        className="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-gray-800 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`text-xs px-2 py-0.5 rounded border font-bold uppercase ${SEVERITY_STYLE[issue.severity] || SEVERITY_STYLE.low}`}>
            {issue.severity}
          </span>
          <span className="text-sm font-semibold text-gray-100">{issue.title}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">{issue.category?.replace("_", " ")}</span>
          <span className="text-gray-500 text-xs">{expanded ? "▲" : "▼"}</span>
        </div>
      </div>

      {expanded && (
        <div className="px-4 py-3 flex flex-col gap-3 border-t border-gray-700">
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">📄</span>
            {githubUrl ? (
              <a href={githubUrl} target="_blank" rel="noopener noreferrer"
                className="text-xs text-blue-400 font-mono hover:text-blue-300 hover:underline">
                {issue.file.replace(/\\/g, "/")}:{issue.line_start} ↗
              </a>
            ) : (
              <span className="text-xs text-blue-400 font-mono">{issue.file}:{issue.line_start}</span>
            )}
          </div>
          <div>
            <div className="text-xs text-gray-500 uppercase tracking-widest mb-1">What is the issue</div>
            <p className="text-sm text-gray-300">{issue.what}</p>
          </div>
          <div>
            <div className="text-xs text-gray-500 uppercase tracking-widest mb-1">Why it matters in this project</div>
            <p className="text-sm text-yellow-200">{issue.why_matters}</p>
          </div>
          <div>
            <div className="text-xs text-red-400 uppercase tracking-widest mb-1">Current code</div>
            <pre className="bg-gray-950 text-red-200 text-xs p-3 rounded-lg overflow-x-auto font-mono whitespace-pre-wrap">{issue.current_code}</pre>
          </div>
          <div>
            <div className="flex items-center justify-between mb-1">
              <div className="text-xs text-green-400 uppercase tracking-widest">Suggested fix</div>
              <button onClick={() => onCopy(issue.suggested_fix, idx)}
                className="text-xs text-gray-500 hover:text-green-400 cursor-pointer bg-transparent border-none">
                {copied === idx ? "✓ copied" : "copy"}
              </button>
            </div>
            <pre className="bg-gray-950 text-green-200 text-xs p-3 rounded-lg overflow-x-auto font-mono whitespace-pre-wrap">{issue.suggested_fix}</pre>
          </div>
          <div>
            <div className="text-xs text-gray-500 uppercase tracking-widest mb-1">How the fix helps</div>
            <p className="text-sm text-green-300">{issue.how_fix_helps}</p>
          </div>
          <button onClick={() => onAsk(`Tell me more about the "${issue.title}" issue in ${issue.file}`)}
            className="text-xs text-left text-gray-400 border border-gray-700 rounded px-3 py-2 hover:border-blue-500 hover:text-blue-400 transition-colors cursor-pointer bg-transparent">
            💬 Ask CodeSage about this issue
          </button>
        </div>
      )}
    </div>
  );
}

// ─── Review Panel ─────────────────────────────────────────────────────────────
const SEVERITY_STYLE = {
  high:   "bg-red-900 text-red-300 border-red-700",
  medium: "bg-yellow-900 text-yellow-300 border-yellow-700",
  low:    "bg-green-900 text-green-300 border-green-700",
};

const CATEGORY_TABS = ["all", "security", "performance", "code_quality", "error_handling", "setup"];
function ReviewPanel({ data, onClose, onAsk, indexName }) {
  const [activeTab, setActiveTab] = useState("all");
  const [copied, setCopied] = useState(null);

  const issues = data?.issues || [];
  const filtered = activeTab === "all"
    ? issues
    : issues.filter(i => i.category === activeTab);

  function copyFix(fix, idx) {
    navigator.clipboard.writeText(fix);
    setCopied(idx);
    setTimeout(() => setCopied(null), 2000);
  }
 
  return (
    <div className="flex-1 overflow-y-auto px-6 py-6 flex flex-col gap-4">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-gray-500 uppercase tracking-widest mb-1">Code Review</div>
          <div className="text-lg font-bold text-purple-400">{indexName} — {data.focus}</div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => downloadReview(
              issues.map(i => `### ${i.title}\n**File:** ${i.file}:${i.line_start}\n**Severity:** ${i.severity}\n\n${i.what}\n\n**Fix:**\n\`\`\`\n${i.suggested_fix}\n\`\`\``).join("\n\n---\n\n"),
              indexName, data.focus
            )}
            className="text-xs text-purple-400 border border-purple-700 rounded px-3 py-1 hover:border-purple-400 cursor-pointer bg-transparent"
          >
            ↓ export
          </button>
          <button
            onClick={onClose}
            className="text-xs text-gray-500 border border-gray-600 rounded px-3 py-1 hover:border-gray-400 cursor-pointer bg-transparent"
          >
            ✕ close
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 flex-wrap">
        {CATEGORY_TABS.map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`text-xs px-3 py-1 rounded border cursor-pointer transition-colors ${
              activeTab === tab
                ? "bg-purple-900 text-purple-300 border-purple-600"
                : "text-gray-500 border-gray-700 hover:border-gray-500 bg-transparent"
            }`}
          >
            {tab === "all" ? `all (${issues.length})` : tab.replace("_", " ")}
          </button>
        ))}
      </div>

      {/* Issue cards */}
      {filtered.length === 0 && (
        <div className="text-sm text-gray-500 text-center py-8">
          No issues found in this category.
        </div>
      )}

      {filtered.map((issue, idx) => (
  <IssueCard
    key={idx}
    issue={issue}
    idx={idx}
    copied={copied}
    onCopy={copyFix}
    onAsk={onAsk}
    repoUrl={data.repo_url}
  />
))}
    </div>
  );
}
// ─── Onboarding Report Panel ─────────────────────────────────────────────────
function OnboardPanel({ report, onClose, onQuestion, indexName }) {
  const repoUrl = report.repo_url || "";

  return (
    <div className="flex-1 overflow-y-auto px-6 py-6 flex flex-col gap-6">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-gray-500 uppercase tracking-widest mb-1">Onboarding Report</div>
          <div className="text-lg font-bold text-blue-400">{indexName}</div>
        </div>
        <button
          onClick={onClose}
          className="text-xs text-gray-500 border border-gray-600 rounded px-3 py-1 hover:border-gray-400 cursor-pointer bg-transparent"
        >
          Start chatting →
        </button>
      </div>

      {/* What it does */}
      <div className="bg-gray-900 border border-gray-700 rounded-xl p-5">
        <div className="text-xs text-blue-400 uppercase tracking-widest mb-2">What this project does</div>
        <p className="text-sm text-gray-200 leading-relaxed">{report.what_it_does}</p>
      </div>

      {/* Architecture */}
      <div className="bg-gray-900 border border-gray-700 rounded-xl p-5">
        <div className="text-xs text-blue-400 uppercase tracking-widest mb-2">Architecture</div>
        <p className="text-sm text-gray-300 leading-relaxed">{report.architecture}</p>
      </div>

      {/* How to run */}
      <div className="bg-gray-900 border border-gray-700 rounded-xl p-5">
        <div className="text-xs text-blue-400 uppercase tracking-widest mb-3">How to run</div>
        <div className="flex flex-col gap-2">
          {report.how_to_run.map((step, i) => (
            <div key={i} className="flex gap-3 items-start">
              <span className="text-xs px-2 py-0.5 rounded bg-blue-900 text-blue-300 border border-blue-700 shrink-0 mt-0.5">
                {i + 1}
              </span>
              <span className="text-sm text-gray-300">{step.replace(/^Step \d+:\s*/, "")}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Key files */}
      <div className="bg-gray-900 border border-gray-700 rounded-xl p-5">
        <div className="text-xs text-blue-400 uppercase tracking-widest mb-3">Key files to read first</div>
        <div className="flex flex-col gap-2">
          {report.key_files.map((kf, i) => (
            <div key={i} className="flex gap-3 items-start p-3 bg-gray-950 rounded-lg border border-gray-700">
              <span className="text-xs text-blue-400 font-semibold shrink-0 mt-0.5">📄</span>
              <div>
                <div className="text-xs font-semibold text-blue-400 mb-0.5">
                  {kf.file}
                </div>
                <div className="text-xs text-gray-400">{kf.why}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Gotchas */}
      <div className="bg-gray-900 border border-gray-700 rounded-xl p-5">
        <div className="text-xs text-yellow-500 uppercase tracking-widest mb-3">⚠ Gotchas for new contributors</div>
        <div className="flex flex-col gap-2">
          {report.gotchas.map((g, i) => (
            <div key={i} className="flex gap-3 items-start p-3 bg-yellow-950 rounded-lg border border-yellow-800">
              <span className="text-yellow-500 text-xs shrink-0 mt-0.5">!</span>
              <span className="text-xs text-yellow-200">{g.replace(/^Gotcha \d+:\s*/, "")}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Suggested questions */}
      <div className="bg-gray-900 border border-gray-700 rounded-xl p-5">
        <div className="text-xs text-green-400 uppercase tracking-widest mb-3">Suggested questions to ask</div>
        <div className="flex flex-col gap-2">
          {report.suggested_questions.map((q, i) => (
            <button
              key={i}
              onClick={() => onQuestion(q)}
              className="text-left text-xs text-gray-300 p-3 bg-gray-950 rounded-lg border border-gray-700 hover:border-green-600 hover:text-green-300 transition-colors cursor-pointer"
            >
              {q}
            </button>
          ))}
        </div>
        <div className="text-xs text-gray-600 mt-3">Click any question to send it to chat</div>
      </div>

      {/* Start chatting button */}
      <button
        onClick={onClose}
        className="w-full bg-blue-500 hover:bg-blue-400 text-gray-950 font-bold text-sm py-3 rounded-xl transition-colors cursor-pointer"
      >
        Start chatting about this codebase →
      </button>

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
  const [multiMode, setMultiMode]     = useState(false); 
  const [reviewMode, setReviewMode]   = useState(false);
  const [reviewFocus, setReviewFocus] = useState("general");
  const [reviewing, setReviewing]     = useState(false);
  const [onboardReport, setOnboardReport] = useState(null);
  const [onboarding, setOnboarding]       = useState(false);
  const [showOnboard, setShowOnboard]     = useState(false);
  const [reviewData, setReviewData]     = useState(null);
  const [showReview, setShowReview]     = useState(false);

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
    setShowOnboard(false);
    setOnboardReport(null);
    setMessages([{ role: "system", content: `Switched to: ${name}` }]);
    fetchOnboard(name);
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
      const history = messages
    .filter(m => m.role === "user" || m.role === "assistant")
    .map(m => ({ role: m.role, content: m.content }))
    .slice(-6);

    const endpoint = multiMode ? `${API}/ask-multi` : `${API}/ask`;
    const payload = multiMode
        ? { question, index_names: indexes, top_k: 3, history }
        : { question, index_name: activeIndex, top_k: 5, history };

    const res = await axios.post(endpoint, payload);
          setMessages(prev => [...prev, { role: "assistant", content: res.data.answer, sources: res.data.sources }]);
        } catch (e) {
          setMessages(prev => [...prev, { role: "assistant", content: `❌ ${e.response?.data?.detail || "Something went wrong."}`, sources: [] }]);
        } finally {
          setLoading(false);
        }
      }
  async function handleReview() {
    if (!activeIndex || reviewing) return;
    setReviewing(true);
    addSystemMsg(`🔍 Reviewing ${activeIndex} (focus: ${reviewFocus})...`);
    try {
        const res = await axios.post(`${API}/review`, {
            index_name: activeIndex,
            focus: reviewFocus,
        });
        const repoUrl = await axios.get(`${API}/repo-info/${activeIndex}`);
        setReviewData({ ...res.data, repo_url: repoUrl.data.repo_url });
        setShowReview(true);
        setShowOnboard(false);
    } catch (e) {
        addSystemMsg("❌ Review failed: " + (e.response?.data?.detail || e.message));
    } finally {
        setReviewing(false);
    }
  }

  async function fetchOnboard(name) {
    setOnboarding(true);
    try {
        const res = await axios.post(`${API}/onboard`, { index_name: name });
        setOnboardReport(res.data);
        setShowOnboard(true);
    } catch (e) {
        console.error("Onboard failed:", e);
    } finally {
        setOnboarding(false);
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

        <div className="overflow-y-auto" style={{maxHeight: "200px"}}>
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
        {/* Code Review */}
        {activeIndex && (
            <div className="px-4 py-4 border-t border-gray-700">
                <div className="text-xs text-gray-500 uppercase tracking-widest mb-2">Code Review</div>
                <select
                    className="w-full bg-gray-950 border border-gray-700 rounded-lg px-3 py-2 text-xs text-gray-100 outline-none focus:border-blue-500 transition-colors font-mono"
                    value={reviewFocus}
                    onChange={e => setReviewFocus(e.target.value)}
                >
                    <option value="general">General</option>
                    <option value="security">Security</option>
                    <option value="performance">Performance</option>
                    <option value="error-handling">Error Handling</option>
                </select>
                <button
                    className="w-full bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs py-2 rounded-lg transition-colors disabled:opacity-50 cursor-pointer"
                    onClick={handleReview}
                    disabled={reviewing}
                >
                    {reviewing ? "Reviewing..." : "Review Code"}
                </button>
            </div>
        )}

        {/* Footer - already exists */}
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
                  {indexes.length > 1 && (
                    <button
                      onClick={() => setMultiMode(!multiMode)}
                      className={`ml-auto text-xs px-3 py-1 rounded border transition-colors cursor-pointer ${
                        multiMode
                          ? "bg-blue-900 text-blue-300 border-blue-600"
                          : "text-gray-500 border-gray-600 hover:border-gray-400 bg-transparent"
                      }`}
                    >
                      {multiMode ? "● searching all repos" : "search all repos"}
                    </button>
                  )}
            </>
          ) : (
            <span className="text-xs text-gray-500">Select or index a repo to start chatting</span>
          )}
        </div>

        

        {showReview && reviewData ? (
            <ReviewPanel
                data={reviewData}
                indexName={activeIndex}
                onClose={() => setShowReview(false)}
                onAsk={(q) => {
                    setShowReview(false);
                    setInput(q);
                }}
            />
        ) : showOnboard && onboardReport ? (
            <OnboardPanel
                report={onboardReport}
                indexName={activeIndex}
                onClose={() => setShowOnboard(false)}
                onQuestion={(q) => {
                    setShowOnboard(false);
                    setInput(q);
                }}
            />
        ) : (
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
        )}

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
