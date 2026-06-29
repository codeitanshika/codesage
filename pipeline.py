"""
pipeline.py

Responsibility: Wire all modules together into one clean RAG pipeline.

This is the brain of CodeSage. It connects:
    ingestion  (clone + parse)
    embedding  (embed + store)
    retrieval  (search)
    generation (LLM answer)

Two modes:
    1. INDEX  — given a repo URL/path, build and save the vector index
    2. QUERY  — given a question, retrieve relevant chunks and generate an answer

Usage:
    from pipeline import CodeSagePipeline

    pipe = CodeSagePipeline()

    # Index a repo (do this once)
    pipe.index(repo_url="https://github.com/tiangolo/fastapi", name="fastapi")

    # Ask questions (do this as many times as you want)
    answer = pipe.query(question="how does routing work?", index_name="fastapi")
    print(answer)
"""

import os
import time
from pathlib import Path

from ingestion.clone import load_repo, cleanup_repo
from ingestion.parser import parse_repo
from embedding.embedder import Embedder, embed_chunks
from embedding.store import VectorStore
from generation.llm import LLMGenerator


class CodeSagePipeline:
    """
    Full RAG pipeline for codebase Q&A.

    Keeps the embedder and LLM generator as instance variables so they're
    loaded once and reused across multiple queries (loading them each time
    would be slow).
    """

    def __init__(self, index_dir: str = "indexes"):
        self.index_dir = index_dir
        self._embedder = None    # lazy loaded
        self._generator = None   # lazy loaded

    @property
    def embedder(self) -> Embedder:
        if self._embedder is None:
            self._embedder = Embedder()
        return self._embedder

    @property
    def generator(self) -> LLMGenerator:
        if self._generator is None:
            self._generator = LLMGenerator()
        return self._generator

    # ------------------------------------------------------------------
    # Step 1: INDEX
    # ------------------------------------------------------------------

    def index(self, repo_url: str, name: str = None, force: bool = False) -> VectorStore:
        """
        Clone a repo, parse it, embed all chunks, and save the FAISS index.

        Args:
            repo_url: GitHub URL or local path to the repo
            name:     name for this index (defaults to repo name from URL)
            force:    if True, re-index even if an index already exists

        Returns:
            VectorStore: the built and saved index

        Example:
            pipe.index("https://github.com/tiangolo/fastapi", name="fastapi")
            # Creates indexes/fastapi.faiss and indexes/fastapi.chunks.json
        """
        # Derive index name from URL if not provided
        if name is None:
            name = repo_url.rstrip("/").split("/")[-1]
            name = name.replace(".git", "")

        store = VectorStore(name=name, index_dir=self.index_dir)

        # Skip if already indexed (unless forced)
        if store.exists() and not force:
            print(f"Index '{name}' already exists. Loading it.")
            print(f"  (Use force=True to re-index)")
            store.load()
            return store

        print(f"\n{'='*50}")
        print(f"  INDEXING: {repo_url}")
        print(f"  Index name: {name}")
        print(f"{'='*50}\n")

        total_start = time.time()

        # --- Step 1: Clone / load the repo ---
        print("Step 1/4: Fetching repo...")
        t = time.time()
        file_paths, repo_root = load_repo(repo_url)
        print(f"  Done in {time.time()-t:.1f}s\n")

        # --- Step 2: Parse into chunks ---
        print("Step 2/4: Parsing files into chunks...")
        t = time.time()
        chunks = parse_repo(file_paths, repo_root)
        print(f"  Done in {time.time()-t:.1f}s\n")

        if not chunks:
            raise RuntimeError("No chunks extracted. Check that the repo has supported file types.")

        # --- Step 3: Embed chunks ---
        print("Step 3/4: Embedding chunks...")
        t = time.time()
        chunks, vectors = embed_chunks(chunks, self.embedder)
        print(f"  Done in {time.time()-t:.1f}s\n")

        # --- Step 4: Build and save FAISS index ---
        print("Step 4/4: Building and saving FAISS index...")
        t = time.time()
        store.build(chunks, vectors)
        print(f"  Done in {time.time()-t:.1f}s\n")

        # Clean up cloned temp dir if it was a GitHub URL
        if repo_url.startswith("http"):
            cleanup_repo(repo_root)

        total_time = time.time() - total_start
        print(f"\n✅ Indexing complete in {total_time:.1f}s")
        print(f"   {store.chunk_count} chunks indexed and ready to search.\n")

        return store

    # ------------------------------------------------------------------
    # Step 2: QUERY
    # ------------------------------------------------------------------

    def query(
        self,
        question: str,
        index_name: str,
        top_k: int = 5,
        show_sources: bool = True,
    ) -> str:
        """
        Answer a question about an indexed repo.

        Args:
            question:   natural language question about the codebase
            index_name: name of the index to search (must be indexed first)
            top_k:      number of chunks to retrieve and send to LLM
            show_sources: if True, print the retrieved source chunks before the answer

        Returns:
            str: the LLM's answer with file references

        Example:
            answer = pipe.query("how does authentication work?", "fastapi")
        """
        # Load the index
        store = VectorStore(name=index_name, index_dir=self.index_dir)
        if not store.exists():
            raise FileNotFoundError(
                f"No index named '{index_name}' found in {self.index_dir}/\n"
                f"Run pipe.index(..., name='{index_name}') first."
            )
        store.load()

        # Embed the question
        query_vec = self.embedder.embed_one(question)

        # Retrieve top-k most relevant chunks
        results = store.search(query_vec, top_k=top_k)

        if show_sources:
            print(f"\n📂 Retrieved {len(results)} relevant chunks:")
            for r in results:
                print(f"   {r['score']:.3f}  {r['rel_path']}:{r['start_line']}  [{r['type']}] {r['name']}")
            print()

        # Generate answer with LLM
        answer = self.generator.answer(question=question, chunks=results)
        return answer


# ---------------------------------------------------------------------------
# Quick test — run directly:
# python pipeline.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    pipe = CodeSagePipeline()

    # Use a small repo for fast testing
    # You can change this to any public GitHub repo
    REPO_URL  = "https://github.com/tiangolo/fastapi"
    INDEX_NAME = "fastapi"

    # --- Index the repo (skips if already done) ---
    pipe.index(repo_url=REPO_URL, name=INDEX_NAME)

    # --- Ask questions ---
    questions = [
        "How does request routing work?",
        "How does FastAPI handle dependency injection?",
        "Where are HTTP exceptions defined and raised?",
    ]

    print(f"\n{'='*50}")
    print("  QUERY MODE")
    print(f"{'='*50}")

    for question in questions:
        print(f"\n❓ Question: {question}\n")
        answer = pipe.query(
            question=question,
            index_name=INDEX_NAME,
            top_k=5,
            show_sources=True,
        )
        print(f"💬 Answer:\n{answer}")
        print("\n" + "-"*50)