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

from generation.prompts import CHAT_SYSTEM_PROMPT


# Model to use — Groq deprecated llama-3.3-70b-versatile; gpt-oss-120b is
# the largest model currently available on the free tier.
GROQ_MODEL = "openai/gpt-oss-120b"

# How many tokens the LLM can generate in its answer.
# gpt-oss-120b is a reasoning model — its hidden reasoning tokens count
# against this budget, so it needs headroom beyond just the visible answer.
MAX_TOKENS = 2000


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

    def _build_messages(self, question: str, chunks: list[dict], history: list[dict] = None) -> list[dict]:
        """
        Build the message list shared by answer() and answer_stream().

        We format each chunk as a labeled block with file path + line numbers,
        then ask the LLM to answer using only those blocks. This is called
        "grounding" — the LLM is anchored to real code, not its training
        data, so it can't hallucinate file names.
        """
        context = self._format_chunks(chunks)

        messages = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}]

        if history:
            for turn in history:
                messages.append({
                    "role": turn["role"],
                    "content": turn["content"]
                })

        messages.append({
            "role": "user",
            "content": f"""Here are the relevant code chunks from the repository:

{context}

Question: {question}

Please answer based on the code chunks above, referencing specific files and line numbers."""
        })

        return messages

    def answer(self, question: str, chunks: list[dict], history: list[dict] = None, top_k: int = 5) -> str:
        """
        Generate an answer to a question using retrieved code chunks.

        Args:
            question: the user's question about the codebase
            chunks:   list of result dicts from VectorStore.search()
                      each has: score, content, rel_path, name, start_line, end_line
            top_k:    max number of chunks to include in the prompt

        Returns:
            str: the LLM's answer, with file references
        """
        top_chunks = chunks[:top_k]

        if not top_chunks:
            return "No relevant code found in the indexed repository for that question."

        messages = self._build_messages(question, top_chunks, history)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=MAX_TOKENS,
            temperature=0.1,
            reasoning_effort="medium",
        )

        return response.choices[0].message.content

    def answer_stream(self, question: str, chunks: list[dict], history: list[dict] = None, top_k: int = 5):
        """
        Same as answer(), but yields the answer token-by-token as it's
        generated instead of returning the full string at once.

        gpt-oss-120b is a reasoning model — Groq streams its hidden
        reasoning as a separate `delta.reasoning` field before the visible
        answer arrives in `delta.content`. Only content deltas are yielded;
        reasoning is never shown to the user.
        """
        top_chunks = chunks[:top_k]

        if not top_chunks:
            yield "No relevant code found in the indexed repository for that question."
            return

        messages = self._build_messages(question, top_chunks, history)

        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=MAX_TOKENS,
            temperature=0.1,
            reasoning_effort="medium",
            stream=True,
        )

        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content

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
# Manual smoke test moved to tests/test_llm.py — run: python tests/test_llm.py
# ---------------------------------------------------------------------------