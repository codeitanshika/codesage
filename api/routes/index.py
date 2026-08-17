"""
api/routes/index.py

Endpoints: /index, /status/{name}, /indexes, /repo-info/{name}
"""

from pathlib import Path

from fastapi import APIRouter, BackgroundTasks

from api.deps import get_indexing_jobs, get_pipeline, get_store, invalidate_store
from api.models import IndexRequest, IndexResponse, StatusResponse

router = APIRouter()


def _name_from_url(url: str) -> str:
    """Derive an index name from a GitHub URL — same logic as main.py."""
    return url.rstrip("/").split("/")[-1].replace(".git", "")


@router.get("/")
def root():
    """Health check — lets you verify the server is running."""
    return {"message": "CodeSage API is running", "version": "1.0.0"}


@router.get("/status/{index_name}", response_model=StatusResponse)
def get_status(index_name: str):
    """
    Check if an index exists and is ready to query.

    The React frontend calls this:
    1. After submitting a repo URL — to show a loading spinner while indexing
    2. On page load — to restore the last used index
    """
    jobs = get_indexing_jobs()

    # Check if there's an active indexing job for this name
    job = jobs.get(index_name)
    if job:
        return StatusResponse(
            index_name=index_name,
            exists=False,
            status=job["status"],
        )

    store = get_store(index_name)
    if store:
        return StatusResponse(
            index_name=index_name,
            exists=True,
            chunk_count=store.chunk_count,
            status="done",
        )

    return StatusResponse(index_name=index_name, exists=False)


@router.get("/indexes")
def list_indexes():
    """
    List all available indexes on disk.

    The React frontend uses this to show a dropdown of indexed repos
    so the user can switch between them.
    """
    index_dir = Path("indexes")
    if not index_dir.exists():
        return {"indexes": []}

    names = [f.stem for f in index_dir.glob("*.faiss")]
    return {"indexes": sorted(names)}


@router.get("/repo-info/{index_name}")
def get_repo_info(index_name: str):
    """
    Returns the GitHub URL stored for this index.
    Used by the frontend to construct clickable GitHub links.
    """
    pipe = get_pipeline()
    repo_url = pipe._load_repo_url(index_name)
    return {
        "index_name": index_name,
        "repo_url": repo_url,
        "has_url": repo_url is not None,
    }


@router.post("/index", response_model=IndexResponse)
def index_repo(request: IndexRequest, background_tasks: BackgroundTasks):
    """
    Index a GitHub repo — clone, parse, embed, save to FAISS.

    This is the expensive operation (can take minutes for large repos).
    We run it in a background thread so the API doesn't hang.
    The frontend polls GET /status/{name} to check progress.
    """
    pipe = get_pipeline()
    jobs = get_indexing_jobs()

    repo_url = request.repo_url.strip()
    index_name = request.name or _name_from_url(repo_url)

    # If already indexed and not forcing, return immediately
    if not request.force and get_store(index_name):
        return IndexResponse(
            index_name=index_name,
            status="already_exists",
            message=f"Index '{index_name}' already exists. Use force=true to re-index.",
        )

    # Mark as indexing
    jobs[index_name] = {"status": "indexing", "message": "Starting..."}

    def run_indexing():
        """Runs in a background thread."""
        try:
            jobs[index_name]["message"] = "Cloning repo..."
            pipe.index(repo_url=repo_url, name=index_name, force=request.force)
            invalidate_store(index_name)  # force fresh load next time it's fetched
            jobs[index_name] = {"status": "done", "message": "Indexing complete."}
        except Exception as e:
            jobs[index_name] = {"status": "error", "message": str(e)}

    # BackgroundTasks runs run_indexing() after sending the response
    # So the frontend gets an immediate "started" response, then polls for completion
    background_tasks.add_task(run_indexing)

    return IndexResponse(
        index_name=index_name,
        status="started",
        message=f"Indexing '{repo_url}' in background. Poll GET /status/{index_name} for progress.",
    )
