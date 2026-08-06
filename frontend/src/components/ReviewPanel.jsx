/**
 * components/ReviewPanel.jsx
 *
 * Full-screen code review panel.
 * Renders category tabs and a filtered list of IssueCards.
 * Does NOT fetch data — receives it via props from App.
 */

import { useState } from "react";
import { theme as t } from "../styles/theme";
import { downloadReview } from "../utils/helpers";
import IssueCard from "./IssueCard";

// ── Constants ─────────────────────────────────────────────────────────────────

const TABS = ["all", "security", "performance", "code_quality", "error_handling", "setup"];

// ── Sub-components ────────────────────────────────────────────────────────────

function PanelHeader({ indexName, focus, onExport, onClose }) {
  return (
    <div className="flex items-center justify-between shrink-0">
      <div>
        <div className={t.text.muted}>Code Review</div>
        <div className="text-lg font-bold text-purple-400">{indexName} — {focus}</div>
      </div>
      <div className="flex gap-2">
        <button onClick={onExport} className="text-xs text-purple-400 border border-purple-700 rounded px-3 py-1 hover:border-purple-400 cursor-pointer bg-transparent">
          ↓ export
        </button>
        <button onClick={onClose} className={t.button.close}>✕ close</button>
      </div>
    </div>
  );
}

function TabBar({ activeTab, issues, onSelect }) {
  return (
    <div className="flex gap-2 flex-wrap shrink-0">
      {TABS.map(tab => (
        <button
          key={tab}
          onClick={() => onSelect(tab)}
          className={t.button.tab(activeTab === tab)}
        >
          {tab === "all" ? `all (${issues.length})` : tab.replace("_", " ")}
        </button>
      ))}
    </div>
  );
}

function IssueList({ issues, copied, onCopy, onAsk, repoUrl }) {
  if (!issues.length) {
    return (
      <div className="text-sm text-gray-500 text-center py-8">
        No issues found in this category.
      </div>
    );
  }
  return issues.map((issue, idx) => (
    <IssueCard
      key={idx}
      issue={issue}
      idx={idx}
      copied={copied}
      onCopy={onCopy}
      onAsk={onAsk}
      repoUrl={repoUrl}
    />
  ));
}

// ── Main component ────────────────────────────────────────────────────────────

export default function ReviewPanel({ data, indexName, onClose, onAsk }) {
  const [activeTab, setActiveTab] = useState("all");
  const [copied, setCopied]       = useState(null);

  const issues   = data?.issues || [];
  const filtered = activeTab === "all" ? issues : issues.filter(i => i.category === activeTab);

  function handleCopy(fix, idx) {
    navigator.clipboard.writeText(fix);
    setCopied(idx);
    setTimeout(() => setCopied(null), 2000);
  }

  function handleExport() {
    const content = issues
      .map(i => `### ${i.title}\n**File:** ${i.file}:${i.line_start}\n**Severity:** ${i.severity}\n\n${i.what}\n\n**Fix:**\n\`\`\`\n${i.suggested_fix}\n\`\`\``)
      .join("\n\n---\n\n");
    downloadReview(content, indexName, data.focus);
  }

  return (
    <div className="flex flex-col flex-1 min-h-0 px-6 py-6 gap-4">

      <PanelHeader
        indexName={indexName}
        focus={data.focus}
        onExport={handleExport}
        onClose={onClose}
      />

      <TabBar activeTab={activeTab} issues={issues} onSelect={setActiveTab} />

      {/* Scrollable issue list */}
      <div className="flex flex-col gap-4 overflow-y-auto flex-1 pr-1">
        <IssueList
          issues={filtered}
          copied={copied}
          onCopy={handleCopy}
          onAsk={onAsk}
          repoUrl={data.repo_url}
        />
      </div>

    </div>
  );
}