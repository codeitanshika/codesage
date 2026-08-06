"""
tests/test_llm.py

Manual smoke test for generation/llm.py — sends a fake question + fake
retrieved chunks to the real Groq API and prints the answer. Not a
pytest suite (no assertions, hits the network, needs GROQ_API_KEY); run
it directly to sanity-check LLM generation.

Run:
    python tests/test_llm.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generation.llm import LLMGenerator

if __name__ == "__main__":
    # Simulate what retrieval would return
    fake_chunks = [
        {
            "score": 0.821,
            "content": (
                "def login(username: str, password: str) -> User:\n"
                "    user = db.get_user(username)\n"
                "    if not user:\n"
                "        raise HTTPException(status_code=404, detail='User not found')\n"
                "    if not verify_password(password, user.hashed_password):\n"
                "        raise HTTPException(status_code=401, detail='Wrong password')\n"
                "    token = create_access_token(user.id)\n"
                "    return {'access_token': token, 'user': user}"
            ),
            "rel_path": "app/auth/login.py",
            "type": "function",
            "name": "login",
            "start_line": 10,
            "end_line": 18,
        },
        {
            "score": 0.743,
            "content": (
                "def verify_password(plain: str, hashed: str) -> bool:\n"
                "    return bcrypt.checkpw(plain.encode(), hashed.encode())"
            ),
            "rel_path": "app/auth/utils.py",
            "type": "function",
            "name": "verify_password",
            "start_line": 5,
            "end_line": 7,
        },
        {
            "score": 0.698,
            "content": (
                "def create_access_token(user_id: int) -> str:\n"
                "    payload = {'sub': user_id, 'exp': datetime.utcnow() + timedelta(hours=24)}\n"
                "    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')"
            ),
            "rel_path": "app/auth/tokens.py",
            "type": "function",
            "name": "create_access_token",
            "start_line": 12,
            "end_line": 15,
        },
    ]

    print("=== LLM Generation Test ===\n")
    print("Sending question + code chunks to Groq...\n")

    gen = LLMGenerator()
    answer = gen.answer(
        question="How does user authentication work? Walk me through the login flow.",
        chunks=fake_chunks,
    )

    print("Answer:")
    print("-" * 60)
    print(answer)
    print("-" * 60)
