"""
tests/test_parser.py

Manual smoke test for ingestion/parser.py — clones a real repo, parses a
sample of its Python files with tree-sitter, and prints the resulting
chunks. Not a pytest suite (no assertions, hits the network); run it
directly to sanity-check chunking.

Run:
    python tests/test_parser.py [repo_url]
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ingestion.clone import load_repo
from ingestion.parser import parse_file

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://github.com/tiangolo/fastapi"

    print(f"Loading repo: {url}")
    file_paths, repo_root = load_repo(url)

    # Only parse the first 20 files so the test is fast
    sample = [f for f in file_paths if f.endswith(".py")][:20]
    print(f"\nParsing {len(sample)} Python files...\n")

    all_chunks = []
    for fp in sample:
        chunks = parse_file(fp, repo_root)
        all_chunks.extend(chunks)
        rel = os.path.relpath(fp, repo_root)
        print(f"  {rel} → {len(chunks)} chunks")

    print(f"\nTotal chunks: {len(all_chunks)}")
    print(f"\nSample chunk:")
    if all_chunks:
        c = all_chunks[0]
        print(f"  file  : {c['rel_path']}")
        print(f"  type  : {c['type']}")
        print(f"  name  : {c['name']}")
        print(f"  lines : {c['start_line']} - {c['end_line']}")
        print(f"  preview: {c['content'][:200]}...")
