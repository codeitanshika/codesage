"""
tests/test_pipeline.py

Manual smoke test for the full pipeline — indexes a small real repo
(skips if already indexed) and asks it a few questions end to end.
Not a pytest suite (no assertions, hits the network and the real Groq
API); run it directly to sanity-check the whole RAG flow.

Run:
    python tests/test_pipeline.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline import CodeSagePipeline

if __name__ == "__main__":
    pipe = CodeSagePipeline()

    # Use a small repo for fast testing
    # You can change this to any public GitHub repo
    REPO_URL   = "https://github.com/karpathy/micrograd"
    INDEX_NAME = "micrograd"

    # --- Index the repo (skips if already done) ---
    pipe.index(repo_url=REPO_URL, name=INDEX_NAME)

    # --- Ask questions ---
    questions = [
        "How does backpropagation work?",
        "How is a neuron implemented?",
        "How does the Value class compute gradients?",
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
