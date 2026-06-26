# CodeSage 🔍

> Ask questions about any codebase in plain English — powered by RAG (Retrieval-Augmented Generation)

---

## What is this?

CodeSage lets you point at any GitHub repository and have a conversation with it.

Instead of reading through hundreds of files to understand an unfamiliar codebase, you ask:

- *"Where is authentication handled?"*
- *"How does the payment flow work?"*
- *"What does the `UserService` class do?"*
- *"Which files should I edit to add a new API route?"*

CodeSage indexes the repo, understands the code semantically, and gives you grounded, file-referenced answers.

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
Embed each chunk → vector (sentence-transformers)
    │
    ▼
Store in vector DB (FAISS)
    │
    ▼
User asks a question
    │
    ├── Embed the question
    ├── Find top-k most similar chunks
    └── Send [question + chunks] to LLM → answer with file references
```

The key insight: code is chunked **semantically** (by function/class boundary), not by arbitrary word count. This means each retrieved chunk is a complete, meaningful unit — not half a function.

---

## Tech stack

| Layer | Tool | Why |
|-------|------|-----|
| Language | Python 3.10+ | |
| LLM | Groq API (Llama 3.3 70B) | Free tier, fast inference |
| Embeddings | `sentence-transformers` (all-MiniLM-L6-v2) | Free, runs fully locally |
| Vector search | FAISS | Fast, no external service needed |
| Code parsing | `tree-sitter` | Understands function/class boundaries |
| CLI | `argparse` | Simple interface |
| (Optional) Frontend | Streamlit | Quick web UI |

> **No paid APIs required.** Groq offers a free tier with generous limits. Embeddings and vector search run entirely on your machine.

---

## Project structure

```
codesage/
├── README.md
├── requirements.txt
│
├── ingestion/
│   ├── __init__.py
│   ├── clone.py          # Clone any GitHub repo, discover all code files
│   └── parser.py         # tree-sitter: extract functions/classes per file
│
├── embedding/
│   ├── embedder.py       # sentence-transformers wrapper
│   └── store.py          # FAISS index: build, save, load
│
├── retrieval/
│   └── retriever.py      # Query → top-k chunks with file + line references
│
├── generation/
│   └── llm.py            # Groq API call with retrieved context
│
├── pipeline.py           # Wires ingestion → embedding → retrieval → generation
└── main.py               # CLI entrypoint
```

---

## Quickstart

```bash
# 1. Clone this repo
git clone https://github.com/YOUR_USERNAME/codesage.git
cd codesage

# 2. Install dependencies
pip install -r requirements.txt

# 3. Get a free Groq API key at https://console.groq.com
#    No credit card required.

# 4. Set your Groq API key
export GROQ_API_KEY=your_key_here       # Mac/Linux
$env:GROQ_API_KEY="your_key_here"      # Windows PowerShell

# 5. Index a repo and ask a question
python main.py --repo https://github.com/some-user/some-repo --ask "How does auth work?"
```

---

## Roadmap

- [x] Project structure and README
- [x] Repo cloning and file traversal (`ingestion/clone.py`)
- [x] tree-sitter code parsing — function/class chunking (`ingestion/parser.py`)
- [ ] Embedding pipeline with sentence-transformers (`embedding/embedder.py`)
- [ ] FAISS vector store — build and persist (`embedding/store.py`)
- [ ] Retrieval with file + line number references (`retrieval/retriever.py`)
- [ ] LLM generation with Groq API (`generation/llm.py`)
- [ ] Full pipeline wiring (`pipeline.py`)
- [ ] CLI interface (`main.py`)
- [ ] Streamlit web UI
- [ ] Support for multi-repo indexing
- [ ] Incremental re-indexing (only re-embed changed files)

---

## Why this is different from "chat with your PDF"

Most RAG demos chunk text by word count and embed paragraphs. That works for prose, but breaks for code — you end up retrieving half a function or a random block mid-loop.

CodeSage uses `tree-sitter` to parse the AST and chunk by actual code units (functions, classes, methods). Every retrieved chunk is a complete, runnable piece of code with its file path and line numbers attached.

---

## Learning goals

This project was built to understand RAG from the ground up:

1. How LLMs and LLM APIs work (tokens, context windows, prompt structure)
2. What embeddings are and why they capture semantic meaning
3. How vector search works (cosine similarity, FAISS indexes)
4. How to chunk documents intelligently for retrieval quality
5. How to wire all of the above into a production-style pipeline

---

## Contributing

This is a learning project — PRs, issues, and suggestions welcome.

---

## License

MIT