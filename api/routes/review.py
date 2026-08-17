"""
api/routes/review.py

Endpoint: /review
"""

import json

from fastapi import APIRouter, HTTPException

from api.deps import get_pipeline, get_store
from api.models import ReviewRequest, ReviewResponse
from generation.prompts import build_review_prompt

router = APIRouter()

# Focused retrieval queries per review type — used instead of embedding
# the user's question, since a review has no single question.
REVIEW_QUERIES = {
    "general":        "error handling bugs edge cases missing validation",
    "security":       "authentication authorization SQL injection input validation secrets",
    "performance":    "slow queries N+1 caching bottleneck optimization",
    "error-handling": "try catch exception missing error handling failure modes",
}


@router.post("/review", response_model=ReviewResponse)
def review_code(request: ReviewRequest):
    """
    Analyze an indexed codebase for issues and suggest fixes.
    Retrieves key chunks and sends them to the LLM with a code-review prompt.
    """
    pipe = get_pipeline()

    store = get_store(request.index_name)
    if not store:
        raise HTTPException(status_code=404, detail=f"Index '{request.index_name}' not found.")

    query = REVIEW_QUERIES.get(request.focus, REVIEW_QUERIES["general"])
    query_vec = pipe.embedder.embed_one(query)
    results = store.search(query_vec, top_k=5)

    if not results:
        raise HTTPException(status_code=404, detail="No code found to review.")

    context = "\n\n".join([
        f"[{r['rel_path']}:{r['start_line']}-{r['end_line']}] {r['type']}: {r['name']}\n```\n{r['content']}\n```"
        for r in results
    ])

    response = pipe.generator.client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": build_review_prompt(request.focus, context)}],
        max_tokens=2000,
        temperature=0.1,
        reasoning_effort="low",
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="LLM returned invalid JSON. Try again.")

    return ReviewResponse(
        issues=data.get("issues", []),
        index_name=request.index_name,
        focus=request.focus,
    )
