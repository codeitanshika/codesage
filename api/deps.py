"""
api/deps.py

Shared dependencies — the pipeline instance and indexing jobs dict.
Imported by all route modules to avoid circular imports and to avoid
reloading the embedding model on every request.
"""

from pipeline import CodeSagePipeline

# Single shared pipeline instance — loaded once, reused across all requests
_pipeline = CodeSagePipeline()

# Tracks background indexing jobs: { index_name: { status, message } }
_indexing_jobs: dict[str, dict] = {}


def get_pipeline() -> CodeSagePipeline:
    return _pipeline


def get_indexing_jobs() -> dict:
    return _indexing_jobs
