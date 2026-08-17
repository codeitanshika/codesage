/**
 * components/Sidebar.jsx
 *
 * Left panel of the app.
 * Responsibilities: repo URL input, index button, indexed repos list,
 * code review focus selector and trigger button.
 * All state and handlers come from props — Sidebar owns no state itself.
 */

import { theme as t } from "../styles/theme";

// ── Sub-components ────────────────────────────────────────────────────────────

function Logo() {
  return (
    <div className={t.sidebar.logo}>
      <span className={t.sidebar.logoText}>⚡ CodeSage</span>
    </div>
  );
}

function RepoIndexer({ repoUrl, indexing, indexMsg, onChange, onSubmit }) {
  return (
    <div className={t.sidebar.section}>
      <div className={t.sidebar.label}>Index a repo</div>
      <input
        className={t.input.base}
        placeholder="https://github.com/user/repo"
        value={repoUrl}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && onSubmit()}
      />
      <button
        className={`mt-2 ${t.button.indexItem}`}
        onClick={onSubmit}
        disabled={indexing}
      >
        {indexing ? indexMsg : "Index repo"}
      </button>
      {indexMsg && !indexing && (
        <div className="text-xs text-gray-500 mt-2">{indexMsg}</div>
      )}
    </div>
  );
}

function IndexList({ indexes, activeIndex, onSelect }) {
  return (
    <div className={t.sidebar.repoList} style={{ maxHeight: "200px" }}>
      <div className={`${t.sidebar.label} px-5 py-3`}>Indexed repos</div>
      {!indexes.length && (
        <div className="text-xs text-gray-600 px-5">No indexes yet.</div>
      )}
      {indexes.map((name) => (
        <div
          key={name}
          onClick={() => onSelect(name)}
          className={t.sidebar.repoItem(name === activeIndex)}
        >
          {name}
        </div>
      ))}
    </div>
  );
}

function CodeReview({ activeIndex, reviewFocus, reviewing, onFocusChange, onReview }) {
  if (!activeIndex) return null;
  return (
    <div className={t.sidebar.section}>
      <div className={t.sidebar.label}>Code Review</div>
      <select
        className={t.input.select}
        value={reviewFocus}
        onChange={(e) => onFocusChange(e.target.value)}
      >
        <option value="general">General</option>
        <option value="security">Security</option>
        <option value="performance">Performance</option>
        <option value="error-handling">Error Handling</option>
      </select>
      <button
        className={t.button.purple}
        onClick={onReview}
        disabled={reviewing}
      >
        {reviewing ? "Reviewing..." : "Review Code"}
      </button>
    </div>
  );
}

function Contribute({ activeIndex, contributing, onContribute }) {
  if (!activeIndex) return null;
  return (
    <div className={t.sidebar.section}>
      <div className={t.sidebar.label}>Contribute</div>
      <button
        className={t.button.purple}
        onClick={onContribute}
        disabled={contributing}
      >
        {contributing ? "Searching..." : "Find Good First Issues"}
      </button>
    </div>
  );
}

function Footer() {
  return (
    <div className={t.sidebar.footer}>
      RAG · FAISS · Groq · Llama 3.3
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export default function Sidebar({
  // Repo indexer
  repoUrl, indexing, indexMsg,
  onRepoUrlChange, onIndexSubmit,
  // Index list
  indexes, activeIndex, onSelectIndex,
  // Code review
  reviewFocus, reviewing,
  onReviewFocusChange, onReview,
  // Contribute
  contributing, onContribute,
}) {
  return (
    <div className={t.sidebar.root}>
      <Logo />
      <RepoIndexer
        repoUrl={repoUrl}
        indexing={indexing}
        indexMsg={indexMsg}
        onChange={onRepoUrlChange}
        onSubmit={onIndexSubmit}
      />
      <IndexList
        indexes={indexes}
        activeIndex={activeIndex}
        onSelect={onSelectIndex}
      />
      <CodeReview
        activeIndex={activeIndex}
        reviewFocus={reviewFocus}
        reviewing={reviewing}
        onFocusChange={onReviewFocusChange}
        onReview={onReview}
      />
      <Contribute
        activeIndex={activeIndex}
        contributing={contributing}
        onContribute={onContribute}
      />
      <Footer />
    </div>
  );
}