"""
api/routes/query.py

Endpoints: /ask, /ask-multi
"""

import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from api.deps import cache_answer, get_cached_answer, get_indexing_jobs, get_pipeline, get_store
from api.models import AskMultiRequest, AskRequest, AskResponse, SourceChunk

router = APIRouter()


def _build_github_url(repo_url: str, rel_path: str, line: int = None) -> str | None:
    """
    Construct a GitHub link to a specific file and line.
    Returns None if repo_url is not a GitHub URL.
    """
    if not repo_url or "github.com" not in repo_url:
        return None
    # Normalize path separators (Windows uses backslashes)
    rel_path = rel_path.replace("\\", "/")
    base = repo_url.rstrip("/")
    url = f"{base}/blob/main/{rel_path}"
    if line:
        url += f"#L{line}"
    return url


def _build_sources(results: list[dict], repo_url: str) -> list[SourceChunk]:
    return [
        SourceChunk(
            score=r["score"],
            rel_path=r["rel_path"],
            name=r["name"],
            type=r["type"],
            start_line=r["start_line"],
            end_line=r["end_line"],
            content=r["content"],
            github_url=_build_github_url(repo_url, r["rel_path"], r["start_line"]),
        )
        for r in results
    ]


@router.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest):
    """
    Answer a question about an indexed repo.

    Retrieves top-k chunks and asks the LLM to generate an answer grounded
    in those chunks. Returns the answer plus the source chunks (shown as
    cards in the UI).

    First-turn questions (no history) are cached by (index, question) —
    history isn't part of the cache key since it changes the answer, so
    follow-up questions always hit the LLM fresh.
    """
    is_cacheable = not request.history
    if is_cacheable:
        cached = get_cached_answer(request.index_name, request.question)
        if cached:
            return AskResponse(**cached, index_name=request.index_name, question=request.question)

    pipe = get_pipeline()

    store = get_store(request.index_name)
    if not store:
        job = get_indexing_jobs().get(request.index_name)
        if job and job["status"] == "indexing":
            raise HTTPException(
                status_code=409,
                detail=f"Index '{request.index_name}' is still being built. Please wait.",
            )
        raise HTTPException(
            status_code=404,
            detail=f"Index '{request.index_name}' not found. Index the repo first.",
        )

    query_vec = pipe.embedder.embed_one(request.question)
    results = store.search(query_vec, top_k=request.top_k)

    if not results:
        raise HTTPException(
            status_code=404,
            detail="No relevant chunks found for that question.",
        )

    answer = pipe.generator.answer(
        question=request.question,
        chunks=results,
        history=request.history,
    )

    repo_url = pipe._load_repo_url(request.index_name) or ""
    sources = _build_sources(results, repo_url)

    if is_cacheable:
        cache_answer(request.index_name, request.question, {
            "answer": answer,
            "sources": sources,
        })

    return AskResponse(
        answer=answer,
        sources=sources,
        index_name=request.index_name,
        question=request.question,
    )


@router.post("/ask/stream")
def ask_question_stream(request: AskRequest):
    """
    Same as /ask, but streams the answer token-by-token over SSE instead
    of waiting for the full response.

    Event stream shape:
        event: sources   data: [SourceChunk dicts]   (sent first — retrieval
                                                        already happened)
        data: {"token": "..."}                        (one per answer token)
        event: done       data: {}                     (on success)
        event: error       data: {"detail": "..."}     (if the LLM call fails)
    """
    pipe = get_pipeline()

    store = get_store(request.index_name)
    if not store:
        job = get_indexing_jobs().get(request.index_name)
        if job and job["status"] == "indexing":
            raise HTTPException(
                status_code=409,
                detail=f"Index '{request.index_name}' is still being built. Please wait.",
            )
        raise HTTPException(
            status_code=404,
            detail=f"Index '{request.index_name}' not found. Index the repo first.",
        )

    query_vec = pipe.embedder.embed_one(request.question)
    results = store.search(query_vec, top_k=request.top_k)

    if not results:
        raise HTTPException(
            status_code=404,
            detail="No relevant chunks found for that question.",
        )

    repo_url = pipe._load_repo_url(request.index_name) or ""
    sources = _build_sources(results, repo_url)

    def generate():
        yield f"event: sources\ndata: {json.dumps([s.model_dump() for s in sources])}\n\n"
        try:
            for token in pipe.generator.answer_stream(
                question=request.question,
                chunks=results,
                history=request.history,
            ):
                yield f"data: {json.dumps({'token': token})}\n\n"
            yield "event: done\ndata: {}\n\n"
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'detail': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/ask-multi", response_model=AskResponse)
def ask_multi(request: AskMultiRequest):
    """
    Search across multiple indexes at once and generate one unified answer.
    Results from all repos are merged and ranked by score before sending to LLM.
    """
    pipe = get_pipeline()
    all_results = []

    for index_name in request.index_names:
        store = get_store(index_name)
        if not store:
            continue
        query_vec = pipe.embedder.embed_one(request.question)
        results = store.search(query_vec, top_k=request.top_k)
        # Tag each result with which repo it came from
        for r in results:
            r["repo"] = index_name
        all_results.extend(results)

    if not all_results:
        raise HTTPException(status_code=404, detail="No results found across any index.")

    # Sort all results by score — best chunks from any repo float to the top
    all_results.sort(key=lambda x: x["score"], reverse=True)

    # Take top 5 overall
    top_results = all_results[:5]

    answer = pipe.generator.answer(
        question=request.question,
        chunks=top_results,
        history=request.history,
    )

    sources = [
        SourceChunk(
            score=r["score"],
            rel_path=r["rel_path"],
            name=r["name"],
            type=r["type"],
            start_line=r["start_line"],
            end_line=r["end_line"],
            content=r["content"],
            github_url=_build_github_url(
                pipe._load_repo_url(r.get("repo", "")) or "",
                r["rel_path"],
                r["start_line"],
            ),
        )
        for r in top_results
    ]

    return AskResponse(
        answer=answer,
        sources=sources,
        index_name="multi: " + ", ".join(request.index_names),
        question=request.question,
    )
