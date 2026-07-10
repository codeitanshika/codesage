/**
 * components/IssueCard.jsx
 *
 * One expandable card per code review issue.
 * Shows severity, what/why/fix, GitHub link, and copy button.
 *
 * Props:
 *   issue   — issue object from /review API
 *   idx     — index for copy state tracking
 *   copied  — currently copied index (from parent state)
 *   onCopy  — handler to copy fix to clipboard
 *   onAsk   — handler to pre-fill chat with follow-up question
 *   repoUrl — GitHub repo URL for constructing file links
 */

import { useState } from "react";
import { buildGithubUrl } from "../utils/helpers";

const SEVERITY_STYLE = {
  high:   "bg-red-900 text-red-300 border-red-700",
  medium: "bg-yellow-900 text-yellow-300 border-yellow-700",
  low:    "bg-green-900 text-green-300 border-green-700",
};

export default function IssueCard({ issue, idx, copied, onCopy, onAsk, repoUrl }) {
  const [expanded, setExpanded] = useState(false);

  const githubUrl = buildGithubUrl(repoUrl, issue.file, issue.line_start);

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl overflow-hidden">

      {/* Header — click to expand */}
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

      {/* Expandable content */}
      {expanded && (
        <div className="px-4 py-3 flex flex-col gap-3 border-t border-gray-700">

          {/* File reference */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">📄</span>
            {githubUrl ? (
              <a
                href={githubUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-blue-400 font-mono hover:text-blue-300 hover:underline"
              >
                {issue.file?.replace(/\\/g, "/")}:{issue.line_start} ↗
              </a>
            ) : (
              <span className="text-xs text-blue-400 font-mono">
                {issue.file}:{issue.line_start}
              </span>
            )}
          </div>

          {/* What */}
          <div>
            <div className="text-xs text-gray-500 uppercase tracking-widest mb-1">What is the issue</div>
            <p className="text-sm text-gray-300">{issue.what}</p>
          </div>

          {/* Why it matters */}
          <div>
            <div className="text-xs text-gray-500 uppercase tracking-widest mb-1">Why it matters in this project</div>
            <p className="text-sm text-yellow-200">{issue.why_matters}</p>
          </div>

          {/* Current code */}
          <div>
            <div className="text-xs text-red-400 uppercase tracking-widest mb-1">Current code</div>
            <pre className="bg-gray-950 text-red-200 text-xs p-3 rounded-lg overflow-x-auto font-mono whitespace-pre-wrap">
              {issue.current_code}
            </pre>
          </div>

          {/* Suggested fix */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <div className="text-xs text-green-400 uppercase tracking-widest">Suggested fix</div>
              <button
                onClick={() => onCopy(issue.suggested_fix, idx)}
                className="text-xs text-gray-500 hover:text-green-400 cursor-pointer bg-transparent border-none"
              >
                {copied === idx ? "✓ copied" : "copy"}
              </button>
            </div>
            <pre className="bg-gray-950 text-green-200 text-xs p-3 rounded-lg overflow-x-auto font-mono whitespace-pre-wrap">
              {issue.suggested_fix}
            </pre>
          </div>

          {/* How fix helps */}
          <div>
            <div className="text-xs text-gray-500 uppercase tracking-widest mb-1">How the fix helps</div>
            <p className="text-sm text-green-300">{issue.how_fix_helps}</p>
          </div>

          {/* Ask about this */}
          <button
            onClick={() => onAsk(`Tell me more about the "${issue.title}" issue in ${issue.file}`)}
            className="text-xs text-left text-gray-400 border border-gray-700 rounded px-3 py-2 hover:border-blue-500 hover:text-blue-400 transition-colors cursor-pointer bg-transparent"
          >
            💬 Ask CodeSage about this issue
          </button>
        </div>
      )}
    </div>
  );
}
