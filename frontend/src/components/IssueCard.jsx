/**
 * components/IssueCard.jsx
 * Expandable card per code review issue.
 */

import { useState } from "react";
import { theme as t } from "../styles/theme";
import { buildGithubUrl } from "../utils/helpers";

// ── Sub-components ────────────────────────────────────────────────────────────

function SeverityBadge({ severity }) {
  return (
    <span className={`${t.badge.base} font-bold uppercase ${t.badge[severity] || t.badge.low}`}>
      {severity}
    </span>
  );
}

function FileLink({ file, githubUrl, lineStart }) {
  const label = `${file?.replace(/\\/g, "/")}:${lineStart}`;
  return githubUrl ? (
    <a href={githubUrl} target="_blank" rel="noopener noreferrer"
      className="text-xs text-blue-400 font-mono hover:text-blue-300 hover:underline">
      {label} ↗
    </a>
  ) : (
    <span className={t.text.blue}>{label}</span>
  );
}

function Section({ label, labelClass = t.text.sectionGray, children }) {
  return (
    <div>
      <div className={labelClass}>{label}</div>
      {children}
    </div>
  );
}

function CardHeader({ title, severity, category, expanded, onToggle }) {
  return (
    <div className={t.card.header} onClick={onToggle}>
      <div className="flex items-center gap-2 flex-wrap">
        <SeverityBadge severity={severity} />
        <span className="text-sm font-semibold text-gray-100">{title}</span>
      </div>
      <div className="flex items-center gap-2">
        <span className={t.text.muted}>{category?.replace("_", " ")}</span>
        <span className={t.text.muted}>{expanded ? "▲" : "▼"}</span>
      </div>
    </div>
  );
}

function CardBody({ issue, githubUrl, copied, onCopy, onAsk }) {
  const { file, line_start, what, why_matters, current_code, suggested_fix, how_fix_helps, title } = issue;

  return (
    <div className={t.card.body}>

      <div className="flex items-center gap-2">
        <span className={t.text.muted}>📄</span>
        <FileLink file={file} githubUrl={githubUrl} lineStart={line_start} />
      </div>

      <Section label="What is the issue">
        <p className={t.text.body}>{what}</p>
      </Section>

      <Section label="Why it matters in this project">
        <p className={t.text.yellow}>{why_matters}</p>
      </Section>

      <Section label="Current code" labelClass={t.text.sectionRed}>
        <pre className={`${t.code.block} ${t.code.red}`}>{current_code}</pre>
      </Section>

      <div>
        <div className="flex items-center justify-between mb-1">
          <div className={t.text.sectionGreen}>Suggested fix</div>
          <button onClick={() => onCopy(suggested_fix)} className={t.button.copy}>
            {copied ? "✓ copied" : "copy"}
          </button>
        </div>
        <pre className={`${t.code.block} ${t.code.green}`}>{suggested_fix}</pre>
      </div>

      <Section label="How the fix helps">
        <p className={t.text.green}>{how_fix_helps}</p>
      </Section>

      <button onClick={() => onAsk(`Tell me more about "${title}" in ${file}`)}
        className={t.button.ghost}>
        💬 Ask CodeSage about this issue
      </button>

    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export default function IssueCard({ issue, idx, copied, onCopy, onAsk, repoUrl }) {
  const [expanded, setExpanded] = useState(false);
  const githubUrl = buildGithubUrl(repoUrl, issue.file, issue.line_start);

  return (
    <div className={t.card.wrapper}>
      <CardHeader
        title={issue.title}
        severity={issue.severity}
        category={issue.category}
        expanded={expanded}
        onToggle={() => setExpanded(!expanded)}
      />
      {expanded && (
        <CardBody
          issue={issue}
          githubUrl={githubUrl}
          copied={copied === idx}
          onCopy={(fix) => onCopy(fix, idx)}
          onAsk={onAsk}
        />
      )}
    </div>
  );
}
