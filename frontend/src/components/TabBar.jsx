/**
 * components/TabBar.jsx
 *
 * Persistent top-level navigation: Chat / Onboard / Review / Contribute.
 * Switching tabs never loses data or triggers a re-fetch — each tab's
 * content lives in useCodeSage state and just gets shown/hidden.
 */

import { theme as t } from "../styles/theme";

const TABS = [
  { id: "chat",       label: "Chat",       icon: "💬" },
  { id: "onboard",    label: "Onboard",    icon: "📋" },
  { id: "review",     label: "Review",     icon: "🔍" },
  { id: "contribute", label: "Contribute", icon: "🌱" },
];

function Spinner() {
  return (
    <span className="inline-block w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin" />
  );
}

export default function TabBar({ activeTab, onSelect, onboarding, reviewing, contributing }) {
  const loadingByTab = { onboard: onboarding, review: reviewing, contribute: contributing };

  return (
    <div className={t.tabs.bar}>
      {TABS.map(({ id, label, icon }) => (
        <button
          key={id}
          onClick={() => onSelect(id)}
          className={t.tabs.tab(activeTab === id)}
        >
          <span className="mr-1.5">{loadingByTab[id] ? <Spinner /> : icon}</span>
          {label}
        </button>
      ))}
    </div>
  );
}
