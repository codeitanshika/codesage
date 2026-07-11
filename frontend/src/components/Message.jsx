/**
 * components/Message.jsx
 * Single chat message bubble — handles user, assistant, and system roles.
 */

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { theme as t } from "../styles/theme";
import { downloadReview } from "../utils/helpers";
import SourceCard from "./SourceCard";

// ── Sub-components ────────────────────────────────────────────────────────────

function SystemMessage({ content }) {
  return <div className={t.message.system}>{content}</div>;
}

function UserMessage({ content }) {
  return <div className={t.message.user}>{content}</div>;
}

function MarkdownContent({ content }) {
  return (
    <ReactMarkdown
      components={{
        code({ children, className }) {
          const isBlock = className?.includes("language-");
          return isBlock ? (
            <pre className={`${t.code.block} ${t.code.blue} rounded-md my-2`}>
              <code>{children}</code>
            </pre>
          ) : (
            <code className={t.code.inline}>{children}</code>
          );
        },
      }}
    >
      {content}
    </ReactMarkdown>
  );
}

function SourcesToggle({ sources, showSources, onToggle }) {
  if (!sources?.length) return null;
  return (
    <div className="mt-3">
      <button onClick={onToggle} className={t.button.close}>
        {showSources ? "▲ hide" : "▼ show"} {sources.length} source{sources.length > 1 ? "s" : ""}
      </button>
      {showSources && sources.map((chunk, i) => (
        <SourceCard key={i} chunk={chunk} index={i} />
      ))}
    </div>
  );
}

function ReviewDownload({ msg }) {
  if (!msg.isReview) return null;
  return (
    <button
      onClick={() => downloadReview(msg.content, msg.reviewMeta.indexName, msg.reviewMeta.focus)}
      className="mt-3 text-xs text-purple-400 border border-purple-700 rounded px-3 py-1 hover:border-purple-400 transition-colors cursor-pointer bg-transparent font-mono"
    >
      ↓ download review
    </button>
  );
}

function AssistantMessage({ msg }) {
  const [showSources, setShowSources] = useState(false);

  return (
    <div className={t.message.bot}>
      <div className="prose prose-invert prose-sm max-w-none">
        <MarkdownContent content={msg.content} />
      </div>
      <ReviewDownload msg={msg} />
      <SourcesToggle
        sources={msg.sources}
        showSources={showSources}
        onToggle={() => setShowSources(!showSources)}
      />
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export default function Message({ msg }) {
  if (msg.role === "system")    return <SystemMessage content={msg.content} />;
  if (msg.role === "user")      return <UserMessage content={msg.content} />;
  return <AssistantMessage msg={msg} />;
}