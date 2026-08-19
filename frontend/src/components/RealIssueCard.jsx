/**
 * components/RealIssueCard.jsx
 *
 * One real, currently-open GitHub issue (labeled "good first issue" or
 * "help wanted") — fetched from the GitHub API, not inferred by the LLM.
 * Just links out to GitHub; there's nothing to draft since it's a real,
 * already-filed issue.
 */

import { theme as t } from "../styles/theme";

export default function RealIssueCard({ issue }) {
  const { number, title, url, labels, comments } = issue;

  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="block bg-gray-900 border border-gray-700 rounded-xl px-5 py-4 hover:border-green-600 transition-colors"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`${t.badge.base} ${t.badge.good}`}>#{number}</span>
          <span className="text-sm font-bold text-gray-100">{title}</span>
        </div>
        <span className={t.text.muted}>💬 {comments}</span>
      </div>
      <div className="flex items-center gap-2 flex-wrap mt-2">
        {labels.map((label) => (
          <span key={label} className={`${t.badge.base} ${t.badge.neutral}`}>
            {label}
          </span>
        ))}
      </div>
      <div className="text-xs text-blue-400 hover:underline mt-3">Open on GitHub ↗</div>
    </a>
  );
}
