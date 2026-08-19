"""
generation/prompts.py

All LLM prompts in one place — the chat system prompt, the code review
prompt, and the onboarding report prompt. Previously these were scattered
across generation/llm.py and api.py; keeping them here means one place to
tune AI behavior.
"""

# ---------------------------------------------------------------------------
# Chat — used by LLMGenerator.answer() for /ask and /ask-multi
# ---------------------------------------------------------------------------

CHAT_SYSTEM_PROMPT = """You are CodeSage, an expert code assistant that answers questions about software repositories.

You are given:
1. A question about a codebase
2. Relevant code chunks retrieved from that codebase (with file paths and line numbers)

Your answer style — CODE FIRST:
- Lead with the most relevant code snippet from the chunks (use markdown code blocks)
- Add a file reference immediately after: `filename.py:line_number`
- Keep explanation SHORT — 2-3 sentences max per point
- Use bullet points, not paragraphs
- If multiple files are involved, show each one's key snippet
- End with a one-line summary of the overall flow

Rules:
- Only use code from the provided chunks — never invent code
- If chunks don't contain enough info, say so in one line
- No long introductions, no "Based on the provided code chunks..."
- Talk like a senior dev explaining to a teammate, not a textbook"""


# ---------------------------------------------------------------------------
# Code review — used by /review
# ---------------------------------------------------------------------------

def build_review_prompt(focus: str, context: str) -> str:
    """Build the code-review prompt for a given focus area and retrieved context."""
    return f"""You are a senior software engineer doing a code review.

Focus area: {focus.upper()}

Review the following code chunks and identify REAL issues.

{context}

Respond with ONLY valid JSON, no markdown, no backticks:
{{
  "issues": [
    {{
      "title": "short issue title",
      "severity": "high|medium|low",
      "category": "security|performance|code_quality|error_handling|setup|understanding",
      "file": "path/to/file.py",
      "line_start": 10,
      "line_end": 20,
      "what": "one sentence: what is the problem",
      "why_matters": "one sentence: why this matters specifically in this project",
      "current_code": "the problematic code snippet",
      "suggested_fix": "the corrected code",
      "how_fix_helps": "one sentence: how the fix improves things"
    }}
  ]
}}

Rules:
- Maximum 5 issues
- Only real issues, not nitpicks
- Be specific to this codebase, not generic advice
- Pure JSON only, no other text"""


# ---------------------------------------------------------------------------
# Onboarding report — used by /onboard
# ---------------------------------------------------------------------------

def build_onboard_prompt(context: str) -> str:
    """Build the onboarding-report prompt for the retrieved structural context."""
    return f"""You are onboarding a new open source contributor to this codebase.

Analyze the following code chunks and generate a structured onboarding report.

{context}

Respond with ONLY valid JSON, no markdown, no backticks, exactly this structure:
{{
  "what_it_does": "2-3 sentence explanation of what this project does and its purpose",
  "how_to_run": [
    "Step 1: ...",
    "Step 2: ...",
    "Step 3: ..."
  ],
  "key_files": [
    {{"file": "path/to/file.py", "why": "one sentence on why this file matters"}},
    {{"file": "path/to/file.py", "why": "one sentence on why this file matters"}}
  ],
  "architecture": "2-3 sentences explaining how the main components connect and interact",
  "gotchas": [
    "Gotcha 1: ...",
    "Gotcha 2: ..."
  ],
  "suggested_questions": [
    "How does X work?",
    "Where is Y implemented?",
    "What happens when Z fails?"
  ]
}}

Rules:
- key_files: list the 4-5 most important files only
- how_to_run: concrete steps a developer would actually follow
- gotchas: real things that would trip up a new contributor
- suggested_questions: 5 questions that would help understand this codebase deeply
- Respond with pure JSON only"""


# ---------------------------------------------------------------------------
# Contribution opportunities — used by /contribute
# ---------------------------------------------------------------------------

def build_contribute_prompt(context: str, existing_issues: list[dict] = None) -> str:
    """Build the contribution-opportunities prompt for the retrieved context.

    existing_issues: real open GitHub issues already filed for this repo
    (from ingestion/github_issues.py) — passed in so the LLM doesn't
    suggest something that's already been claimed.
    """
    existing_block = ""
    if existing_issues:
        titles = "\n".join(f"- {i['title']}" for i in existing_issues)
        existing_block = f"""

These issues are already open on GitHub — do NOT suggest anything that duplicates them:
{titles}"""

    return f"""You are helping a new open-source contributor find good first issues in this codebase.

Analyze the following code chunks and identify REAL opportunities to contribute — bugs, missing tests, missing docs, TODOs, small refactors.

{context}{existing_block}

Respond with ONLY valid JSON, no markdown, no backticks:
{{
  "opportunities": [
    {{
      "title": "short opportunity title",
      "difficulty": "good-first-issue|medium|advanced",
      "category": "bug|missing-test|missing-docs|todo|refactor",
      "file": "path/to/file.py",
      "line_start": 10,
      "line_end": 20,
      "description": "one or two sentences: what's missing or wrong",
      "suggested_approach": "one or two sentences: how a contributor would tackle this",
      "draft_pr_title": "a ready-to-use PR title",
      "draft_pr_description": "a short ready-to-use PR description",
      "effort_estimate": "e.g. 15 min, 1-2 hours, half day"
    }}
  ]
}}

Rules:
- Maximum 5 opportunities
- Only real, actionable opportunities, not nitpicks
- Be specific to this codebase, not generic advice
- Pure JSON only, no other text"""
