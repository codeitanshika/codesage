/**
 * components/IssueCard.jsx
 *
 * One expandable card per code review issue.
 * Shows severity, what/why/fix, GitHub link, and copy button.
 */

import { useState } from "react";
import { theme as t } from "../styles/theme";
import { buildGithubUrl } from "../utils/helpers";

// ── Sub-components ────────────────────────────────────────────────────────────

function SeverityBadge({ severity }) {
  const style = t.badge[severity] || t.badge.low;
  return (
    <span className={`${t.badge.base} font-bold uppercase ${style}`}>
      {severity}
    </span>
  );
}

function FileLink({ file, githubUrl, lineStart }) {
  const label = `${file?.replace(/\\/g, "/")}:${lineStart}`;
  if (githubUrl) {
    return (
      <a href={githubUrl} target="_blank" rel="noopener noreferrer"
        className="text-xs text-blue-400 font-mono hover:text-blue-300 hover:underline">
        {label} ↗
      </a>
    );
  }
  return <span className={t.text.blue}>{label}</span>;
}

function SectionLabel({ text, className = t.text.sectionGray }) {
  return <div className={className}>{text}</div>;
}

function CodeBlock({ code, colorClass }) {
  return (
    <pre className={`${t.code.block} ${colorClass}`}>{code}</pre>
  );
}

function CopyButton({ onCopy, copied }) {
  return (
    <button onClick={onCopy} className={t.button.copy}>
      {copied ? "✓ copied" : "copy"}
    </button>
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
  const {
    file, line_start, what, why_matters,
    current_code, suggested_fix, how_fix_helps, title,
  } = issue;

  return (
    <div className={t.card.body}>

      <div className="flex items-center gap-2">
        <span className={t.text.muted}>📄</span>
        <FileLink file={file} githubUrl={githubUrl} lineStart={line_start} />
      </div>

      <div>
        <SectionLabel text="What is the issue" />
        <p className={t.text.body}>{what}</p>
      </div>

      <div>
        <SectionLabel text="Why it matters in this project" />
        <p className={t.text.yellow}>{why_matters}</p>
      </div>

      <div>
        <SectionLabel text="Current code" className={t.text.sectionRed} />
        <CodeBlock code={current_code} colorClass={t.code.red} />
      </div>

      <div>
        <div className="flex items-center justify-between mb-1">
          <SectionLabel text="Suggested fix" className={t.text.sectionGreen} />
          <CopyButton onCopy={() => onCopy(suggested_fix)} copied={copied} />
        </div>
        <CodeBlock code={suggested_fix} colorClass={t.code.green} />
      </div>

      <div>
        <SectionLabel text="How the fix helps" />
        <p className={t.text.green}>{how_fix_helps}</p>
      </div>

      <button
        onClick={() => onAsk(`Tell me more about the "${title}" issue in ${file}`)}
        className={t.button.ghost}
      >
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
