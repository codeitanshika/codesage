"""
ingestion/parser.py

Responsibility: Given a file path, extract meaningful chunks from it.
For code files — extract individual functions and classes using tree-sitter.
For markdown files — extract sections by heading.

Each chunk is a dict:
{
    "content":   str,   # the actual code/text
    "file_path": str,   # absolute path to the source file
    "rel_path":  str,   # path relative to repo root (shown in answers)
    "type":      str,   # "function", "class", "method", "section", "file"
    "name":      str,   # function/class name, or heading text
    "start_line": int,  # line number where this chunk starts (1-indexed)
    "end_line":   int,  # line number where this chunk ends
}

Usage:
    from ingestion.parser import parse_file
    chunks = parse_file("/tmp/codesage_abc/fastapi/main.py", repo_root="/tmp/codesage_abc")
"""

import os
import re
from pathlib import Path


# ---------------------------------------------------------------------------
# tree-sitter setup
# Tree-sitter parses source code into an AST (Abstract Syntax Tree).
# We use it to find function/class boundaries instead of guessing by line count.
# ---------------------------------------------------------------------------

# We import lazily inside functions so the file is still importable even if
# tree-sitter isn't installed yet (useful during early development/testing).

def _get_parser(language_name: str):
    """
    Returns a tree-sitter parser configured for the given language.
    Returns None if tree-sitter or the language binding isn't installed.
    """
    try:
        import tree_sitter_python
        import tree_sitter_javascript
        import tree_sitter_go
        import tree_sitter_java
        import tree_sitter_rust
        import tree_sitter_cpp
        from tree_sitter import Language, Parser

        language_map = {
            "python":     tree_sitter_python.language(),
            "javascript": tree_sitter_javascript.language(),
            "typescript": tree_sitter_javascript.language(),  # close enough for chunking
            "jsx":        tree_sitter_javascript.language(),
            "tsx":        tree_sitter_javascript.language(),
            "go":         tree_sitter_go.language(),
            "java":       tree_sitter_java.language(),
            "rust":       tree_sitter_rust.language(),
            "cpp":        tree_sitter_cpp.language(),
        }

        if language_name not in language_map:
            return None

        lang = Language(language_map[language_name])
        parser = Parser(lang)
        return parser

    except Exception:
        return None


# Map file extensions to language names
EXTENSION_TO_LANGUAGE = {
    ".py":  "python",
    ".js":  "javascript",
    ".ts":  "typescript",
    ".jsx": "jsx",
    ".tsx": "tsx",
    ".go":  "go",
    ".java": "java",
    ".rs":  "rust",
    ".cpp": "cpp",
}

# Node types in the AST that we treat as top-level chunks
# These are the tree-sitter node type names for each language
CHUNK_NODE_TYPES = {
    "python": {
        "function_definition",   # def my_function():
        "decorated_definition",  # @decorator + def/class
        "class_definition",      # class MyClass:
    },
    "javascript": {
        "function_declaration",      # function foo() {}
        "class_declaration",         # class Foo {}
        "method_definition",         # methods inside a class
        "arrow_function",            # const foo = () => {}  (captured via parent)
        "export_statement",          # export default function...
        "lexical_declaration",       # const foo = ...
    },
    "typescript": {
        "function_declaration",
        "class_declaration",
        "method_definition",
        "export_statement",
        "lexical_declaration",
        "interface_declaration",     # TypeScript specific
        "type_alias_declaration",    # TypeScript: type Foo = ...
    },
}
CHUNK_NODE_TYPES["jsx"] = CHUNK_NODE_TYPES["javascript"]
CHUNK_NODE_TYPES["tsx"] = CHUNK_NODE_TYPES["typescript"]

