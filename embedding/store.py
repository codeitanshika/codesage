"""
embedding/store.py

Responsibility: Store chunk vectors in a FAISS index so we can search
them instantly at query time.

What is FAISS?
    FAISS (Facebook AI Similarity Search) is a library that stores vectors
    and finds the closest ones to a query vector — extremely fast.

    Think of it like a dictionary, but instead of looking up by exact key,
    you look up by "nearest meaning".

    Without FAISS: compare query vector against every chunk one by one → slow
    With FAISS:    index organises vectors spatially → search in milliseconds
                   even with 100,000+ chunks

On disk we save two files:
    chunks.json   — the chunk dicts (content, file path, line numbers, etc.)
    index.faiss   — the FAISS index (the vectors)

They stay in sync: row i in the FAISS index = chunks[i] in the JSON.

Usage:
    from embedding.store import VectorStore
    store = VectorStore("my_index")
    store.build(chunks, vectors)       # index + save to disk
    store.save()                       # explicit save
    store.load()                       # load from disk
    results = store.search(query_vec, top_k=5)
"""

import os
import json
import numpy as np
from pathlib import Path


# Default directory where indexes are saved
DEFAULT_INDEX_DIR = "indexes"


class VectorStore:
    """
    Wraps FAISS to store, save, load, and search chunk embeddings.

    Each VectorStore corresponds to one indexed repo. You can have
    multiple stores for multiple repos.

    Args:
        name:      a name for this index (e.g. "fastapi", "my-project")
        index_dir: directory to save/load indexes from
    """

    def __init__(self, name: str, index_dir: str = DEFAULT_INDEX_DIR):
        self.name = name
        self.index_dir = Path(index_dir)
        self.index_path = self.index_dir / f"{name}.faiss"
        self.chunks_path = self.index_dir / f"{name}.chunks.json"

        self._index = None   # FAISS index object
        self._chunks = []    # list of chunk dicts, aligned with index rows

    # ------------------------------------------------------------------
    # Building the index
    # ------------------------------------------------------------------

    def build(self, chunks: list[dict], vectors: np.ndarray) -> None:
        """
        Build a FAISS index from chunks and their embedding vectors,
        then save both to disk.

        Args:
            chunks:  list of chunk dicts from ingestion/parser.py
            vectors: numpy float32 array of shape (len(chunks), vector_dim)

        After calling this, the index is ready to search immediately.
        """
        import faiss

        if len(chunks) != vectors.shape[0]:
            raise ValueError(
                f"Mismatch: {len(chunks)} chunks but {vectors.shape[0]} vectors. "
                "They must be the same length and in the same order."
            )

        vector_dim = vectors.shape[1]  # 384 for all-MiniLM-L6-v2

        print(f"\nBuilding FAISS index...")
        print(f"  Chunks  : {len(chunks)}")
        print(f"  Vectors : {vectors.shape}")
        print(f"  Dim     : {vector_dim}")

        # IndexFlatIP = "Flat Inner Product" index
        # "Flat" means we store all vectors exactly (no compression/approximation)
        # "IP" = Inner Product = dot product
        # Since our vectors are normalised (done in embedder.py), dot product
        # equals cosine similarity — so highest score = most similar meaning.
        #
        # For small-medium repos (< 100k chunks), Flat is perfect.
        # For very large repos you'd switch to IndexIVFFlat or IndexHNSW
        # but that's overkill here.
        self._index = faiss.IndexFlatIP(vector_dim)

        # Add all vectors to the index in one shot
        self._index.add(vectors)
        self._chunks = chunks

        print(f"  Index built. Total vectors stored: {self._index.ntotal}")

        # Save immediately after building
        self.save()

    # ------------------------------------------------------------------
    # Saving and loading
    # ------------------------------------------------------------------

    def save(self) -> None:
        """
        Persist the FAISS index and chunk metadata to disk.
        Creates the index directory if it doesn't exist.
        """
        import faiss

        if self._index is None:
            raise RuntimeError("No index to save. Call build() first.")

        self.index_dir.mkdir(parents=True, exist_ok=True)

        # Save the FAISS binary index
        faiss.write_index(self._index, str(self.index_path))

        # Save chunk metadata as JSON
        with open(self.chunks_path, "w", encoding="utf-8") as f:
            json.dump(self._chunks, f, ensure_ascii=False, indent=2)

        index_size_mb = self.index_path.stat().st_size / 1_000_000
        print(f"\nSaved index to {self.index_dir}/")
        print(f"  {self.name}.faiss        ({index_size_mb:.1f} MB)")
        print(f"  {self.name}.chunks.json  ({len(self._chunks)} chunks)")

    def load(self) -> None:
        """
        Load a previously saved index from disk.
        Raises FileNotFoundError if the index doesn't exist.
        """
        import faiss

        if not self.index_path.exists():
            raise FileNotFoundError(
                f"No saved index found at {self.index_path}\n"
                f"Run build() first to create one."
            )

        print(f"Loading index: {self.name}")
        self._index = faiss.read_index(str(self.index_path))

        with open(self.chunks_path, "r", encoding="utf-8") as f:
            self._chunks = json.load(f)

        print(f"  Loaded {self._index.ntotal} vectors, {len(self._chunks)} chunks")

    def exists(self) -> bool:
        """Returns True if a saved index exists on disk for this name."""
        return self.index_path.exists() and self.chunks_path.exists()

    # ------------------------------------------------------------------
    # Searching
    # ------------------------------------------------------------------

    def search(self, query_vector: np.ndarray, top_k: int = 5) -> list[dict]:
        """
        Find the top-k most similar chunks to a query vector.

        Args:
            query_vector: 1D numpy array of shape (vector_dim,)
                          — embed your question first using Embedder.embed_one()
            top_k:        how many results to return (default 5)

        Returns:
            list of result dicts, sorted by similarity (highest first):
            [
                {
                    "score":      float,  # cosine similarity (0-1, higher = better)
                    "content":    str,    # the actual code/text
                    "rel_path":   str,    # e.g. "fastapi/routing.py"
                    "type":       str,    # "function", "class", "section", etc.
                    "name":       str,    # function/class name
                    "start_line": int,
                    "end_line":   int,
                },
                ...
            ]

        Example:
            query_vec = embedder.embed_one("how does authentication work?")
            results = store.search(query_vec, top_k=5)
            for r in results:
                print(f"{r['score']:.3f}  {r['rel_path']}:{r['start_line']}  {r['name']}")
        """
        if self._index is None:
            raise RuntimeError("Index not loaded. Call load() or build() first.")

        # FAISS expects a 2D array: (num_queries, vector_dim)
        # We're searching with one query at a time, so reshape to (1, dim)
        query_2d = query_vector.reshape(1, -1).astype("float32")

        # search() returns:
        #   scores  — shape (1, top_k): similarity scores
        #   indices — shape (1, top_k): which rows in the index matched
        scores, indices = self._index.search(query_2d, top_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                # FAISS returns -1 when there aren't enough vectors
                # (e.g. asking for top_k=5 but only 3 chunks exist)
                continue

            chunk = self._chunks[idx]
            results.append({
                "score":      float(score),
                "content":    chunk["content"],
                "rel_path":   chunk["rel_path"],
                "file_path":  chunk.get("file_path", ""),
                "type":       chunk["type"],
                "name":       chunk["name"],
                "start_line": chunk["start_line"],
                "end_line":   chunk["end_line"],
            })

        return results

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def chunk_count(self) -> int:
        """Number of chunks in the index."""
        return len(self._chunks)

    def __repr__(self):
        status = f"{self._index.ntotal} vectors" if self._index else "not loaded"
        return f"VectorStore(name={self.name!r}, {status})"


# ---------------------------------------------------------------------------
# Manual smoke test moved to tests/test_store.py — run: python tests/test_store.py
# ---------------------------------------------------------------------------