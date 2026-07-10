/**
 * components/SourceCard.jsx
 *
 * Expandable card showing one retrieved code chunk.
 * Shown below every chat answer when user clicks "show N sources".
 *
 * Props:
 *   chunk — source chunk object from the API
 *   index — position number (shown as #1, #2, etc.)
 */

import { useState } from "react";

export default function SourceCard({ chunk, index }) {
  const [open, setOpen] = useState(false);

  const score = Math.round(chunk.score * 100);
  const path = chunk.rel_path.replace(/\\/g, "/");

  return (
    <div className="mt-3 rounded-lg border border-gray-700 overflow-hidden">

      {/* Header — click to expand */}
      <div
        className="flex items-center justify-between px-3 py-2 bg-blue-950 cursor-pointer select-none"
        onClick={() => setOpen(!open)}
      >
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs px-2 py-0.5 rounded bg-blue-900 text-blue-300 border border-blue-700">
            #{index + 1}
          </span>

          {/* File path — clickable GitHub link if available */}
          {chunk.github_url ? (
            <a
              href={chunk.github_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs font-semibold text-blue-400 hover:text-blue-300 hover:underline"
              onClick={(e) => e.stopPropagation()}
            >
              {path} ↗
            </a>
          ) : (
            <span className="text-xs font-semibold text-blue-400">{path}</span>
          )}

          <span className="text-xs text-gray-500">
            :{chunk.start_line}–{chunk.end_line}
          </span>
          <span className="text-xs px-2 py-0.5 rounded bg-gray-800 text-gray-400 border border-gray-700">
            {chunk.type}: {chunk.name}
          </span>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <span
            className={`text-xs px-2 py-0.5 rounded border ${
              score > 50
                ? "bg-green-900 text-green-400 border-green-700"
                : "bg-gray-800 text-gray-400 border-gray-700"
            }`}
          >
            {score}% match
          </span>
          <span className="text-gray-500 text-xs">{open ? "▲" : "▼"}</span>
        </div>
      </div>

      {/* Expandable code block */}
      {open && (
        <pre className="p-4 text-xs text-blue-200 bg-gray-950 overflow-x-auto whitespace-pre-wrap break-words leading-relaxed font-mono">
          {chunk.content}
        </pre>
      )}
    </div>
  );
}
