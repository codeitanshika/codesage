"""
ingestion/clone.py

Responsibility: Given a GitHub URL or a local path, return a list of
all code file paths worth indexing.

Usage:
    from ingestion.clone import load_repo
    files = load_repo("https://github.com/some-user/some-repo")
    # files -> ["/tmp/codesage_abc123/src/main.py", ...]
"""

import os
import subprocess
import tempfile
import shutil
from pathlib import Path


# ---------------------------------------------------------------------------
# File types we care about. Add more as needed.
# ---------------------------------------------------------------------------
SUPPORTED_EXTENSIONS = {
    ".py",   # Python
    ".js",   # JavaScript
    ".ts",   # TypeScript
    ".jsx",  # React
    ".tsx",  # React + TypeScript
    ".java", # Java
    ".go",   # Go
    ".rs",   # Rust
    ".cpp",  # C++
    ".c",    # C
    ".cs",   # C#
    ".rb",   # Ruby
    ".php",  # PHP
    ".swift",# Swift
    ".kt",   # Kotlin
    ".md",   # Markdown (README, docs — useful context)
}

# Folders that are never worth indexing
SKIP_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".env",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "coverage",
    ".pytest_cache",
    ".mypy_cache",
}

# Max file size to index (bytes). Files larger than this are skipped.
# Avoids accidentally embedding huge auto-generated files.
MAX_FILE_SIZE_BYTES = 100_000  # 100 KB


def load_repo(source: str) -> tuple[list[str], str]:
    """
    Main entry point. Accepts a GitHub URL or a local directory path.

    Returns:
        (file_paths, repo_root)
        - file_paths: list of absolute paths to indexable code files
        - repo_root:  the root directory of the repo on disk
                      (useful later for showing relative paths in answers)

    Examples:
        files, root = load_repo("https://github.com/tiangolo/fastapi")
        files, root = load_repo("/home/samar/my-project")
    """
    if source.startswith("http://") or source.startswith("https://"):
        repo_root = _clone_from_github(source)
        cloned = True
    else:
        repo_root = os.path.abspath(source)
        cloned = False
        if not os.path.isdir(repo_root):
            raise ValueError(f"Local path does not exist: {repo_root}")

    file_paths = _discover_files(repo_root)

    print(f"  Source  : {source}")
    print(f"  Root    : {repo_root}")
    print(f"  Cloned  : {cloned}")
    print(f"  Files   : {len(file_paths)} indexable files found")

    return file_paths, repo_root


def _clone_from_github(url: str) -> str:
    """
    Clones a GitHub repo into a temporary directory and returns that path.

    We use a temp directory so we don't litter the user's filesystem.
    The caller is responsible for cleanup if they want it (see cleanup_repo).
    """
    # Create a temp directory that won't be auto-deleted (we need it to persist
    # until indexing is done). We name it so it's recognisable in /tmp.
    tmp_dir = tempfile.mkdtemp(prefix="codesage_")

    print(f"Cloning {url} ...")
    result = subprocess.run(
        ["git", "clone", "--depth=1", url, tmp_dir],
        capture_output=True,
        text=True,
    )
    # --depth=1 means we only fetch the latest commit, not the full history.
    # This is much faster for large repos.

    if result.returncode != 0:
        # Clean up the empty temp dir before raising
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise RuntimeError(
            f"git clone failed for {url}.\n"
            f"stderr: {result.stderr.strip()}"
        )

    return tmp_dir


def _discover_files(repo_root: str) -> list[str]:
    """
    Walks the repo directory tree and returns paths of all indexable files.

    Skips:
    - Directories in SKIP_DIRS
    - Files whose extension is not in SUPPORTED_EXTENSIONS
    - Files larger than MAX_FILE_SIZE_BYTES
    - Files that can't be read as UTF-8 (binary files, etc.)
    """
    indexable = []
    root_path = Path(repo_root)

    for dirpath, dirnames, filenames in os.walk(repo_root):
        # os.walk lets us prune directories in-place by modifying dirnames.
        # This is the correct way to skip entire subtrees efficiently.
        dirnames[:] = [
            d for d in dirnames
            if d not in SKIP_DIRS and not d.startswith(".")
        ]

        for filename in filenames:
            file_path = Path(dirpath) / filename

            # Check extension
            if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue

            # Check file size
            try:
                size = file_path.stat().st_size
            except OSError:
                continue
            if size > MAX_FILE_SIZE_BYTES:
                continue
            if size == 0:
                continue

            # Quick UTF-8 check — we don't want to embed binary garbage
            if not _is_utf8(file_path):
                continue

            indexable.append(str(file_path))

    # Sort so the order is deterministic (helpful for debugging)
    indexable.sort()
    return indexable


def _is_utf8(file_path: Path) -> bool:
    """
    Returns True if the file can be decoded as UTF-8, False otherwise.
    Reads only the first 512 bytes for speed.
    """
    try:
        with open(file_path, "rb") as f:
            f.read(512).decode("utf-8")
        return True
    except (UnicodeDecodeError, OSError):
        return False


def cleanup_repo(repo_root: str) -> None:
    """
    Deletes a cloned repo from disk. Call this after indexing is done
    if the source was a GitHub URL (you don't need the files anymore once
    the FAISS index is built).
    """
    if "codesage_" in repo_root:  # Safety check: only delete our own temp dirs
        shutil.rmtree(repo_root, ignore_errors=True)
        print(f"Cleaned up temp dir: {repo_root}")
    else:
        print(f"Skipping cleanup — {repo_root} doesn't look like a temp dir.")


# ---------------------------------------------------------------------------
# Quick manual test — run this file directly to try it out:
# python ingestion/clone.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    # Default to a small, fast-to-clone repo for testing
    test_url = sys.argv[1] if len(sys.argv) > 1 else "https://github.com/tiangolo/fastapi"

    files, root = load_repo(test_url)

    print(f"\nFirst 10 files:")
    for f in files[:10]:
        # Show path relative to repo root so it's readable
        rel = os.path.relpath(f, root)
        print(f"  {rel}")

    print(f"\n...and {max(0, len(files) - 10)} more.")