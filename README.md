# CodeSage ⚡

> Ask questions about any codebase in plain English — powered by RAG (Retrieval-Augmented Generation)

---

## What is this?

CodeSage is an AI-powered developer tool that lets you have a conversation with any GitHub repository.

Instead of reading through hundreds of files to understand an unfamiliar codebase, you ask:

- *"How does the diagnosis agent work?"*
- *"Where is authentication handled?"*
- *"What does the `UserService` class do?"*
- *"Which files should I edit to add a new API route?"*

CodeSage indexes the repo, understands the code semantically, and gives you grounded answers with exact file and line references — backed by the actual source code.

---

## How it works (RAG pipeline)

```
GitHub Repo
    │
    ▼
Clone & parse files (.py, .js, .ts, .java, etc.)
    │
    ▼
Chunk by function / class using tree-sitter (AST-based, not word count)
    │
    ▼
Embed each chunk → vector (sentence-transformers, runs locally)
    │
    ▼
Store in vector DB (FAISS, persisted to disk)
    │
    ▼
User asks a question
    │
    ├── Embed the question
    ├── Find top-k most similar chunks (cosine similarity)
    └── Send [question + chunks] to LLM → answer with file references
```

---

## Tech stack

| Layer | Tool | Cost |
|-------|------|------|
| Language | Python 3.10+ | Free |
| LLM | Groq API (Llama 3.3 70B) | Free tier, no card needed |
| Embeddings | `sentence-transformers` (all-MiniLM-L6-v2) | Free, runs fully locally |
| Vector search | FAISS | Free, no external service |
| Code parsing | `tree-sitter` | Free, runs locally |
| Backend | FastAPI + uvicorn | Free |
| Frontend | React + Tailwind CSS | Free |
| Deployment | Render (backend) + Vercel (frontend) | Free tier |

