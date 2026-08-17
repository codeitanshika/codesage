/**
 * components/ContributionCard.jsx
 *
 * Displays one contribution opportunity as a document-style section.
 * Mirrors IssueCard.jsx's layout and conventions.
 */

import { theme as t } from "../styles/theme";
import { buildGithubUrl } from "../utils/helpers";

// ── Constants ─────────────────────────────────────────────────────────────────

const DIFFICULTY_STYLE = {
  "good-first-issue": "bg-green-900 text-green-300 border-green-700",
  medium:             "bg-yellow-900 text-yellow-300 border-yellow-700",
  advanced:           "bg-red-900 text-red-300 border-red-700",
};

// ── Sub-components ────────────────────────────────────────────────────────────

function ContributionHeader({ title, difficulty, category, effortEstimate, githubUrl, file, lineStart }) {
  return (
    <div className="flex items-start justify-between gap-4 mb-4">
      <div className="flex items-center gap-2 flex-wrap">
        <span className={`${t.badge.base} font-bold uppercase ${DIFFICULTY_STYLE[difficulty] || DIFFICULTY_STYLE.medium}`}>
          {difficulty}
        </span>
        <span className="text-base font-bold text-gray-100">{title}</span>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        <span className={t.text.muted}>{category?.replace("_", " ")} · {effortEstimate}</span>
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

export default function ContributionCard({ item, idx, copied, onCopy, onAsk, repoUrl }) {
  const { title, difficulty, category, file, line_start,
          description, suggested_approach,
          draft_pr_title, draft_pr_description, effort_estimate } = item;

  const githubUrl = buildGithubUrl(repoUrl, file, line_start);
  const prText = `${draft_pr_title}\n\n${draft_pr_description}`;

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl px-5 py-4">

      <ContributionHeader
        title={title}
        difficulty={difficulty}
        category={category}
        effortEstimate={effort_estimate}
        githubUrl={githubUrl}
        file={file}
        lineStart={line_start}
      />

      <DocSection label="What needs doing">
        <p className={t.text.body}>{description}</p>
      </DocSection>

      <DocSection label="Suggested approach" labelClass={t.text.sectionBlue}>
        <p className={t.text.blue}>{suggested_approach}</p>
      </DocSection>

      <DocSection label="Draft PR" labelClass={t.text.sectionGreen}>
        <CopyButton text={prText} copied={copied === idx} onCopy={(text) => onCopy(text, idx)} />
        <div className={`${t.code.block} ${t.code.green}`}>
          <div className="font-bold mb-1">{draft_pr_title}</div>
          <div>{draft_pr_description}</div>
        </div>
      </DocSection>

      <button
        onClick={() => onAsk(`Tell me more about "${title}" in ${file}`)}
        className={t.button.ghost}
      >
        💬 Ask CodeSage about this
      </button>

    </div>
  );
}
