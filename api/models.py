"""
api/models.py

All Pydantic request/response models in one place.
"""

from typing import Optional
from pydantic import BaseModel


# ── Index models ─────────────────────────────────────────────────────────────

class IndexRequest(BaseModel):
    """What the frontend sends when asking to index a repo."""
    repo_url: str           # e.g. "https://github.com/karpathy/micrograd"
    name: Optional[str] = None   # optional custom name, defaults to repo name
    force: bool = False     # if True, re-index even if index exists

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


# ── Query models ─────────────────────────────────────────────────────────────

class AskRequest(BaseModel):
    """What the frontend sends when asking a question."""
    question: str           # e.g. "how does backpropagation work?"
    index_name: str         # which index to search, e.g. "micrograd"
    top_k: int = 5          # how many chunks to retrieve
    history: list[dict] = []

class AskMultiRequest(BaseModel):
    question: str
    index_names: list[str]   # list of indexes to search
    top_k: int = 3           # chunks per repo (3 × repos = total results)
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
    github_url: Optional[str] = None

class AskResponse(BaseModel):
    """What we send back after answering a question."""
    answer: str             # the LLM's answer
    sources: list[SourceChunk]   # the chunks that were retrieved
    index_name: str
    question: str


# ── Review models ────────────────────────────────────────────────────────────

class ReviewRequest(BaseModel):
    index_name: str
    focus: str = "general"  # "general", "security", "performance", "error-handling"

class ReviewResponse(BaseModel):
    issues: list[dict]
    index_name: str
    focus: str


# ── Onboard models ───────────────────────────────────────────────────────────

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
    repo_url: Optional[str] = None


# ── Contribute models ────────────────────────────────────────────────────────

class ContributeRequest(BaseModel):
    index_name: str

class ContributeResponse(BaseModel):
    opportunities: list[dict]
    index_name: str
