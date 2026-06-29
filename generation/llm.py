"""
generation/llm.py

Responsibility: Take a user question + retrieved code chunks and send
them to the Groq API (Llama 3.3 70B) to generate a grounded answer.

This is the final step of the RAG pipeline:
    question + relevant chunks → LLM → answer with file references

Usage:
    from generation.llm import LLMGenerator
    gen = LLMGenerator()
    answer = gen.answer(question="how does auth work?", chunks=results)
    print(answer)
"""

import os
from groq import Groq


# Model to use — Llama 3.3 70B is Groq's best free model
# Fast, smart, great at reading and explaining code
GROQ_MODEL = "llama-3.3-70b-versatile"

# How many tokens the LLM can generate in its answer
# 1024 is plenty for a detailed code explanation
MAX_TOKENS = 1024

# System prompt — tells the LLM its role and how to behave
SYSTEM_PROMPT = """You are CodeSage, an expert code assistant that answers questions about software repositories.

You are given:
1. A question about a codebase
2. Relevant code chunks retrieved from that codebase (with file paths and line numbers)

Your job:
- Answer the question using ONLY the provided code chunks as your source
- Always reference the specific file and line numbers where you found the answer
- If the chunks don't contain enough information, say so honestly
- Keep answers clear and developer-friendly
- Format file references like this: `path/to/file.py:line_number`

Do not make up code or file paths that aren't in the provided chunks."""


class LLMGenerator:
    """
    Wraps the Groq API to generate answers from retrieved code chunks.
    """

    def __init__(self, model: str = GROQ_MODEL):
        self.model = model
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY environment variable not set.\n"
                "Get a free key at https://console.groq.com\n"
                "Then run: $env:GROQ_API_KEY='your_key_here'"
            )
        self.client = Groq(api_key=api_key)

    def answer(self, question: str, chunks: list[dict], top_k: int = 5) -> str:
        """
        Generate an answer to a question using retrieved code chunks.

        Args:
            question: the user's question about the codebase
            chunks:   list of result dicts from VectorStore.search()
                      each has: score, content, rel_path, name, start_line, end_line
            top_k:    max number of chunks to include in the prompt

        Returns:
            str: the LLM's answer, with file references

        How the prompt is built:
            We format each chunk as a labeled block with file path + line numbers,
            then ask the LLM to answer using only those blocks.
            This is called "grounding" — the LLM is anchored to real code,
            not its training data, so it can't hallucinate file names.
        """
        # Take only the top chunks (already sorted by score from store.search)
        top_chunks = chunks[:top_k]

        if not top_chunks:
            return "No relevant code found in the indexed repository for that question."

        # Build the context block — this is what gets injected into the prompt
        context = self._format_chunks(top_chunks)

        # Build the full user message
        user_message = f"""Here are the relevant code chunks from the repository:

{context}

Question: {question}

Please answer based on the code chunks above, referencing specific files and line numbers."""

        # Call the Groq API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_message},
            ],
            max_tokens=MAX_TOKENS,
            temperature=0.1,  # low temperature = focused, deterministic answers
                              # (we want facts, not creativity)
        )

        return response.choices[0].message.content

    def _format_chunks(self, chunks: list[dict]) -> str:
        """
        Format retrieved chunks into a readable context block for the prompt.

        Each chunk becomes:
            [Chunk 1] app/auth/login.py (lines 10-15) — function: login
            ```
            def login(username, password):
                ...
            ```
        """
        parts = []
        for i, chunk in enumerate(chunks, start=1):
            header = (
                f"[Chunk {i}] {chunk['rel_path']} "
                f"(lines {chunk['start_line']}-{chunk['end_line']}) "
                f"— {chunk['type']}: {chunk['name']}"
            )
            parts.append(f"{header}\n```\n{chunk['content']}\n```")

        return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Quick test — run directly:
# python -m generation.llm
# ---------------------------------------------------------------------------
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