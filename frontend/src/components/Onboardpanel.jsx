/**
 * components/OnboardPanel.jsx
 *
 * Auto-generated onboarding report shown when a repo is first selected.
 * Six sections: what it does, architecture, how to run,
 * key files, gotchas, and suggested questions.
 * Suggested questions are clickable — they pre-fill the chat input.
 * Does NOT fetch data — receives it via props from App.
 */

import { theme as t } from "../styles/theme";

// ── Sub-components ────────────────────────────────────────────────────────────

function PanelHeader({ indexName, onClose }) {
  return (
    <div className="flex items-center justify-between">
      <div>
        <div className={t.text.muted}>Onboarding Report</div>
        <div className="text-lg font-bold text-blue-400">{indexName}</div>
      </div>
      <button onClick={onClose} className={t.button.close}>
        Start chatting →
      </button>
    </div>
  );
}

function Section({ title, colorClass = t.text.sectionBlue, children }) {
  return (
    <div className={t.panel.section}>
      <div className={colorClass}>{title}</div>
      {children}
    </div>
  );
}

function HowToRun({ steps }) {
  return (
    <div className="flex flex-col gap-2 mt-2">
      {steps.map((step, i) => (
        <div key={i} className="flex gap-3 items-start">
          <span className={`${t.badge.base} ${t.badge.index} shrink-0 mt-0.5`}>
            {i + 1}
          </span>
          <span className="text-sm text-gray-300">
            {step.replace(/^Step \d+:\s*/, "")}
          </span>
        </div>
      ))}
    </div>
  );
}

function KeyFiles({ files }) {
  return (
    <div className="flex flex-col gap-2 mt-2">
      {files.map((kf, i) => (
        <div key={i} className="flex gap-3 items-start p-3 bg-gray-950 rounded-lg border border-gray-700">
          <span className="text-xs text-blue-400 shrink-0 mt-0.5">📄</span>
          <div>
            <div className="text-xs font-semibold text-blue-400 mb-0.5">{kf.file}</div>
            <div className={t.text.muted}>{kf.why}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

function Gotchas({ items }) {
  return (
    <div className="flex flex-col gap-2 mt-2">
      {items.map((g, i) => (
        <div key={i} className="flex gap-3 items-start p-3 bg-yellow-950 rounded-lg border border-yellow-800">
          <span className="text-yellow-500 text-xs shrink-0 mt-0.5">!</span>
          <span className="text-xs text-yellow-200">{g.replace(/^Gotcha \d+:\s*/, "")}</span>
        </div>
      ))}
    </div>
  );
}

function SuggestedQuestions({ questions, onQuestion }) {
  return (
    <div className="flex flex-col gap-2 mt-2">
      {questions.map((q, i) => (
        <button
          key={i}
          onClick={() => onQuestion(q)}
          className="text-left text-xs text-gray-300 p-3 bg-gray-950 rounded-lg border border-gray-700 hover:border-green-600 hover:text-green-300 transition-colors cursor-pointer"
        >
          {q}
        </button>
      ))}
      <div className={t.text.muted}>Click any question to send it to chat</div>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export default function OnboardPanel({ report, indexName, onClose, onQuestion }) {
  return (
    <div className={t.panel.root}>

      <PanelHeader indexName={indexName} onClose={onClose} />

      <Section title="What this project does">
        <p className="text-sm text-gray-200 leading-relaxed mt-2">{report.what_it_does}</p>
      </Section>

      <Section title="Architecture">
        <p className="text-sm text-gray-300 leading-relaxed mt-2">{report.architecture}</p>
      </Section>

      <Section title="How to run">
        <HowToRun steps={report.how_to_run} />
      </Section>

      <Section title="Key files to read first">
        <KeyFiles files={report.key_files} />
      </Section>

      <Section title="⚠ Gotchas for new contributors" colorClass={t.text.sectionYellow}>
        <Gotchas items={report.gotchas} />
      </Section>

      <Section title="Suggested questions to ask" colorClass={t.text.sectionGreen}>
        <SuggestedQuestions questions={report.suggested_questions} onQuestion={onQuestion} />
      </Section>

      <button onClick={onClose} className={`w-full py-3 rounded-xl ${t.button.indexItem}`}>
        Start chatting about this codebase →
      </button>

    </div>
  );
}