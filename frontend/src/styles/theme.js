/**
 * styles/theme.js
 *
 * Single source of truth for all Tailwind class strings.
 * Every component imports from here — no inline class walls.
 *
 * Structure mirrors the UI:
 *   layout   → page-level containers
 *   sidebar  → left panel
 *   card     → generic card patterns
 *   badge    → small label chips
 *   code     → code block display
 *   text     → typography
 *   button   → interactive elements
 *   input    → form inputs
 *   panel    → full-screen panels (review, onboard)
 */

export const theme = {

  // ── Layout ────────────────────────────────────────────────────────────────
  layout: {
    root:     "flex h-screen bg-gray-950 text-gray-100 font-mono overflow-hidden",
    main:     "flex flex-col flex-1 min-h-0",
    messages: "flex-1 overflow-y-auto px-6 py-6 flex flex-col gap-5",
  },

  // ── Sidebar ───────────────────────────────────────────────────────────────
  sidebar: {
    root:       "w-72 bg-gray-900 border-r border-gray-700 flex flex-col shrink-0",
    logo:       "px-5 py-4 border-b border-gray-700",
    logoText:   "text-lg font-bold text-blue-400 tracking-tight",
    section:    "px-4 py-4 border-b border-gray-700",
    label:      "text-xs text-gray-500 uppercase tracking-widest mb-2",
    footer:     "px-5 py-3 border-t border-gray-700 text-xs text-gray-600",
    repoList:   "overflow-y-auto",
    repoItem: (active) =>
      `px-5 py-2.5 text-xs cursor-pointer border-l-2 transition-all break-all ${
        active
          ? "text-blue-400 bg-blue-950 border-blue-400"
          : "text-gray-400 border-transparent hover:text-gray-200 hover:bg-gray-800"
      }`,
  },

  // ── Header ────────────────────────────────────────────────────────────────
  header: {
    root: "px-6 py-3 border-b border-gray-700 bg-gray-900 flex items-center gap-3",
  },

  // ── Card (generic) ────────────────────────────────────────────────────────
  card: {
    wrapper:  "rounded-xl border border-gray-700 bg-gray-900 overflow-hidden",
    header:   "flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-gray-800 transition-colors",
    body:     "px-4 py-3 flex flex-col gap-3 border-t border-gray-700",
  },

  // ── Source card (chat answers) ────────────────────────────────────────────
  sourceCard: {
    wrapper: "mt-3 rounded-lg border border-gray-700 overflow-hidden",
    header:  "flex items-center justify-between px-3 py-2 bg-blue-950 cursor-pointer select-none",
  },

  // ── Badge ─────────────────────────────────────────────────────────────────
  badge: {
    // Severity
    high:     "bg-red-900 text-red-300 border-red-700",
    medium:   "bg-yellow-900 text-yellow-300 border-yellow-700",
    low:      "bg-green-900 text-green-300 border-green-700",
    // Match score
    good:     "bg-green-900 text-green-400 border-green-700",
    neutral:  "bg-gray-800 text-gray-400 border-gray-700",
    // Chunk index
    index:    "bg-blue-900 text-blue-300 border-blue-700",
    // Status
    live:     "bg-green-900 text-green-400 border-green-700",
    base:     "text-xs px-2 py-0.5 rounded border",
  },

  // ── Code ──────────────────────────────────────────────────────────────────
  code: {
    block:  "bg-gray-950 text-xs p-3 rounded-lg overflow-x-auto font-mono whitespace-pre-wrap",
    red:    "text-red-200",
    green:  "text-green-200",
    blue:   "text-blue-200",
    // Inline code
    inline: "bg-gray-950 text-blue-300 rounded px-1.5 py-0.5 text-xs font-mono",
    // Full preview block (source card)
    preview: "p-4 text-xs text-blue-200 bg-gray-950 overflow-x-auto whitespace-pre-wrap break-words leading-relaxed font-mono",
  },

  // ── Text ──────────────────────────────────────────────────────────────────
  text: {
    label:    "text-xs uppercase tracking-widest mb-1",
    muted:    "text-xs text-gray-500",
    body:     "text-sm text-gray-300",
    yellow:   "text-sm text-yellow-200",
    green:    "text-sm text-green-300",
    blue:     "text-xs text-blue-400 font-mono",
    sectionRed:   "text-xs text-red-400 uppercase tracking-widest mb-1",
    sectionGreen: "text-xs text-green-400 uppercase tracking-widest mb-1",
    sectionGray:  "text-xs text-gray-500 uppercase tracking-widest mb-1",
    sectionBlue:  "text-xs text-blue-400 uppercase tracking-widest mb-1",
    sectionYellow:"text-xs text-yellow-500 uppercase tracking-widest mb-1",
  },

  // ── Button ────────────────────────────────────────────────────────────────
  button: {
    primary:  "bg-blue-500 hover:bg-blue-400 text-gray-950 font-bold text-sm px-5 rounded-lg transition-colors disabled:opacity-50 cursor-pointer",
    ghost:    "text-xs text-gray-400 border border-gray-700 rounded px-3 py-2 hover:border-blue-500 hover:text-blue-400 transition-colors cursor-pointer bg-transparent",
    copy:     "text-xs text-gray-500 hover:text-green-400 cursor-pointer bg-transparent border-none",
    purple:   "w-full bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs py-2 rounded-lg transition-colors disabled:opacity-50 cursor-pointer",
    close:    "text-xs text-gray-500 border border-gray-600 rounded px-3 py-1 hover:border-gray-400 cursor-pointer bg-transparent",
    tab: (active) =>
      `text-xs px-3 py-1 rounded border cursor-pointer transition-colors ${
        active
          ? "bg-purple-900 text-purple-300 border-purple-600"
          : "text-gray-500 border-gray-700 hover:border-gray-500 bg-transparent"
      }`,
    indexItem: "mt-2 w-full bg-blue-500 hover:bg-blue-400 text-gray-950 font-bold text-xs py-2 rounded-lg transition-colors disabled:opacity-50 cursor-pointer",
  },

  // ── Input ─────────────────────────────────────────────────────────────────
  input: {
    base:     "w-full bg-gray-950 border border-gray-700 rounded-lg px-3 py-2 text-xs text-gray-100 placeholder-gray-600 outline-none focus:border-blue-500 transition-colors font-mono",
    chat:     "flex-1 bg-gray-950 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-gray-100 placeholder-gray-600 outline-none focus:border-blue-500 transition-colors font-mono disabled:opacity-50",
    select:   "w-full bg-gray-950 border border-gray-700 rounded-lg px-3 py-2 text-xs text-gray-100 outline-none font-mono mb-2 cursor-pointer",
  },

  // ── Message bubbles ───────────────────────────────────────────────────────
  message: {
    user:   "self-end bg-blue-950 border border-blue-800 rounded-tl-xl rounded-tr-xl rounded-bl-xl px-4 py-2 max-w-[70%] text-sm leading-relaxed",
    bot:    "self-start bg-gray-800 border border-gray-700 rounded-tr-xl rounded-br-xl rounded-bl-xl px-4 py-3 max-w-[80%] text-sm leading-relaxed",
    system: "self-center text-xs text-gray-500 bg-gray-800 border border-gray-700 rounded-full px-4 py-1",
    loading:"self-start bg-gray-800 border border-gray-700 rounded-tr-xl rounded-br-xl rounded-bl-xl px-4 py-3 text-sm text-gray-400",
  },

  // ── Panel (full-screen overlays) ──────────────────────────────────────────
  panel: {
    root:     "flex-1 overflow-y-auto px-6 py-6 flex flex-col gap-6",
    section:  "bg-gray-900 border border-gray-700 rounded-xl p-5",
    title:    "text-lg font-bold",
    subtitle: "text-xs text-gray-500 uppercase tracking-widest mb-1",
  },

  // ── Tabs (top-level nav — Chat / Onboard / Review / Contribute) ───────────
  tabs: {
    bar: "flex gap-1 px-6 border-b border-gray-700 bg-gray-900 shrink-0",
    tab: (active) =>
      `px-4 py-3 text-sm font-medium cursor-pointer border-b-2 transition-colors ${
        active
          ? "text-blue-400 border-blue-400"
          : "text-gray-500 border-transparent hover:text-gray-300 hover:border-gray-600"
      }`,
  },

  // ── Input bar (bottom of chat) ────────────────────────────────────────────
  inputBar: {
    root: "px-6 py-4 border-t border-gray-700 bg-gray-900 flex gap-3",
  },
};