> **No paid APIs required.** Get a free Groq key at [console.groq.com](https://console.groq.com) — no credit card.

---

## Features

### Core RAG Pipeline
Built from scratch — no LangChain, no frameworks. Every component written and understood from the ground up.

- **AST-based code chunking** — tree-sitter parses code into functions and classes. Each retrieved chunk is a complete, runnable unit — not half a function.
- **Local embeddings** — sentence-transformers runs entirely on your machine. No API calls, no cost, no internet required after first download.
- **FAISS vector search** — indexes and searches thousands of code chunks in milliseconds using cosine similarity.
- **Groq LLM integration** — Llama 3.3 70B generates grounded answers using only retrieved code as context. Never hallucinates file names.

### Chat Interface
- **Index any GitHub repo from the UI** — paste a URL, click Index. Indexes in the background, polls for completion, activates automatically.
- **Code-first answers** — answers lead with actual code snippets and file references (`filename.py:line`), not paragraphs of explanation.
- **Expandable source cards** — every answer shows retrieved chunks with file path, line numbers, match score, and actual code.
- **Persistent chat history** — follow-up questions work. The LLM has the last 3 conversation turns as context.

### Advanced Features
- **Multi-repo search** — toggle "search all repos" to search across every indexed codebase simultaneously. Results merged and ranked by relevance score.
- **Incremental re-indexing** — MD5 hashes track which files changed. Only re-embeds changed files on re-index.
- **Code review** — four focus areas: General, Security, Performance, Error Handling. Returns structured issues with file references, current code, and suggested fixes.
- **Export review as Markdown** — download any code review as a `.md` file.

---

## Project structure

```
codesage/
├── README.md
├── requirements.txt
├── .gitignore
├── .env                        # GROQ_API_KEY (never committed)
│
├── main.py                     # CLI entrypoint (index / ask / chat)
├── pipeline.py                 # Wires all modules together
│
├── api/                        # FastAPI backend (HTTP endpoints)
│   ├── __init__.py
│   ├── app.py                  # FastAPI setup, CORS, route registration
│   ├── deps.py                 # Shared pipeline instance + indexing job tracking
│   ├── models.py                # All Pydantic request/response models
│   └── routes/
│       ├── __init__.py
│       ├── index.py            # /index, /status, /indexes, /repo-info
│       ├── query.py            # /ask, /ask-multi
│       ├── review.py           # /review
│       └── onboard.py          # /onboard
│
├── ingestion/
│   ├── __init__.py
│   ├── clone.py                # Clone any GitHub repo, discover code files
│   └── parser.py               # tree-sitter: extract functions/classes
│
├── embedding/
│   ├── __init__.py
│   ├── embedder.py             # sentence-transformers: text → vectors
│   └── store.py                # FAISS index: build, save, load, search
│
├── generation/
│   ├── __init__.py
│   ├── llm.py                  # Groq API: question + chunks → answer
│   └── prompts.py              # All LLM prompts (chat, review, onboard)
│
├── indexes/                    # FAISS indexes saved here (gitignored)
│   ├── my-repo.faiss
│   ├── my-repo.chunks.json
│   └── my-repo.hashes.json     # MD5 hashes for incremental re-indexing
│
└── frontend/                   # React + Tailwind frontend
    ├── src/
    │   ├── App.jsx             # Main app (chat UI, sidebar, source cards)
    │   ├── main.jsx
    │   └── index.css
    ├── index.html
    └── vite.config.js
```

---

## Quickstart

```bash
# 1. Clone this repo
git clone https://github.com/codeitanshika/codesage.git
cd codesage

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Get a free Groq API key at https://console.groq.com

# 4. Create .env file
echo GROQ_API_KEY=your_key_here > .env

# 5. Start the backend
uvicorn api.app:app --reload --port 8000

# 6. In a new terminal, start the frontend
cd frontend
npm install
npm run dev

# 7. Open http://localhost:5173
```

Or use the CLI:
```bash
python main.py index --repo https://github.com/karpathy/micrograd
python main.py ask --index micrograd --question "how does backpropagation work?"
python main.py chat --index micrograd
```

---

## API endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/indexes` | List all indexed repos |
| GET | `/status/{name}` | Check indexing status |
| POST | `/index` | Index a GitHub repo (background) |
| POST | `/ask` | Ask a question |
| POST | `/ask-multi` | Search across multiple indexes |
| POST | `/review` | Run a code review |

---

## Roadmap

### Completed ✅
- [x] AST-based code chunking with tree-sitter
- [x] Local embeddings with sentence-transformers
- [x] FAISS vector store (build, save, load, search)
- [x] Groq LLM integration (Llama 3.3 70B)
- [x] CLI interface (index / ask / chat)
- [x] FastAPI backend with REST endpoints
- [x] React + Tailwind frontend
- [x] Index any GitHub repo from the UI
- [x] Code-first answer style
- [x] Expandable source cards with file references
- [x] Persistent chat history (follow-up questions)
- [x] Multi-repo search
- [x] Incremental re-indexing with MD5 hashing
- [x] Code review (Security / Performance / General / Error Handling)
- [x] Export review as Markdown

### In Progress 🔨
- [ ] **Step 1** — Store repo URL at index time
- [ ] **Step 2** — GitHub link generation (file refs → clickable GitHub links)
- [ ] **Step 3** — Onboarding report endpoint (what it does, how to run, key files, architecture)
- [ ] **Step 4** — Onboarding UI (auto-appears on new repo index, suggested questions)
- [ ] **Step 5** — Structured review JSON (severity, category, what/why/fix per issue)
- [ ] **Step 6** — Tabbed review panel (Security / Performance / Code Quality / Setup tabs)
- [ ] **Step 7** — Contribution opportunities endpoint (find good first issues)
- [ ] **Step 8** — Contribution cards UI (draft PR title + description, effort estimate)
- [ ] **Step 9** — "Ask about this" button on every card
- [ ] **Step 10** — Deploy to Render + Vercel (live URL)

---

## Why this is different from "chat with your PDF"

Most RAG demos chunk text by word count and embed paragraphs. That works for prose but breaks for code — you end up retrieving half a function or a random block mid-loop.

CodeSage uses tree-sitter to parse the AST and chunk by actual code units (functions, classes, methods). Every retrieved chunk is a complete, runnable piece of code with its file path and line numbers attached. The LLM is grounded in real code — it cannot invent file names or make up APIs that don't exist.

---

## What I learned building this

1. **LLMs and LLM APIs** — tokens, context windows, prompt engineering, grounding
2. **Embeddings** — how text becomes vectors, why similar meaning = similar numbers
3. **Vector search** — cosine similarity, FAISS indexes, nearest neighbour search
4. **AST parsing** — tree-sitter, abstract syntax trees, chunking by semantic unit vs word count
5. **RAG pipeline** — how retrieval + generation work together end to end
6. **FastAPI** — async endpoints, Pydantic models, background tasks, CORS
7. **React + Tailwind** — component architecture, useState, useEffect, axios

---

## Contributing

This is a learning project — PRs, issues, and suggestions welcome.

---

## License

MIT