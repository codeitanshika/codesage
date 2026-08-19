/**
 * components/ContributePanel.jsx
 *
 * Full-screen contribution opportunities panel.
 * Renders difficulty tabs and a filtered list of ContributionCards.
 * Does NOT fetch data — receives it via props from App.
 */

import { useState } from "react";
import { theme as t } from "../styles/theme";
import ContributionCard from "./ContributionCard";
import RealIssueCard from "./RealIssueCard";

// ── Constants ─────────────────────────────────────────────────────────────────

const TABS = ["all", "good-first-issue", "medium", "advanced"];

// ── Sub-components ────────────────────────────────────────────────────────────

function PanelHeader({ indexName, onClose }) {
  return (
    <div className="flex items-center justify-between shrink-0">
      <div>
        <div className={t.text.muted}>Contribution Opportunities</div>
        <div className="text-lg font-bold text-purple-400">{indexName}</div>
      </div>
      <button onClick={onClose} className={t.button.close}>✕ close</button>
    </div>
  );
}

function TabBar({ activeTab, opportunities, onSelect }) {
  return (
    <div className="flex gap-2 flex-wrap shrink-0">
      {TABS.map(tab => (
        <button
          key={tab}
          onClick={() => onSelect(tab)}
          className={t.button.tab(activeTab === tab)}
        >
          {tab === "all" ? `all (${opportunities.length})` : tab.replace("-", " ")}
        </button>
      ))}
    </div>
  );
}

function RealIssuesSection({ issues }) {
  if (!issues.length) return null;
  return (
    <div className="flex flex-col gap-3 shrink-0">
      <div className={t.text.sectionGreen}>
        Already open on GitHub — real issues, not AI-inferred
      </div>
      <div className="flex flex-col gap-3">
        {issues.map((issue) => (
          <RealIssueCard key={issue.number} issue={issue} />
        ))}
      </div>
    </div>
  );
}

function ContributionList({ opportunities, copied, onCopy, onAsk, repoUrl }) {
  if (!opportunities.length) {
    return (
      <div className="text-sm text-gray-500 text-center py-8">
        No opportunities found in this category.
      </div>
    );
  }
  return opportunities.map((item, idx) => (
    <ContributionCard
      key={idx}
      item={item}
      idx={idx}
      copied={copied}
      onCopy={onCopy}
      onAsk={onAsk}
      repoUrl={repoUrl}
    />
  ));
}

// ── Main component ────────────────────────────────────────────────────────────

export default function ContributePanel({ data, indexName, onClose, onAsk }) {
  const [activeTab, setActiveTab] = useState("all");
  const [copied, setCopied]       = useState(null);

  const opportunities = data?.opportunities || [];
  const realIssues = data?.real_issues || [];
  const filtered = activeTab === "all" ? opportunities : opportunities.filter(o => o.difficulty === activeTab);

  function handleCopy(text, idx) {
    navigator.clipboard.writeText(text);
    setCopied(idx);
    setTimeout(() => setCopied(null), 2000);
  }

  return (
    <div className="flex flex-col flex-1 min-h-0 px-6 py-6 gap-4 overflow-y-auto">

      <PanelHeader indexName={indexName} onClose={onClose} />

      <RealIssuesSection issues={realIssues} />

      <div className={t.text.sectionBlue}>AI-suggested opportunities</div>

      <TabBar activeTab={activeTab} opportunities={opportunities} onSelect={setActiveTab} />

      <div className="flex flex-col gap-4 pr-1">
        <ContributionList
          opportunities={filtered}
          copied={copied}
          onCopy={handleCopy}
          onAsk={onAsk}
          repoUrl={data.repo_url}
        />
      </div>

    </div>
  );
}
