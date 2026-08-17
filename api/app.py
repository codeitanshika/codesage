"""
api/app.py

FastAPI app setup — CORS, middleware, route registration.
Entry point: uvicorn api.app:app --reload --port 8000
"""

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

# CORS — this is what allows your React frontend (running on localhost:5173)
# to talk to this backend (running on localhost:8000).
# Without this, the browser blocks cross-origin requests.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # in production you'd lock this to your frontend URL
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
