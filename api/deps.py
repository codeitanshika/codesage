"""
api/deps.py

Shared dependencies — the pipeline instance and indexing jobs dict.
Imported by all route modules to avoid circular imports and to avoid
reloading the embedding model on every request.
"""

from collections import OrderedDict

from pipeline import CodeSagePipeline
from embedding.store import VectorStore

# Single shared pipeline instance — loaded once, reused across all requests
_pipeline = CodeSagePipeline()

# Tracks background indexing jobs: { index_name: { status, message } }
_indexing_jobs: dict[str, dict] = {}

# Loaded VectorStores, keyed by index name — avoids re-reading the FAISS
# index and chunks JSON from disk on every single request.
_store_cache: dict[str, VectorStore] = {}

# Answers to first-turn questions (no history), keyed by (index_name,
# normalized question) — avoids re-hitting Groq for repeated questions.
# Only first-turn questions are cached since history changes the answer.
_ASK_CACHE_MAX = 200
_ask_cache: "OrderedDict[tuple[str, str], dict]" = OrderedDict()


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
    """Evict a cached store, e.g. after re-indexing changes it on disk.
    Also drops any cached /ask answers for that index — they were
    generated against the old code and would now be stale."""
    _store_cache.pop(name, None)
    for key in [k for k in _ask_cache if k[0] == name]:
        _ask_cache.pop(key, None)


def _ask_cache_key(index_name: str, question: str) -> tuple[str, str]:
    return (index_name, question.strip().lower())


def get_cached_answer(index_name: str, question: str) -> dict | None:
    """Return a cached {answer, sources} payload, or None on a miss."""
    key = _ask_cache_key(index_name, question)
    if key not in _ask_cache:
        return None
    _ask_cache.move_to_end(key)
    return _ask_cache[key]


def cache_answer(index_name: str, question: str, payload: dict) -> None:
    key = _ask_cache_key(index_name, question)
    _ask_cache[key] = payload
    _ask_cache.move_to_end(key)
    if len(_ask_cache) > _ASK_CACHE_MAX:
        _ask_cache.popitem(last=False)
