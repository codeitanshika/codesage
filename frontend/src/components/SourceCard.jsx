/**
 * components/SourceCard.jsx
 *
 * Expandable card showing one retrieved code chunk.
 * Shown below every chat answer when user clicks "show N sources".
 */

import { useState } from "react";
import { theme as t } from "../styles/theme";

// ── Sub-components ────────────────────────────────────────────────────────────

function MatchBadge({ score }) {
  const style = score > 50 ? t.badge.good : t.badge.neutral;
  return (
    <span className={`${t.badge.base} ${style}`}>
      {score}% match
    </span>
  );
}

function ChunkLabel({ type, name }) {
  return (
    <span className={`${t.badge.base} ${t.badge.neutral}`}>
      {type}: {name}
    </span>
  );
}

function FileLink({ path, githubUrl, startLine, endLine }) {
  return (
    <div className="flex items-center gap-2">
      {githubUrl ? (
        <a
          href={githubUrl}
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
      <span className={t.text.muted}>:{startLine}–{endLine}</span>
    </div>
  );
}

function CardHeader({ chunk, path, score, open, onToggle }) {
  return (
    <div className={t.sourceCard.header} onClick={onToggle}>
      <div className="flex items-center gap-2 flex-wrap">
        <span className={`${t.badge.base} ${t.badge.index}`}>
          #{chunk.index + 1}
        </span>
        <FileLink
          path={path}
          githubUrl={chunk.github_url}
          startLine={chunk.start_line}
          endLine={chunk.end_line}
        />
        <ChunkLabel type={chunk.type} name={chunk.name} />
      </div>
      <div className="flex items-center gap-2 shrink-0">
        <MatchBadge score={score} />
        <span className={t.text.muted}>{open ? "▲" : "▼"}</span>
      </div>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export default function SourceCard({ chunk, index }) {
  const [open, setOpen] = useState(false);

  const score = Math.round(chunk.score * 100);
  const path = chunk.rel_path.replace(/\\/g, "/");
  const chunkWithIndex = { ...chunk, index };

  return (
    <div className={t.sourceCard.wrapper}>
      <CardHeader
        chunk={chunkWithIndex}
        path={path}
        score={score}
        open={open}
        onToggle={() => setOpen(!open)}
      />
      {open && (
        <pre className={t.code.preview}>{chunk.content}</pre>
      )}
    </div>
  );
}