CHUNK_NODE_TYPES["go"] = {
    "function_declaration",   # func Foo() {}
    "method_declaration",     # func (r Receiver) Foo() {}
    "type_declaration",       # type Foo struct{...} / type Foo interface{...}
}
CHUNK_NODE_TYPES["java"] = {
    "class_declaration",
    "interface_declaration",
    "enum_declaration",
    "record_declaration",
}
CHUNK_NODE_TYPES["rust"] = {
    "function_item",   # not nested inside impl_item's own chunk (see below),
                        # so methods inside `impl` blocks get their own chunks too
    "struct_item",
    "trait_item",
    "enum_item",
}
CHUNK_NODE_TYPES["cpp"] = {
    "function_definition",   # free functions; methods defined inline inside a
                              # class are swallowed into that class's chunk,
                              # same as Python/Java
    "class_specifier",
    "struct_specifier",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_file(file_path: str, repo_root: str) -> list[dict]:
    """
    Parse a single file and return a list of chunks.
    Dispatches to the right parser based on file extension.
    """
    path = Path(file_path)
    ext = path.suffix.lower()
    rel_path = os.path.relpath(file_path, repo_root)

    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []

    if not content.strip():
        return []

    if ext == ".md":
        return _parse_markdown(content, file_path, rel_path)

    language = EXTENSION_TO_LANGUAGE.get(ext)
    if language:
        chunks = _parse_with_treesitter(content, file_path, rel_path, language)
        if chunks:
            return chunks
        # Fallback: if tree-sitter fails or isn't installed, chunk by lines
        return _parse_by_lines(content, file_path, rel_path)

    # Unknown extension — return the whole file as one chunk
    return _whole_file_chunk(content, file_path, rel_path)


def parse_repo(file_paths: list[str], repo_root: str) -> list[dict]:
    """
    Parse all files in the repo. Returns all chunks across all files.

    Args:
        file_paths: list of absolute file paths (from clone.load_repo)
        repo_root:  repo root directory (for computing relative paths)
    """
    all_chunks = []
    for i, file_path in enumerate(file_paths):
        chunks = parse_file(file_path, repo_root)
        all_chunks.extend(chunks)

        # Progress indicator every 50 files
        if (i + 1) % 50 == 0:
            print(f"  Parsed {i + 1}/{len(file_paths)} files — {len(all_chunks)} chunks so far")

    print(f"  Done. {len(file_paths)} files → {len(all_chunks)} total chunks")
    return all_chunks


# ---------------------------------------------------------------------------
# tree-sitter parser
# ---------------------------------------------------------------------------

def _parse_with_treesitter(
    content: str,
    file_path: str,
    rel_path: str,
    language: str,
) -> list[dict]:
    """
    Use tree-sitter to extract functions and classes from the file.
    Returns an empty list if tree-sitter isn't available.
    """
    parser = _get_parser(language)
    if parser is None:
        return []

    tree = parser.parse(content.encode("utf-8"))
    root_node = tree.root_node

    target_types = CHUNK_NODE_TYPES.get(language, set())
    lines = content.splitlines()
    chunks = []

    # Different grammars use different node types for names: plain
    # "identifier" (Python/JS/Go functions/Rust functions), "type_identifier"
    # (Rust/C++ struct/class names, Go type names), or "field_identifier"
    # (Go method names).
    NAME_NODE_TYPES = {"identifier", "type_identifier", "field_identifier"}

    def extract_name(node) -> str:
        """
        Pull the name out of a function/class/type node. Checks direct
        children first, then one level deeper — covers cases where the
        name is nested (Go's `type_declaration` -> `type_spec` ->
        `type_identifier`, C++'s `function_definition` ->
        `function_declarator` -> `identifier`, a Python `@decorator`-
        wrapped def/class, or a JS `const foo = () => {}`).
        """
        for child in node.children:
            if child.type in NAME_NODE_TYPES:
                return child.text.decode("utf-8")
        for child in node.children:
            if child.type == "decorator":
                continue  # e.g. @staticmethod — never the name of the thing it decorates
            for grandchild in child.children:
                if grandchild.type in NAME_NODE_TYPES:
                    return grandchild.text.decode("utf-8")
        return "unknown"

    def visit(node, depth=0):
        """
        Recursively walk the AST. When we hit a chunk-worthy node,
        extract it and don't recurse deeper into it (its contents are
        already included in the chunk text).
        """
        if node.type in target_types:
            start_line = node.start_point[0]  # 0-indexed
            end_line   = node.end_point[0]    # 0-indexed

            chunk_lines = lines[start_line:end_line + 1]
            chunk_text  = "\n".join(chunk_lines)

            # Skip tiny chunks (e.g. empty functions, stubs)
            if len(chunk_text.strip()) < 20:
                return

            name = extract_name(node)
            node_type = (
                node.type
                .replace("_definition", "")
                .replace("_declaration", "")
                .replace("_specifier", "")
                .replace("_item", "")
            )

            chunks.append({
                "content":    chunk_text,
                "file_path":  file_path,
                "rel_path":   rel_path,
                "type":       node_type,
                "name":       name,
                "start_line": start_line + 1,  # convert to 1-indexed for display
                "end_line":   end_line + 1,
            })
            # Don't recurse into this node's children — the chunk already
            # contains all of them as text
            return

        for child in node.children:
            visit(child, depth + 1)

    visit(root_node)

    # If tree-sitter found nothing (e.g. a file with only imports/constants),
    # fall back to treating the whole file as one chunk
    if not chunks:
        return _whole_file_chunk(content, file_path, rel_path)

    return chunks


# ---------------------------------------------------------------------------
# Markdown parser — split by headings
# ---------------------------------------------------------------------------

def _parse_markdown(content: str, file_path: str, rel_path: str) -> list[dict]:
    """
    Split a markdown file into sections at each heading (# ## ###).
    Each section becomes one chunk.
    """
    lines = content.splitlines()
    chunks = []
    current_heading = "Introduction"
    current_lines = []
    start_line = 1

    heading_pattern = re.compile(r"^#{1,3}\s+(.+)")

    for i, line in enumerate(lines, start=1):
        match = heading_pattern.match(line)
        if match:
            # Save previous section
            if current_lines:
                text = "\n".join(current_lines).strip()
                if len(text) > 30:
                    chunks.append({
                        "content":    text,
                        "file_path":  file_path,
                        "rel_path":   rel_path,
                        "type":       "section",
                        "name":       current_heading,
                        "start_line": start_line,
                        "end_line":   i - 1,
                    })
            current_heading = match.group(1).strip()
            current_lines = [line]
            start_line = i
        else:
            current_lines.append(line)

    # Don't forget the last section
    if current_lines:
        text = "\n".join(current_lines).strip()
        if len(text) > 30:
            chunks.append({
                "content":    text,
                "file_path":  file_path,
                "rel_path":   rel_path,
                "type":       "section",
                "name":       current_heading,
                "start_line": start_line,
                "end_line":   len(lines),
            })

    return chunks if chunks else _whole_file_chunk(content, file_path, rel_path)


# ---------------------------------------------------------------------------
# Fallback parsers
# ---------------------------------------------------------------------------

def _parse_by_lines(content: str, file_path: str, rel_path: str, chunk_size: int = 60) -> list[dict]:
    """
    Dumb fallback: split file into chunks of N lines.
    Used when tree-sitter isn't installed or doesn't support the language.
    """
    lines = content.splitlines()
    chunks = []

    for i in range(0, len(lines), chunk_size):
        chunk_lines = lines[i:i + chunk_size]
        text = "\n".join(chunk_lines).strip()
        if len(text) < 20:
            continue
        chunks.append({
            "content":    text,
            "file_path":  file_path,
            "rel_path":   rel_path,
            "type":       "lines",
            "name":       f"lines {i+1}-{i+len(chunk_lines)}",
            "start_line": i + 1,
            "end_line":   i + len(chunk_lines),
        })

    return chunks


def _whole_file_chunk(content: str, file_path: str, rel_path: str) -> list[dict]:
    """Last resort: the whole file is one chunk."""
    lines = content.splitlines()
    return [{
        "content":    content.strip(),
        "file_path":  file_path,
        "rel_path":   rel_path,
        "type":       "file",
        "name":       Path(file_path).name,
        "start_line": 1,
        "end_line":   len(lines),
    }]


# ---------------------------------------------------------------------------
# Manual smoke test moved to tests/test_parser.py — run: python tests/test_parser.py
# ---------------------------------------------------------------------------