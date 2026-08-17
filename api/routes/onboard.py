"""
api/routes/onboard.py

Endpoint: /onboard
"""

import json

from fastapi import APIRouter, HTTPException

from api.deps import get_pipeline, get_store
from api.models import OnboardRequest, OnboardResponse
from generation.prompts import build_onboard_prompt

router = APIRouter()

# Fixed structural queries used to retrieve an overview of the repo,
# instead of embedding a user question.
ONBOARD_QUERIES = [
    "what does this project do overview purpose",
    "how to run setup install requirements entry point",
    "main components architecture modules structure",
    "common errors gotchas warnings known issues",
]


@router.post("/onboard", response_model=OnboardResponse)
def onboard_repo(request: OnboardRequest):
    """
    Generate an onboarding report for an indexed repo.
    Retrieves key structural chunks and asks the LLM to explain
    the project as if onboarding a new contributor.
    """
    pipe = get_pipeline()

    store = get_store(request.index_name)
    if not store:
        raise HTTPException(status_code=404, detail=f"Index '{request.index_name}' not found.")

    # Query for the most structural/overview chunks
    all_chunks = []
    for query in ONBOARD_QUERIES:
        vec = pipe.embedder.embed_one(query)
        results = store.search(vec, top_k=2)
        all_chunks.extend(results)

    # Deduplicate by rel_path
    seen = set()
    unique_chunks = []
    for c in all_chunks:
        if c["rel_path"] not in seen:
            seen.add(c["rel_path"])
            unique_chunks.append(c)

    context = "\n\n".join([
        f"[{c['rel_path']}:{c['start_line']}-{c['end_line']}]\n{c['content']}"
        for c in unique_chunks[:6]
    ])

    response = pipe.generator.client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": build_onboard_prompt(context)}],
        max_tokens=1500,
        temperature=0.1,
        reasoning_effort="low",
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown fences if LLM adds them anyway
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="LLM returned invalid JSON. Try again.")

    return OnboardResponse(
        what_it_does=data.get("what_it_does", ""),
        how_to_run=data.get("how_to_run", []),
        key_files=data.get("key_files", []),
        architecture=data.get("architecture", ""),
        gotchas=data.get("gotchas", []),
        suggested_questions=data.get("suggested_questions", []),
        index_name=request.index_name,
        repo_url=pipe._load_repo_url(request.index_name),
    )
