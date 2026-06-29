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
