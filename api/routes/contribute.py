"""
api/routes/contribute.py

Endpoint: /contribute
"""

import json

from fastapi import APIRouter, HTTPException

from api.deps import get_pipeline, get_store
from api.models import ContributeRequest, ContributeResponse
from generation.prompts import build_contribute_prompt
from ingestion.github_issues import fetch_good_first_issues

router = APIRouter()

# Fixed retrieval query — surfaces code likely to hold beginner-friendly
# contribution opportunities (unfinished work, gaps, small bugs).
CONTRIBUTE_QUERY = "TODO FIXME unimplemented stub missing tests missing docs simple bug beginner friendly"


@router.post("/contribute", response_model=ContributeResponse)
def find_contributions(request: ContributeRequest):
    """
    Analyze an indexed codebase for good first issues and suggest fixes.
    Retrieves key chunks and sends them to the LLM with a contribution-finding prompt.
    """
    pipe = get_pipeline()

    store = get_store(request.index_name)
    if not store:
        raise HTTPException(status_code=404, detail=f"Index '{request.index_name}' not found.")

    query_vec = pipe.embedder.embed_one(CONTRIBUTE_QUERY)
    results = store.search(query_vec, top_k=8)

    if not results:
        raise HTTPException(status_code=404, detail="No code found to analyze.")

    context = "\n\n".join([
        f"[{r['rel_path']}:{r['start_line']}-{r['end_line']}] {r['type']}: {r['name']}\n```\n{r['content']}\n```"
        for r in results
    ])

    repo_url = pipe._load_repo_url(request.index_name)
    real_issues = fetch_good_first_issues(repo_url) if repo_url else []

    response = pipe.generator.client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": build_contribute_prompt(context, real_issues)}],
        max_tokens=4000,
        temperature=0.1,
        reasoning_effort="medium",
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

    return ContributeResponse(
        opportunities=data.get("opportunities", []),
        real_issues=real_issues,
        index_name=request.index_name,
    )
