"""
embedding/embedder.py

Responsibility: Convert text chunks into vectors (embeddings) using
sentence-transformers — a free, local embedding model.

Key concept:
    Text  →  [0.21, -0.54, 0.87, ...]  (384 numbers)
    This list of numbers captures the *meaning* of the text.
    Similar meaning → similar numbers → close together in vector space.

Usage:
    from embedding.embedder import Embedder
    embedder = Embedder()
    vectors = embedder.embed(["def login(): ...", "class UserService: ..."])
    # vectors.shape → (2, 384)
"""

import os
import numpy as np
from pathlib import Path


# The model we use: all-MiniLM-L6-v2
# - 384-dimensional vectors (small = fast)
# - Downloads once (~90MB), then runs fully offline
# - Good balance of speed and quality for code search
MODEL_NAME = "all-MiniLM-L6-v2"


class Embedder:
    """
    Wraps sentence-transformers to embed text chunks into vectors.

    Lazy-loads the model on first use so importing this file is instant
    even if the model isn't downloaded yet.
    """

    def __init__(self, model_name: str = MODEL_NAME):
        self.model_name = model_name
        self._model = None  # loaded on first call to embed()

    def _load_model(self):
        """Download (first time) and load the embedding model."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            print(f"Loading embedding model: {self.model_name}")
            print("  (downloads ~90MB on first run, then cached locally)")
            self._model = SentenceTransformer(self.model_name)
            print(f"  Model loaded. Vector size: {self._model.get_embedding_dimension()}")
        return self._model

    def embed(self, texts: list[str], batch_size: int = 64, show_progress: bool = True) -> np.ndarray:
        """
        Embed a list of texts into vectors.

        Args:
            texts:         list of strings to embed
            batch_size:    how many texts to process at once (tune based on RAM)
            show_progress: show a tqdm progress bar

        Returns:
            numpy array of shape (len(texts), 384)
            Each row is the embedding vector for one text.

        Example:
            vectors = embedder.embed(["hello world", "def login():"])
            # vectors.shape → (2, 384)
            # vectors[0] → embedding for "hello world"
            # vectors[1] → embedding for "def login():"
        """
        if not texts:
            return np.array([])

        model = self._load_model()

        # sentence-transformers handles batching internally
        # normalize_embeddings=True makes cosine similarity = dot product
        # which is faster and what FAISS expects
        vectors = model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            normalize_embeddings=True,   # important for cosine similarity
            convert_to_numpy=True,
        )

        return vectors.astype("float32")  # FAISS requires float32

    def embed_one(self, text: str) -> np.ndarray:
        """
        Embed a single string. Convenience wrapper for query embedding.

        Returns:
            1D numpy array of shape (384,)

        Example:
            query_vec = embedder.embed_one("how does authentication work?")
            # query_vec.shape → (384,)
        """
        vectors = self.embed([text], show_progress=False)
        return vectors[0]

    def similarity(self, vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        """
        Compute cosine similarity between two vectors.
        Returns a float between -1 and 1. Higher = more similar.

        Since we normalize embeddings, this is just the dot product.

        Example:
            v1 = embedder.embed_one("how does login work")
            v2 = embedder.embed_one("authentication function")
            score = embedder.similarity(v1, v2)
            # score → ~0.85 (very similar meaning)
        """
        return float(np.dot(vec_a, vec_b))

    @property
    def vector_size(self) -> int:
        """The number of dimensions in each vector (384 for MiniLM)."""
        return self._load_model().get_sentence_embedding_dimension()


def embed_chunks(chunks: list[dict], embedder: Embedder = None) -> tuple[list[dict], np.ndarray]:
    """
    Embed a list of chunk dicts (from parser.py) and return
    (chunks, vectors) — keeping them aligned so index i in chunks
    matches row i in vectors.

    Args:
        chunks:   list of chunk dicts from ingestion/parser.py
        embedder: optional Embedder instance (creates one if not provided)

    Returns:
        (chunks, vectors)
        - chunks:  same list, unchanged
        - vectors: numpy array of shape (len(chunks), 384)

    The caller stores both together so they stay in sync.
    """
    if embedder is None:
        embedder = Embedder()

    print(f"\nEmbedding {len(chunks)} chunks...")

    # Build the text we'll embed for each chunk.
    # We prepend file path + name so the vector captures location context
    # not just code content. This helps retrieval distinguish between
    # two functions with the same body in different files.
    texts = []
    for chunk in chunks:
        # Format: "file: path/to/file.py\nfunction: my_func\n\n<code>"
        header = f"file: {chunk['rel_path']}\n{chunk['type']}: {chunk['name']}\n\n"
        texts.append(header + chunk["content"])

    vectors = embedder.embed(texts)
    print(f"  Done. vectors.shape = {vectors.shape}")

    return chunks, vectors


# ---------------------------------------------------------------------------
# Quick test — run directly:
# python -m embedding.embedder
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    embedder = Embedder()

    # Test 1: basic embedding
    print("\n--- Test 1: Basic embedding ---")
    sentences = [
        "def login(username, password): ...",
        "def authenticate_user(user, pwd): ...",
        "def calculate_tax(income, rate): ...",
    ]
    vectors = embedder.embed(sentences, show_progress=False)
    print(f"Input:  {len(sentences)} sentences")
    print(f"Output: {vectors.shape}  ← (num_sentences, vector_size)")

    # Test 2: similarity — the core of RAG retrieval
    print("\n--- Test 2: Similarity scores ---")
    query = "how does user authentication work"
    query_vec = embedder.embed_one(query)

    print(f"Query: '{query}'")
    print()
    for sentence, vec in zip(sentences, vectors):
        score = embedder.similarity(query_vec, vec)
        bar = "█" * int(score * 30)
        print(f"  {score:.3f} {bar}")
        print(f"         '{sentence[:60]}'")

    print()
    print("Notice: the two auth-related functions score high,")
    print("the tax function scores low — even with different words.")
    print("This is exactly how RAG retrieval works.")

    # Test 3: embed a real chunk (simulated)
    print("\n--- Test 3: Chunk embedding (as used in pipeline) ---")
    fake_chunks = [
        {
            "content": "def get_user(self, user_id: int):\n    return db.query(User).filter(User.id == user_id).first()",
            "rel_path": "app/services/user_service.py",
            "type": "function",
            "name": "get_user",
            "start_line": 12,
            "end_line": 14,
        },
        {
            "content": "def hash_password(password: str) -> str:\n    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()",
            "rel_path": "app/utils/auth.py",
            "type": "function",
            "name": "hash_password",
            "start_line": 5,
            "end_line": 7,
        },
    ]

    chunks, vecs = embed_chunks(fake_chunks, embedder)
    print(f"Chunks embedded: {len(chunks)}")
    print(f"Vector matrix:   {vecs.shape}")
    print(f"\nFirst vector (first 8 of 384 dims): {vecs[0][:8].tolist()}")