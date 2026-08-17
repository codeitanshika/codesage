/**
 * App.jsx
 *
 * Root component — layout only.
 * All state and logic lives in useCodeSage hook.
 * All UI pieces live in components/.
 */

import { theme as t } from "./styles/theme";
import useCodeSage from "./hooks/useCodeSage";

import Sidebar         from "./components/Sidebar";
import Message         from "./components/Message";
import ReviewPanel     from "./components/ReviewPanel";
import OnboardPanel    from "./components/OnboardPanel";
import ContributePanel from "./components/ContributePanel";
import TabBar          from "./components/TabBar";

// ── Sub-components ────────────────────────────────────────────────────────────

function Header({ activeIndex, indexes, multiMode, onToggleMulti }) {
  if (!activeIndex) {
    return (
      <div className={t.header.root}>
        <span className={t.text.muted}>Select or index a repo to start chatting</span>
      </div>
    );
  }
  return (
    <div className={t.header.root}>
      <span className={`${t.badge.base} ${t.badge.live}`}>● live</span>
      <span className="text-sm font-semibold">{activeIndex}</span>
      <span className={t.text.muted}>— ask anything about this codebase</span>

      {indexes.length > 1 && (
        <button
          onClick={onToggleMulti}
          className={`ml-auto text-xs px-3 py-1 rounded border transition-colors cursor-pointer ${
            multiMode
              ? "bg-blue-900 text-blue-300 border-blue-600"
              : "text-gray-500 border-gray-600 hover:border-gray-400 bg-transparent"
          }`}
        >
          {multiMode ? "● searching all repos" : "search all repos"}
        </button>
      )}
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex-1 flex flex-col items-center justify-center text-center gap-4 text-gray-500">
      <div className="text-5xl">⚡</div>
      <div className="text-lg font-semibold text-gray-300">Ask anything about your codebase</div>
      <div className="text-sm max-w-md leading-relaxed">
        Index a GitHub repo on the left, then ask:<br />
        <span className="text-blue-400">"How does the diagnosis agent work?"</span><br />
        <span className="text-blue-400">"Where is authentication handled?"</span>
      </div>
    </div>
  );
}

function ChatArea({ messages, loading, bottomRef, onAsk }) {
  return (
    <div className={t.layout.messages}>
      {messages.length === 0 && <EmptyState />}
      {messages.map((msg, i) => <Message key={i} msg={msg} onAsk={onAsk} />)}
      {loading && <div className={t.message.loading}>Searching codebase and generating answer...</div>}
      <div ref={bottomRef} />
    </div>
  );
}

function InputBar({ input, activeIndex, loading, onChange, onAsk, onKey }) {
  return (
    <div className={t.inputBar.root}>
      <input
        className={t.input.chat}
        placeholder={activeIndex ? `Ask about ${activeIndex}...` : "Select a repo first"}
        value={input}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={onKey}
        disabled={!activeIndex || loading}
      />
      <button
        className={t.button.primary}
        onClick={onAsk}
        disabled={!activeIndex || loading || !input.trim()}
      >
        Ask
      </button>
    </div>
  );
}

function MainPanel({ hook }) {
  const { activeTab, setActiveTab, askAbout, activeIndex,
          reviewData, onboardReport, contributeData,
          messages, loading, bottomRef } = hook;

  if (activeTab === "review" && reviewData) {
    return (
      <ReviewPanel
        data={reviewData}
        indexName={activeIndex}
        onClose={() => setActiveTab("chat")}
        onAsk={askAbout}
      />
    );
  }

  if (activeTab === "onboard" && onboardReport) {
    return (
      <OnboardPanel
        report={onboardReport}
        indexName={activeIndex}
        onClose={() => setActiveTab("chat")}
        onQuestion={askAbout}
      />
    );
  }

  if (activeTab === "contribute" && contributeData) {
    return (
      <ContributePanel
        data={contributeData}
        indexName={activeIndex}
        onClose={() => setActiveTab("chat")}
        onAsk={askAbout}
      />
    );
  }

  return <ChatArea messages={messages} loading={loading} bottomRef={bottomRef} onAsk={askAbout} />;
}

// ── Main component ────────────────────────────────────────────────────────────

export default function App() {
  const hook = useCodeSage();

  return (
    <div className={t.layout.root}>

      <Sidebar
        repoUrl={hook.repoUrl}
        indexing={hook.indexing}
        indexMsg={hook.indexMsg}
        onRepoUrlChange={hook.setRepoUrl}
        onIndexSubmit={hook.handleIndexSubmit}
        indexes={hook.indexes}
        activeIndex={hook.activeIndex}
        onSelectIndex={hook.selectIndex}
        reviewFocus={hook.reviewFocus}
        reviewing={hook.reviewing}
        onReviewFocusChange={hook.setReviewFocus}
        onReview={hook.handleReview}
        contributing={hook.contributing}
        onContribute={hook.handleContribute}
      />

      <div className={t.layout.main}>
        <Header
          activeIndex={hook.activeIndex}
          indexes={hook.indexes}
          multiMode={hook.multiMode}
          onToggleMulti={() => hook.setMultiMode(!hook.multiMode)}
        />

        {hook.activeIndex && (
          <TabBar
            activeTab={hook.activeTab}
            onSelect={hook.setActiveTab}
            onboarding={hook.onboarding}
            reviewing={hook.reviewing}
            contributing={hook.contributing}
          />
        )}

        <MainPanel hook={hook} />

        <InputBar
          input={hook.input}
          activeIndex={hook.activeIndex}
          loading={hook.loading}
          onChange={hook.setInput}
          onAsk={hook.handleAsk}
          onKey={hook.handleKey}
        />
      </div>

    </div>
  );
}