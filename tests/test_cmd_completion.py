#!/usr/bin/env python3
"""Tests for command completion functionality in REPL."""
import unittest
import os
import tempfile
import sys
import pandas as pd
from typing import List, Optional, Union

# Fix imports to use the xcelsql package
from xcelsql.cli.repl import _completer, COMMANDS
from xcelsql.cli import repl as repl_mod

def _normalize_completion(completion):
    """Normalize completion result to list type."""
    if completion is None:
        return None
    return completion if isinstance(completion, list) else [completion]

def _call_completer(line: str, state: int):
    """Invoke completer with a fake readline line buffer."""
    class _FakeReadline:
        def __init__(self, buf):
            self._buf = buf
        def get_line_buffer(self):
            return self._buf
    repl_mod.readline = _FakeReadline(line)  # type: ignore
    return _completer(line, state)

class TestCommandCompletion(unittest.TestCase):
    """Test command completion functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Initialize global session for completion
        from xcelsql.cli.repl import Session, _GLOBAL_SESS
        if _GLOBAL_SESS is None:
            global_sess = Session()
            import xcelsql.cli.repl
            xcelsql.cli.repl._GLOBAL_SESS = global_sess
    
    def test_basic_completion(self):
        """Test basic command completion."""
        completions = _call_completer("\\", 0)
        completions = _normalize_completion(completions)
        self.assertIsNotNone(completions)
        self.assertTrue(len(completions) > 0)
        
        completions = _call_completer("\\h", 0)
        completions = _normalize_completion(completions)
        self.assertIsNotNone(completions)
        self.assertIn("\\help", completions)
        
        completions = _call_completer("\\help", 0)
        completions = _normalize_completion(completions)
        self.assertEqual(completions, ["\\help"])
        # Expect SQL keyword completion for plain SELECT token
        kw = _call_completer("SELECT", 0)
        kw_norm = _normalize_completion(kw)
        self.assertIsNotNone(kw_norm)
        self.assertIn("SELECT", kw_norm)

    def test_preserves_backslash(self):
        """Test that the backslash is preserved in completions."""
        for i in range(len(COMMANDS)):
            completion = _call_completer("\\", i)
            if completion is not None:
                if isinstance(completion, list):
                    for item in completion:
                        self.assertTrue(item.startswith("\\"), f"Completion {item} should start with backslash")
                else:
                    self.assertTrue(completion.startswith("\\"), f"Completion {completion} should start with backslash")
        completion = _call_completer("\\h", 0)
        if isinstance(completion, list):
            for item in completion:
                self.assertTrue(item.startswith("\\"), f"Completion {item} should start with backslash")
        else:
            self.assertTrue(completion.startswith("\\"), f"Completion {completion} should start with backslash")

if __name__ == "__main__":
    unittest.main()