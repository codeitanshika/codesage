"""
tests/test_clone.py

Manual smoke test for ingestion/clone.py — clones a real repo from GitHub
and lists the indexable files found. Not a pytest suite (no assertions,
hits the network); run it directly to sanity-check cloning + discovery.

Run:
    python tests/test_clone.py [repo_url]
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ingestion.clone import load_repo

if __name__ == "__main__":
    # Default to a small, fast-to-clone repo for testing
    test_url = sys.argv[1] if len(sys.argv) > 1 else "https://github.com/tiangolo/fastapi"

    files, root = load_repo(test_url)

    print(f"\nFirst 10 files:")
    for f in files[:10]:
        # Show path relative to repo root so it's readable
        rel = os.path.relpath(f, root)
        print(f"  {rel}")

    print(f"\n...and {max(0, len(files) - 10)} more.")
