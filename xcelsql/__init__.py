"""XcelSQL package for SQL-powered Excel transformations."""
from __future__ import annotations
from importlib import metadata
import pathlib
import re

PACKAGE_NAME = "xcelsql"

def _read_pyproject_version() -> str | None:
    # Attempt to read version from pyproject.toml (editable dev mode)
    try:
        root = pathlib.Path(__file__).resolve().parent.parent
        pyproject = root / "pyproject.toml"
        if not pyproject.exists():
            return None
        text = pyproject.read_text(encoding="utf-8", errors="ignore")
        # Simple regex: version = "x.y.z"
        m = re.search(r'^version\s*=\s*"([^"]+)"', text, flags=re.MULTILINE)
        if m:
            return m.group(1)
    except Exception:
        return None
    return None

try:
    __version__ = metadata.version(PACKAGE_NAME)
except metadata.PackageNotFoundError:
    __version__ = _read_pyproject_version() or "0.0.0.dev0"

__all__ = ["__version__"]