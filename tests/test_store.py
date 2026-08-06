"""
tests/test_store.py

Manual smoke test for embedding/store.py — builds a FAISS index from a
handful of fake code chunks, saves it, reloads it from disk, and runs a
few searches to confirm the right chunk comes back for each query. Not a
pytest suite (no assertions, just printed output); run it directly to
sanity-check the vector store.

Run:
    python tests/test_store.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from embedding.embedder import Embedder, embed_chunks
from embedding.store import VectorStore

if __name__ == "__main__":
    print("=== VectorStore Test ===\n")

    # Fake chunks simulating what parser.py would produce
    fake_chunks = [
        {
            "content": "def login(username: str, password: str) -> User:\n    user = db.get_user(username)\n    if not verify_password(password, user.hashed_password):\n        raise HTTPException(401)\n    return user",
            "rel_path": "app/auth/login.py",
            "file_path": "app/auth/login.py",
            "type": "function",
            "name": "login",
            "start_line": 10,
            "end_line": 15,
        },
        {
            "content": "def hash_password(password: str) -> str:\n    salt = bcrypt.gensalt()\n    return bcrypt.hashpw(password.encode(), salt).decode()",
            "rel_path": "app/auth/utils.py",
            "file_path": "app/auth/utils.py",
            "type": "function",
            "name": "hash_password",
            "start_line": 5,
            "end_line": 8,
        },
        {
            "content": "def calculate_total(items: list[Item]) -> float:\n    return sum(item.price * item.quantity for item in items)",
            "rel_path": "app/cart/pricing.py",
            "file_path": "app/cart/pricing.py",
            "type": "function",
            "name": "calculate_total",
            "start_line": 3,
            "end_line": 5,
        },
        {
            "content": "class UserService:\n    def get_user(self, user_id: int) -> User:\n        return self.db.query(User).filter(User.id == user_id).first()\n\n    def create_user(self, data: UserCreate) -> User:\n        user = User(**data.dict())\n        self.db.add(user)\n        self.db.commit()\n        return user",
            "rel_path": "app/services/user_service.py",
            "file_path": "app/services/user_service.py",
            "type": "class",
            "name": "UserService",
            "start_line": 8,
            "end_line": 18,
        },
        {
            "content": "def send_email(to: str, subject: str, body: str) -> bool:\n    msg = MIMEText(body)\n    msg['Subject'] = subject\n    msg['To'] = to\n    smtp.send_message(msg)\n    return True",
            "rel_path": "app/utils/email.py",
            "file_path": "app/utils/email.py",
            "type": "function",
            "name": "send_email",
            "start_line": 12,
            "end_line": 18,
        },
    ]

    # Step 1: Embed the chunks
    embedder = Embedder()
    chunks, vectors = embed_chunks(fake_chunks, embedder)

    # Step 2: Build and save the index
    store = VectorStore("test_index")
    store.build(chunks, vectors)

    # Step 3: Load it back from disk (simulates restarting the app)
    print("\nLoading index back from disk...")
    store2 = VectorStore("test_index")
    store2.load()

    # Step 4: Search with different queries
    queries = [
        "how does user login and authentication work",
        "how are passwords hashed and stored securely",
        "how is the shopping cart total calculated",
    ]

    print("\n=== Search Results ===")
    for query in queries:
        print(f"\nQuery: '{query}'")
        query_vec = embedder.embed_one(query)
        results = store2.search(query_vec, top_k=2)
        for r in results:
            print(f"  {r['score']:.3f}  {r['rel_path']}:{r['start_line']}  [{r['type']}] {r['name']}")
