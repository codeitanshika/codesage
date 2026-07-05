"""
api.py

The FastAPI backend for CodeSage.

This file is the bridge between your React frontend and the pipeline
you already built. It exposes your pipeline as HTTP endpoints that
any frontend (or anyone on the internet) can call.

Remember your pipeline.py? You used it like this in the terminal:
    pipe.index("https://github.com/...")
    pipe.query("how does auth work?", "my-index")

Now we wrap those same calls in HTTP endpoints:
    POST /index  → pipe.index(...)
    POST /ask    → pipe.query(...)
    GET  /status → check if index exists

Run with:
    uvicorn api:app --reload --port 8000
"""

from dotenv import load_dotenv

from embedding.store import VectorStore
load_dotenv()

import os
import time
import threading
from pathlib import Path
from typing import Optional
import json



from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from pipeline import CodeSagePipeline

def build_github_url(repo_url: str, rel_path: str, line: int = None) -> str | None:
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
# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="CodeSage API",
    description="Ask questions about any codebase using RAG",
    version="1.0.0",
)

# CORS — this is what allows your React frontend (running on localhost:5173)
# to talk to this backend (running on localhost:8000).
# Without this, the browser blocks cross-origin requests.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # in production you'd lock this to your frontend URL
    allow_methods=["*"],
    allow_headers=["*"],
)

# One shared pipeline instance — we don't want to reload the embedding model
# on every request. It loads once when the server starts, stays in memory.
# This is the same CodeSagePipeline you used in pipeline.py
pipe = CodeSagePipeline()

# Track indexing jobs so the frontend can poll for progress
# Structure: { index_name: { "status": "indexing"|"done"|"error", "message": str } }
indexing_jobs: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Request / Response models (Pydantic)
# ---------------------------------------------------------------------------
# Pydantic models define the shape of data coming in and going out.
# FastAPI uses them to validate requests and generate docs automatically.
# Think of them as the contract between frontend and backend.

class IndexRequest(BaseModel):
    """What the frontend sends when asking to index a repo."""
    repo_url: str           # e.g. "https://github.com/karpathy/micrograd"
    name: Optional[str] = None   # optional custom name, defaults to repo name
    force: bool = False     # if True, re-index even if index exists

class AskRequest(BaseModel):
    """What the frontend sends when asking a question."""
    question: str           # e.g. "how does backpropagation work?"
    index_name: str         # which index to search, e.g. "micrograd"
    top_k: int = 5          # how many chunks to retrieve
    history: list[dict] = []  


class SourceChunk(BaseModel):
    """One retrieved code chunk — shown as a source card in the UI."""
    score: float
    rel_path: str           # e.g. "micrograd/engine.py"
    name: str               # function/class name
    type: str               # "function", "class", "section", etc.
    start_line: int
    end_line: int
    content: str            # the actual code — shown highlighted in the UI
    github_url: str | None = None

class AskResponse(BaseModel):
    """What we send back after answering a question."""
    answer: str             # the LLM's answer
    sources: list[SourceChunk]   # the chunks that were retrieved
    index_name: str
    question: str

class IndexResponse(BaseModel):
    """What we send back after starting an index job."""
    index_name: str
    status: str             # "started", "already_exists", "error"
    message: str

class StatusResponse(BaseModel):
    """What we send back when checking if an index exists."""
    index_name: str
    exists: bool
    chunk_count: Optional[int] = None
    status: Optional[str] = None   # "indexing", "done", "error" if job running


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _name_from_url(url: str) -> str:
    """Derive an index name from a GitHub URL — same logic as main.py."""
    return url.rstrip("/").split("/")[-1].replace(".git", "")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    """Health check — lets you verify the server is running."""
    return {"message": "CodeSage API is running", "version": "1.0.0"}


@app.get("/status/{index_name}", response_model=StatusResponse)
def get_status(index_name: str):
    """
    Check if an index exists and is ready to query.

    The React frontend calls this:
    1. After submitting a repo URL — to show a loading spinner while indexing
    2. On page load — to restore the last used index

    This maps to VectorStore.exists() from your embedding/store.py
    """
    from embedding.store import VectorStore

    # Check if there's an active indexing job for this name
    job = indexing_jobs.get(index_name)
    if job:
        return StatusResponse(
            index_name=index_name,
            exists=False,
            status=job["status"],
        )

    store = VectorStore(name=index_name)
    if store.exists():
        store.load()
        return StatusResponse(
            index_name=index_name,
            exists=True,
            chunk_count=store.chunk_count,
            status="done",
        )

    return StatusResponse(index_name=index_name, exists=False)


