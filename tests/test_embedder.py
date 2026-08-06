"""
tests/test_embedder.py

Manual smoke test for embedding/embedder.py — embeds a few sentences
locally with sentence-transformers and checks that similarity scores
make sense (auth-related sentences score high against each other,
unrelated ones score low). Not a pytest suite (no assertions, just
printed output); run it directly to sanity-check embeddings.

Run:
    python tests/test_embedder.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from embedding.embedder import Embedder, embed_chunks

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
