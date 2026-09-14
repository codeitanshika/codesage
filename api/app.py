"""
api/app.py

FastAPI app setup — CORS, middleware, route registration.
Entry point: uvicorn api.app:app --reload --port 8000
"""

import os

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import index, query, review, onboard, contribute

app = FastAPI(
    title="CodeSage API",
    description="Ask questions about any codebase using RAG",
    version="1.0.0",
)

# CORS — this is what allows the React frontend to talk to this backend.
# Without this, the browser blocks cross-origin requests.
# ALLOWED_ORIGINS is a comma-separated list (e.g. your Vercel URL) —
# defaults to "*" so local dev (localhost:5173 -> localhost:8000) works
# with zero config. Set it explicitly once deployed.
allowed_origins = os.environ.get("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(index.router)
app.include_router(query.router)
app.include_router(review.router)
app.include_router(onboard.router)
app.include_router(contribute.router)


# ---------------------------------------------------------------------------
# Run directly:
# python -m api.app
# or preferably:
# uvicorn api.app:app --reload --port 8000
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.app:app", host="0.0.0.0", port=8000, reload=True)
