# CodeSage 🔍

> Ask questions about any codebase in plain English — powered by RAG (Retrieval-Augmented Generation)

---

## What is this?

CodeSage lets you point at any GitHub repository and have a conversation with it.

Instead of reading through hundreds of files to understand an unfamiliar codebase, you ask:

- *"How does backpropagation work?"*
- *"Where are HTTP exceptions raised?"*
- *"What does the `Value` class do?"*
- *"Which files should I edit to add a new API route?"*

CodeSage indexes the repo, understands the code semantically, and gives you grounded answers with exact file and line references.

---

## How it works (RAG pipeline)

```
GitHub Repo
    │
    ▼
Clone & parse files (.py, .js, .ts, .java, etc.)
    │
    ▼
Chunk by function / class (not just word count)
    │
    ▼
Embed each chunk → vector (sentence-transformers, runs locally)
    │
    ▼
Store in vector DB (FAISS, saved to disk)
    │
    ▼
User asks a question
    │
    ├── Embed the question
    ├── Find top-k most similar chunks (cosine similarity)
    └── Send [question + chunks] to LLM → answer with file references
```

The key insight: code is chunked **semantically** (by function/class boundary), not by arbitrary word count. This means each retrieved chunk is a complete, meaningful unit — not half a function.

---

## Tech stack

| Layer | Tool | Cost |
|-------|------|------|
| Language | Python 3.10+ | Free |
| LLM | Groq API (Llama 3.3 70B) | Free tier, no card needed |
| Embeddings | `sentence-transformers` (all-MiniLM-L6-v2) | Free, runs fully locally |
| Vector search | FAISS | Free, no external service |
| Code parsing | `tree-sitter` | Free, runs locally |

> **No paid APIs required.** Get a free Groq key at [console.groq.com](https://console.groq.com) — no credit card.

---

## Project structure

```
codesage/
├── README.md
├── requirements.txt
├── .gitignore
├── main.py               # CLI entrypoint (index / ask / chat)
├── pipeline.py           # Wires all modules together
│
├── ingestion/
│   ├── __init__.py
│   ├── clone.py          # Clone any GitHub repo, discover all code files
│   └── parser.py         # tree-sitter: extract functions/classes per file
│
├── embedding/
│   ├── __init__.py
│   ├── embedder.py       # sentence-transformers: text → vectors
│   └── store.py          # FAISS index: build, save, load, search
│
└── generation/
    ├── __init__.py
    └── llm.py            # Groq API: question + chunks → answer
```

---

## Quickstart

```bash
# 1. Clone this repo
git clone https://github.com/YOUR_USERNAME/codesage.git
cd codesage

# 2. Install dependencies
pip install -r requirements.txt

# 3. Get a free Groq API key at https://console.groq.com (no credit card)

# 4. Set your key
export GROQ_API_KEY=your_key_here        # Mac/Linux
$env:GROQ_API_KEY="your_key_here"       # Windows PowerShell

# 5. Index a repo
python main.py index --repo https://github.com/karpathy/micrograd

# 6. Ask a question
python main.py ask --index micrograd --question "how does backpropagation work?"

# 7. Or start an interactive chat
python main.py chat --index micrograd
```

---

## CLI reference

```
# Index a repo (run once per repo)
python main.py index --repo <github_url>
python main.py index --repo <github_url> --name my-index
python main.py index --repo <github_url> --force        # re-index even if exists
python main.py index --repo <github_url> --ask "question"  # index then ask

# Ask a single question
python main.py ask --index <name> --question "your question"
python main.py ask --index <name> -q "your question" --no-sources

# Interactive chat (ask multiple questions)
python main.py chat --index <name>
```

---

## Example output

```
❓ Question: How does backpropagation work?

📂 Retrieved 5 relevant chunks:
   0.821  micrograd/engine.py:85   [function] backward
   0.743  micrograd/engine.py:32   [function] _backward
   0.698  README.md:45             [section] Training a neural net

💬 Answer:
Backpropagation in micrograd is implemented through the `backward` method
in `micrograd/engine.py:85`. It performs a topological sort of the computation
graph, then calls each node's `_backward` function in reverse order...
```

---

## Roadmap

- [x] Project structure and README
- [x] Repo cloning and file traversal (`ingestion/clone.py`)
- [x] tree-sitter code parsing — function/class chunking (`ingestion/parser.py`)
- [x] Embedding pipeline with sentence-transformers (`embedding/embedder.py`)
- [x] FAISS vector store — build and persist (`embedding/store.py`)
- [x] LLM generation with Groq API (`generation/llm.py`)
- [x] Full pipeline wiring (`pipeline.py`)
- [x] CLI interface — index / ask / chat (`main.py`)
- [ ] Streamlit web UI
- [ ] Support for multi-repo indexing
- [ ] Incremental re-indexing (only re-embed changed files)

---

## Why this is different from "chat with your PDF"

Most RAG demos chunk text by word count and embed paragraphs. That works for prose, but breaks for code — you end up retrieving half a function or a random block mid-loop.

CodeSage uses `tree-sitter` to parse the AST and chunk by actual code units (functions, classes, methods). Every retrieved chunk is a complete, runnable piece of code with its file path and line numbers attached.

---

## What I learned building this

1. **LLMs and LLM APIs** — tokens, context windows, prompt structure, grounding
2. **Embeddings** — how text becomes vectors, why similar meaning = similar numbers
3. **Vector search** — cosine similarity, FAISS indexes, nearest neighbour search
4. **Code parsing** — ASTs, tree-sitter, chunking by semantic unit vs word count
5. **RAG pipeline** — how retrieval + generation work together end to end

---

## Contributing

This is a learning project — PRs, issues, and suggestions welcome.

---

## License

MIT