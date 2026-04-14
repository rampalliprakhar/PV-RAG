import sys
from ingest import ingest
from search import search
from rag import ask

def main():
    """
    Command-line interface for the PV-RAG pipeline.
    Usage:
        python main.py ingest <folder>  # Index all documents in a folder (e.g. data/)
        python main.py search <query>   # Search for relevant chunks
        python main.py ask <question>   # Ask a question over the indexed PV literature
    """
    if len(sys.argv) < 2:
        print("Usage: python main.py [ingest <folder> | search <query> | ask <question>]")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "ingest":
        if len(sys.argv) < 3:
            print("Usage: python main.py ingest <folder>")
            sys.exit(1)
        ingest(sys.argv[2])

    elif cmd == "search":
        if len(sys.argv) < 3:
            print("Usage: python main.py search <query>")
            sys.exit(1)
        results = search(" ".join(sys.argv[2:]))
        for r in results[:5]:
            print("\n---")
            print(r["path"])
            print(r["content"][:300])

    elif cmd == "ask":
        if len(sys.argv) < 3:
            print("Usage: python main.py ask <question>")
            sys.exit(1)
        print(ask(" ".join(sys.argv[2:])))

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)

if __name__ == "__main__":
    main()