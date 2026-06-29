"""
main.py
 
The CLI entrypoint for CodeSage.
 
Usage:
    # Index a repo
    python main.py index --repo https://github.com/karpathy/micrograd
 
    # Ask a question
    python main.py ask --index micrograd --question "how does backpropagation work?"
 
    # Index and ask in one shot
    python main.py index --repo https://github.com/karpathy/micrograd --ask "how does the Value class work?"
 
    # Interactive chat mode (ask multiple questions)
    python main.py chat --index micrograd
"""
import argparse
import sys
from pipeline import CodeSagePipeline
 
 
def cmd_index(args, pipe: CodeSagePipeline):
    """Handle the 'index' command."""
    store = pipe.index(
        repo_url=args.repo,
        name=args.name,
        force=args.force,
    )
 
    # If --ask was also passed, answer it immediately after indexing
    if args.ask:
        print(f"\n❓ {args.ask}\n")
        answer = pipe.query(
            question=args.ask,
            index_name=args.name or _name_from_url(args.repo),
            top_k=args.top_k,
            show_sources=args.sources,
        )
        print(f"💬 Answer:\n{answer}\n")
 
 
def cmd_ask(args, pipe: CodeSagePipeline):
    """Handle the 'ask' command — single question."""
    print(f"\n❓ {args.question}\n")
    answer = pipe.query(
        question=args.question,
        index_name=args.index,
        top_k=args.top_k,
        show_sources=args.sources,
    )
    print(f"💬 Answer:\n{answer}\n")
 
 
def cmd_chat(args, pipe: CodeSagePipeline):
    """
    Handle the 'chat' command — interactive loop.
    Type questions one by one. Type 'exit' or 'quit' to stop.
    """
    print(f"\n🔍 CodeSage — chatting with index: '{args.index}'")
    print("   Type your question and press Enter.")
    print("   Type 'exit' to quit.\n")
    print("-" * 50)
 
    while True:
        try:
            question = input("\n❓ You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nGoodbye!")
            break
 
        if not question:
            continue
 
        if question.lower() in ("exit", "quit", "q", "bye"):
            print("Goodbye!")
            break
 
        answer = pipe.query(
            question=question,
            index_name=args.index,
            top_k=args.top_k,
            show_sources=args.sources,
        )
        print(f"\n💬 CodeSage:\n{answer}")
        print("\n" + "-" * 50)
 
 
def _name_from_url(url: str) -> str:
    """Derive an index name from a GitHub URL."""
    return url.rstrip("/").split("/")[-1].replace(".git", "")
 
 
def main():
    parser = argparse.ArgumentParser(
        prog="codesage",
        description="CodeSage — Ask questions about any codebase using RAG",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py index --repo https://github.com/karpathy/micrograd
  python main.py ask   --index micrograd --question "how does backprop work?"
  python main.py chat  --index micrograd
  python main.py index --repo https://github.com/karpathy/micrograd --ask "explain the Value class"
        """,
    )
 
    subparsers = parser.add_subparsers(dest="command", required=True)
 
    # ----------------------------------------------------------------
    # Shared arguments (used by multiple subcommands)
    # ----------------------------------------------------------------
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument(
        "--top-k", type=int, default=5,
        help="Number of chunks to retrieve (default: 5)"
    )
    shared.add_argument(
        "--sources", action="store_true", default=True,
        help="Show retrieved source chunks (default: True)"
    )
    shared.add_argument(
        "--no-sources", dest="sources", action="store_false",
        help="Hide retrieved source chunks"
    )
 
    # ----------------------------------------------------------------
    # 'index' subcommand
    # ----------------------------------------------------------------
    p_index = subparsers.add_parser(
        "index",
        parents=[shared],
        help="Index a GitHub repo or local path",
    )
    p_index.add_argument(
        "--repo", required=True,
        help="GitHub URL or local path to the repo"
    )
    p_index.add_argument(
        "--name",
        help="Name for the index (default: repo name from URL)"
    )
    p_index.add_argument(
        "--force", action="store_true",
        help="Force re-indexing even if index already exists"
    )
    p_index.add_argument(
        "--ask",
        help="Ask a question immediately after indexing"
    )
 
    # ----------------------------------------------------------------
    # 'ask' subcommand
    # ----------------------------------------------------------------
    p_ask = subparsers.add_parser(
        "ask",
        parents=[shared],
        help="Ask a single question about an indexed repo",
    )
    p_ask.add_argument(
        "--index", required=True,
        help="Name of the index to query"
    )
    p_ask.add_argument(
        "--question", "-q", required=True,
        help="Your question about the codebase"
    )
 
    # ----------------------------------------------------------------
    # 'chat' subcommand
    # ----------------------------------------------------------------
    p_chat = subparsers.add_parser(
        "chat",
        parents=[shared],
        help="Start an interactive chat session with an indexed repo",
    )
    p_chat.add_argument(
        "--index", required=True,
        help="Name of the index to chat with"
    )
 
    # ----------------------------------------------------------------
    # Parse and dispatch
    # ----------------------------------------------------------------
    args = parser.parse_args()
 
    # Fix --name default for index command
    if args.command == "index" and not args.name:
        args.name = _name_from_url(args.repo)
 
    pipe = CodeSagePipeline()
 
    if args.command == "index":
        cmd_index(args, pipe)
    elif args.command == "ask":
        cmd_ask(args, pipe)
    elif args.command == "chat":
        cmd_chat(args, pipe)
    else:
        parser.print_help()
        sys.exit(1)
 
 
if __name__ == "__main__":
    main()
 