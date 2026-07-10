/**
 * utils/helpers.js
 * 
 * Pure utility functions — no React, no axios.
 * Testable in isolation.
 */

/**
 * Download a code review as a markdown file.
 */
export function downloadReview(content, indexName, focus) {
  const text = [
    `# CodeSage Review — ${indexName}`,
    `Focus: ${focus}`,
    `Date: ${new Date().toLocaleDateString()}`,
    "",
    content,
  ].join("\n");

  const blob = new Blob([text], { type: "text/markdown" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `review-${indexName}-${focus}.md`;
  a.click();
  URL.revokeObjectURL(url);
}

/**
 * Construct a GitHub link to a specific file and line.
 * Returns null if repoUrl is not a GitHub URL.
 */
export function buildGithubUrl(repoUrl, relPath, lineStart) {
  if (!repoUrl || !relPath || !repoUrl.includes("github.com")) return null;
  const normalizedPath = relPath.replace(/\\/g, "/");
  const url = `${repoUrl.trimEnd("/")}/blob/main/${normalizedPath}`;
  return lineStart ? `${url}#L${lineStart}` : url;
}

/**
 * Derive an index name from a GitHub URL.
 * "https://github.com/user/my-repo" → "my-repo"
 */
export function nameFromUrl(url) {
  return url.trim().split("/").pop().replace(".git", "");
}

/**
 * Filter messages to only user/assistant turns for LLM history.
 * Slices to last N turns to avoid token limits.
 */
export function buildHistory(messages, maxTurns = 6) {
  return messages
    .filter((m) => m.role === "user" || m.role === "assistant")
    .map((m) => ({ role: m.role, content: m.content }))
    .slice(-maxTurns);
}