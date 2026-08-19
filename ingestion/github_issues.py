"""
ingestion/github_issues.py

Responsibility: Fetch real, currently-open "good first issue" /
"help wanted" issues from a repo's GitHub Issues API — used to ground
/contribute in what maintainers have actually labeled as approachable,
instead of only what the LLM infers from code.

Never raises — this is supplementary data. Any failure (rate limit,
private repo, non-GitHub URL) just means an empty list, and the LLM-
inferred opportunities in /contribute still work on their own.

Usage:
    from ingestion.github_issues import fetch_good_first_issues
    issues = fetch_good_first_issues("https://github.com/karpathy/micrograd")
"""

import os
import re
import requests

GITHUB_API = "https://api.github.com"

# Common label spellings maintainers use for approachable issues.
# GitHub's `labels` query param ANDs comma-separated labels, so we need
# one request per label and merge the results ourselves for OR semantics.
BEGINNER_LABELS = ["good first issue", "help wanted"]


def _parse_owner_repo(repo_url: str) -> tuple[str, str] | None:
    """Extract (owner, repo) from a GitHub URL. Returns None if it isn't one."""
    match = re.match(
        r"https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$",
        (repo_url or "").strip(),
    )
    if not match:
        return None
    return match.group(1), match.group(2)


def fetch_good_first_issues(repo_url: str, limit: int = 5) -> list[dict]:
    """
    Fetch up to `limit` open issues labeled "good first issue" or
    "help wanted" for a GitHub repo.

    Returns a list of dicts:
        { number, title, url, labels, comments, created_at }
    Newest-first, deduplicated by issue number. Pull requests (which the
    GitHub issues endpoint also returns) are filtered out.
    """
    parsed = _parse_owner_repo(repo_url)
    if not parsed:
        return []
    owner, repo = parsed

    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    seen_numbers = set()
    issues = []

    for label in BEGINNER_LABELS:
        try:
            resp = requests.get(
                f"{GITHUB_API}/repos/{owner}/{repo}/issues",
                params={"state": "open", "labels": label, "per_page": limit},
                headers=headers,
                timeout=5,
            )
            resp.raise_for_status()
        except requests.RequestException:
            continue

        for item in resp.json():
            if "pull_request" in item or item["number"] in seen_numbers:
                continue
            seen_numbers.add(item["number"])
            issues.append({
                "number": item["number"],
                "title": item["title"],
                "url": item["html_url"],
                "labels": [l["name"] for l in item.get("labels", [])],
                "comments": item["comments"],
                "created_at": item["created_at"],
            })

    issues.sort(key=lambda i: i["created_at"], reverse=True)
    return issues[:limit]
