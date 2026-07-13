/**
 * components/IssueCard.jsx
 *
 * Displays one code review issue as a document-style section.
 * All content visible — no expand/collapse needed.
 */

import { theme as t } from "../styles/theme";
import { buildGithubUrl } from "../utils/helpers";

// ── Constants ─────────────────────────────────────────────────────────────────

const SEVERITY_STYLE = {
  high:   "bg-red-900 text-red-300 border-red-700",
  medium: "bg-yellow-900 text-yellow-300 border-yellow-700",
  low:    "bg-green-900 text-green-300 border-green-700",
};

// ── Sub-components ────────────────────────────────────────────────────────────

function IssueHeader({ title, severity, category, githubUrl, file, lineStart }) {
  return (
    <div className="flex items-start justify-between gap-4 mb-4">
      <div className="flex items-center gap-2 flex-wrap">
        <span className={`${t.badge.base} font-bold uppercase ${SEVERITY_STYLE[severity] || SEVERITY_STYLE.low}`}>
          {severity}
        </span>
        <span className="text-base font-bold text-gray-100">{title}</span>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        <span className={t.text.muted}>{category?.replace("_", " ")}</span>
        {githubUrl ? (
          <a href={githubUrl} target="_blank" rel="noopener noreferrer"
            className="text-xs text-blue-400 font-mono hover:text-blue-300 hover:underline">
            {file?.replace(/\\/g, "/")}:{lineStart} ↗
          </a>
        ) : (
          <span className="text-xs text-blue-400 font-mono">
            {file?.replace(/\\/g, "/")}:{lineStart}
          </span>
        )}
      </div>
    </div>
  );
}

function DocSection({ label, labelClass = t.text.sectionGray, children }) {
  return (
    <div className="mb-3">
      <div className={labelClass}>{label}</div>
      {children}
    </div>
  );
}

function CopyButton({ text, copied, onCopy }) {
  return (
    <button onClick={() => onCopy(text)} className={`${t.button.copy} ml-auto block mb-1`}>
      {copied ? "✓ copied" : "copy"}
    </button>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export default function IssueCard({ issue, idx, copied, onCopy, onAsk, repoUrl }) {
  const { title, severity, category, file, line_start,
          what, why_matters, current_code, suggested_fix, how_fix_helps } = issue;

  const githubUrl = buildGithubUrl(repoUrl, file, line_start);

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl px-5 py-4">

      <IssueHeader
        title={title}
        severity={severity}
        category={category}
        githubUrl={githubUrl}
        file={file}
        lineStart={line_start}
      />

      <DocSection label="What is the issue">
        <p className={t.text.body}>{what}</p>
      </DocSection>

      <DocSection label="Why it matters in this project">
        <p className={t.text.yellow}>{why_matters}</p>
      </DocSection>

      <DocSection label="Current code" labelClass={t.text.sectionRed}>
        <pre className={`${t.code.block} ${t.code.red}`}>{current_code}</pre>
      </DocSection>

      <DocSection label="Suggested fix" labelClass={t.text.sectionGreen}>
        <CopyButton text={suggested_fix} copied={copied === idx} onCopy={(text) => onCopy(text, idx)} />
        <pre className={`${t.code.block} ${t.code.green}`}>{suggested_fix}</pre>
      </DocSection>

      <DocSection label="How the fix helps">
        <p className={t.text.green}>{how_fix_helps}</p>
      </DocSection>

      <button
        onClick={() => onAsk(`Tell me more about "${title}" in ${file}`)}
        className={t.button.ghost}
      >
        💬 Ask CodeSage about this issue
      </button>

    </div>
  );
}