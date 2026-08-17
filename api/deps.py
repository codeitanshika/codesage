"""
api/deps.py

Shared dependencies — the pipeline instance and indexing jobs dict.
Imported by all route modules to avoid circular imports and to avoid
reloading the embedding model on every request.
"""

from pipeline import CodeSagePipeline
from embedding.store import VectorStore

# Single shared pipeline instance — loaded once, reused across all requests
_pipeline = CodeSagePipeline()

# Tracks background indexing jobs: { index_name: { status, message } }
_indexing_jobs: dict[str, dict] = {}

# Loaded VectorStores, keyed by index name — avoids re-reading the FAISS
# index and chunks JSON from disk on every single request.
_store_cache: dict[str, VectorStore] = {}


def get_pipeline() -> CodeSagePipeline:
    return _pipeline


def get_indexing_jobs() -> dict:
    return _indexing_jobs


def get_store(name: str) -> VectorStore | None:
    """Return the cached VectorStore for this index, loading it on first use.
    Returns None if no index exists on disk for this name."""
    if name in _store_cache:
        return _store_cache[name]

    store = VectorStore(name=name, index_dir="indexes")
    if not store.exists():
        return None

    store.load()
    _store_cache[name] = store
    return store


def invalidate_store(name: str) -> None:
    """Evict a cached store, e.g. after re-indexing changes it on disk."""
    _store_cache.pop(name, None)
