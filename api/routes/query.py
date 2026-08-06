"""
api/routes/query.py

Endpoints: /ask, /ask-multi
"""

from fastapi import APIRouter, HTTPException

from api.deps import get_indexing_jobs, get_pipeline
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
    """
    from embedding.store import VectorStore

    pipe = get_pipeline()

    store = VectorStore(name=request.index_name)
    if not store.exists():
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

    store.load()
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

    return AskResponse(
        answer=answer,
        sources=_build_sources(results, repo_url),
        index_name=request.index_name,
        question=request.question,
    )


@router.post("/ask-multi", response_model=AskResponse)
def ask_multi(request: AskMultiRequest):
    """
    Search across multiple indexes at once and generate one unified answer.
    Results from all repos are merged and ranked by score before sending to LLM.
    """
    from embedding.store import VectorStore

    pipe = get_pipeline()
    all_results = []

    for index_name in request.index_names:
        store = VectorStore(name=index_name, index_dir="indexes")
        if not store.exists():
            continue
        store.load()
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
