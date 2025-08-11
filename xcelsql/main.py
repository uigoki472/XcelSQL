"""Main entry point for xcelsql CLI."""
# Allow direct execution via `python xcelsql/main.py` by ensuring package root on sys.path
if __name__ == "__main__" and __package__ is None:  # running as script, not module
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from xcelsql.cli.main import main

if __name__ == "__main__":
    main()