@app.get("/indexes")
def list_indexes():
    """
    List all available indexes on disk.

    The React frontend uses this to show a dropdown of indexed repos
    so the user can switch between them.
    """
    index_dir = Path("indexes")
    if not index_dir.exists():
        return {"indexes": []}

    # Find all .faiss files — each one is an index
    names = [
        f.stem
        for f in index_dir.glob("*.faiss")
    ]
    return {"indexes": sorted(names)}


@app.post("/index", response_model=IndexResponse)
def index_repo(request: IndexRequest, background_tasks: BackgroundTasks):
    """
    Index a GitHub repo — clone, parse, embed, save to FAISS.

    This is the expensive operation (can take minutes for large repos).
    We run it in a background thread so the API doesn't hang.
    The frontend polls GET /status/{name} to check progress.

    This calls pipe.index() from your pipeline.py — the same function
    you called manually in the terminal with:
        python main.py index --repo https://github.com/...
    """
    repo_url = request.repo_url.strip()
    index_name = request.name or _name_from_url(repo_url)

    # If already indexed and not forcing, return immediately
    if not request.force:
        from embedding.store import VectorStore
        store = VectorStore(name=index_name)
        if store.exists():
            return IndexResponse(
                index_name=index_name,
                status="already_exists",
                message=f"Index '{index_name}' already exists. Use force=true to re-index.",
            )

    # Mark as indexing
    indexing_jobs[index_name] = {"status": "indexing", "message": "Starting..."}

    def run_indexing():
        """Runs in a background thread."""
        try:
            indexing_jobs[index_name]["message"] = "Cloning repo..."
            pipe.index(repo_url=repo_url, name=index_name, force=request.force)
            indexing_jobs[index_name] = {"status": "done", "message": "Indexing complete."}
        except Exception as e:
            indexing_jobs[index_name] = {"status": "error", "message": str(e)}

    # BackgroundTasks runs run_indexing() after sending the response
    # So the frontend gets an immediate "started" response, then polls for completion
    background_tasks.add_task(run_indexing)

    return IndexResponse(
        index_name=index_name,
        status="started",
        message=f"Indexing '{repo_url}' in background. Poll GET /status/{index_name} for progress.",
    )

@app.get("/repo-info/{index_name}")
def get_repo_info(index_name: str):
    """
    Returns the GitHub URL stored for this index.
    Used by the frontend to construct clickable GitHub links.
    """
    repo_url = pipe._load_repo_url(index_name)
    return {
        "index_name": index_name,
        "repo_url": repo_url,
        "has_url": repo_url is not None,
    }


@app.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest):
    """
    Answer a question about an indexed repo.

    This is what the frontend calls every time the user sends a message
    in the chat UI.

    Under the hood this calls:
    1. embedder.embed_one(question)        — from embedding/embedder.py
    2. store.search(query_vec, top_k)      — from embedding/store.py
    3. generator.answer(question, chunks)  — from generation/llm.py

    All wired together through pipe.query() from pipeline.py.

    Returns the answer + the source chunks (shown as cards in the UI).
    """
    from embedding.store import VectorStore

    # Check index exists
    store = VectorStore(name=request.index_name)
    if not store.exists():
        # Also check if it's currently being indexed
        job = indexing_jobs.get(request.index_name)
        if job and job["status"] == "indexing":
            raise HTTPException(
                status_code=409,
                detail=f"Index '{request.index_name}' is still being built. Please wait.",
            )
        raise HTTPException(
            status_code=404,
            detail=f"Index '{request.index_name}' not found. Index the repo first.",
        )

    # Embed question + retrieve chunks (from store.py)
    store.load()
    query_vec = pipe.embedder.embed_one(request.question)
    results = store.search(query_vec, top_k=request.top_k)

    if not results:
        raise HTTPException(
            status_code=404,
            detail="No relevant chunks found for that question.",
        )

    # Generate answer with Groq (from llm.py)
    answer = pipe.generator.answer(
        question=request.question,
        chunks=results,
        history=request.history,   

    )

    # Build source chunks for the frontend to display as cards
    repo_url = pipe._load_repo_url(request.index_name) or ""
    sources = [
        SourceChunk(
            score=r["score"],
            rel_path=r["rel_path"],
            name=r["name"],
            type=r["type"],
            start_line=r["start_line"],
            end_line=r["end_line"],
            content=r["content"],
            github_url=build_github_url(repo_url, r["rel_path"], r["start_line"]),
        )
        for r in results
    ]

    return AskResponse(
        answer=answer,
        sources=sources,
        index_name=request.index_name,
        question=request.question,
    )

class AskMultiRequest(BaseModel):
    question: str
    index_names: list[str]   # list of indexes to search
    top_k: int = 3           # chunks per repo (3 × repos = total results)
    history: list[dict] = []

