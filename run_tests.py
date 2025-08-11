#!/usr/bin/env python3
"""
Run all tests for the xcelsql package.

This script discovers and runs all tests in the project using pytest.
"""
import sys
import subprocess
import os
import argparse

def ensure_pandas():
    """Ensure pandas is importable; try install once; on failure show diagnostics."""
    try:
        import pandas  # noqa: F401
        return
    except ImportError:
        print("[ensure_pandas] pandas not importable; attempting installation...")
        print(f"Python executable: {sys.executable}")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pandas'], check=False)
        try:
            import pandas  # noqa: F401
            print("[ensure_pandas] pandas installed successfully.")
            return
        except ImportError:
            print("[ensure_pandas] FAILED to import pandas after install attempt.")
            print("sys.path: \n" + "\n".join(sys.path))
            print("Environment PIP_PREFIX:", os.environ.get('PIP_PREFIX'))
            print("Suggest: activate correct venv or run: python -m pip install pandas")
            raise

# Attempt to ensure pandas is available (tests import it directly)
try:
    import pandas  # noqa: F401
except ImportError:
    print("pandas not found. Attempting to install pandas for tests...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pandas'], check=False)
    except Exception as _e:  # noqa: F841
        print("Automatic installation of pandas failed. Please install manually: pip install pandas")

def run_tests(verbose=False, coverage=False, specific_test=None):
    """Run all tests using pytest."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

    ensure_pandas()

    print("Verifying imports...")
    try:
        if os.path.exists(os.path.join(current_dir, "test_imports.py")):
            import runpy
            runpy.run_path(os.path.join(current_dir, "test_imports.py"), run_name="__main__")
    except Exception as e:
        print(f"Import verification failed: {e}")
        print("Continuing with tests anyway...")

    import pytest
    args = []
    if verbose:
        args.append('-v')
    if coverage:
        args.extend(['--cov=xcelsql', '--cov-report=term', '--cov-report=html'])
    if specific_test:
        args.append(specific_test)
    print("Running tests with pytest args:", ' '.join(args) if args else '(none)')
    return pytest.main(args)

def main():
    """Parse arguments and run tests."""
    parser = argparse.ArgumentParser(description="Run xcelsql package tests")
    parser.add_argument("-v", "--verbose", action="store_true", help="Increase verbosity")
    parser.add_argument("--coverage", action="store_true", help="Generate test coverage report")
    parser.add_argument("test", nargs="?", help="Specific test file or directory to run")
    parser.add_argument("--only-imports", action="store_true", help="Only run import verification test")
    args = parser.parse_args()

    if args.only_imports:
        import runpy
        runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_imports.py"), run_name="__main__")
        return 0

    return run_tests(verbose=args.verbose, coverage=args.coverage, specific_test=args.test)

if __name__ == "__main__":
    sys.exit(main())