@app.post("/ask-multi")
def ask_multi(request: AskMultiRequest):
    """
    Search across multiple indexes at once and generate one unified answer.
    Results from all repos are merged and ranked by score before sending to LLM.
    """
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
            github_url=build_github_url(
                pipe._load_repo_url(r.get("repo", "")) or "",
                r["rel_path"],
                r["start_line"]
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

class ReviewRequest(BaseModel):
    index_name: str
    focus: str = "general"  # "general", "security", "performance", "error-handling"

class ReviewResponse(BaseModel):
    issues: str
    index_name: str
    focus: str

@app.post("/review", response_model=ReviewResponse)
def review_code(request: ReviewRequest):
    """
    Analyze an indexed codebase for issues and suggest fixes.
    Retrieves key chunks and sends them to LLM with a code-review prompt.
    """
    from embedding.store import VectorStore

    store = VectorStore(name=request.index_name, index_dir="indexes")
    if not store.exists():
        raise HTTPException(status_code=404, detail=f"Index '{request.index_name}' not found.")
    store.load()

    # Use focused queries based on review type
    review_queries = {
        "general":        "error handling bugs edge cases missing validation",
        "security":       "authentication authorization SQL injection input validation secrets",
        "performance":    "slow queries N+1 caching bottleneck optimization",
        "error-handling": "try catch exception missing error handling failure modes",
    }

    query = review_queries.get(request.focus, review_queries["general"])
    query_vec = pipe.embedder.embed_one(query)
    results = store.search(query_vec, top_k=8)

    if not results:
        raise HTTPException(status_code=404, detail="No code found to review.")

    # Build context
    context = "\n\n".join([
        f"[{r['rel_path']}:{r['start_line']}-{r['end_line']}] {r['type']}: {r['name']}\n```\n{r['content']}\n```"
        for r in results
    ])

    review_prompt = f"""You are a senior software engineer doing a code review.

Focus area: {request.focus.upper()}

Review the following code chunks and identify REAL issues — not nitpicks.

{context}

For each issue found:
1. State the problem in one line
2. Show the exact file and line: `filename.py:line`
3. Show the problematic code (brief)
4. Show the fix with corrected code

Format each issue as:
### Issue N: <short title>
**File:** `path/to/file.py:line`
**Problem:** one sentence
**Suggested fix:**
**Current code:**
If no real issues found in a category, say so honestly.
Maximum 5 issues. Be specific, not generic."""

    response = pipe.generator.client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": review_prompt}
        ],
        max_tokens=2000,
        temperature=0.1,
    )

    return ReviewResponse(
        issues=response.choices[0].message.content,
        index_name=request.index_name,
        focus=request.focus,
    )

class OnboardRequest(BaseModel):
    index_name: str

class OnboardResponse(BaseModel):
    what_it_does: str
    how_to_run: list[str]
    key_files: list[dict]
    architecture: str
    gotchas: list[str]
    suggested_questions: list[str]
    index_name: str

@app.post("/onboard", response_model=OnboardResponse)
def onboard_repo(request: OnboardRequest):
    """
    Generate an onboarding report for an indexed repo.
    Retrieves key structural chunks and asks the LLM to explain
    the project as if onboarding a new contributor.
    """
    from embedding.store import VectorStore

    store = VectorStore(name=request.index_name, index_dir="indexes")
    if not store.exists():
        raise HTTPException(status_code=404, detail=f"Index '{request.index_name}' not found.")
    store.load()

    # Query for the most structural/overview chunks
    queries = [
        "what does this project do overview purpose",
        "how to run setup install requirements entry point",
        "main components architecture modules structure",
        "common errors gotchas warnings known issues",
    ]

    all_chunks = []
    for query in queries:
        vec = pipe.embedder.embed_one(query)
        results = store.search(vec, top_k=3)
        all_chunks.extend(results)

    # Deduplicate by rel_path
    seen = set()
    unique_chunks = []
    for c in all_chunks:
        if c["rel_path"] not in seen:
            seen.add(c["rel_path"])
            unique_chunks.append(c)

    # Build context
    context = "\n\n".join([
        f"[{c['rel_path']}:{c['start_line']}-{c['end_line']}]\n{c['content']}"
        for c in unique_chunks[:12]
    ])

    repo_url = pipe._load_repo_url(request.index_name) or ""

    prompt = f"""You are onboarding a new open source contributor to this codebase.

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

    response = pipe.generator.client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1500,
        temperature=0.1,
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
    )
    
# ---------------------------------------------------------------------------
# Run directly:
# python api.py
# or preferably:
# uvicorn api:app --reload --port 8000
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)