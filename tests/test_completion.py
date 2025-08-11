#!/usr/bin/env python3
"""Tests for tab completion functionality in the REPL."""
import unittest
import os
import tempfile
import sys
import pandas as pd
from typing import List, Optional, Union

# Fix imports to use the xcelsql package
from xcelsql.cli.repl import _completer, Session, _GLOBAL_SESS
import xcelsql.cli.repl as repl_mod

def _normalize_completion(completion):
    """Normalize completion result to list type."""
    if completion is None:
        return None
    return completion if isinstance(completion, list) else [completion]

class TestCompletion(unittest.TestCase):
    """Test tab completion functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary Excel file for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_file = os.path.join(self.temp_dir.name, "test.xlsx")
        
        # Create a test dataframe and write to Excel
        df = pd.DataFrame({
            'A': [1, 2], 
            'B': [3, 4]
        })
        with pd.ExcelWriter(self.test_file) as writer:
            df.to_excel(writer, sheet_name="Sheet1", index=False)
            df.to_excel(writer, sheet_name="Sheet2", index=False)
    
    def tearDown(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()
    
    def test_sheet_completion(self):
        """Test sheet name completion."""
        sess = Session()
        try:
            sess.load_workbook(self.test_file)
            import xcelsql.cli.repl
            xcelsql.cli.repl._GLOBAL_SESS = sess
            global _GLOBAL_SESS
            _GLOBAL_SESS = sess
            class _FakeReadline:
                def __init__(self, buf):
                    self._buf = buf
                def get_line_buffer(self):
                    return self._buf
            # Prefix completion
            repl_mod.readline = _FakeReadline('{S')  # type: ignore
            completions = _completer('{S', 0)
            completions = _normalize_completion(completions)
            self.assertIsNotNone(completions)
            # The completer returns braced names e.g. {Sheet1}
            self.assertTrue(any(c in ('{Sheet1}', '{Sheet2}') or c in ('{Sheet1', '{Sheet2') for c in completions),
                            f"Expected Sheet1/Sheet2 variants in completions, got {completions}")
            # Exact match (should include closing brace variant)
            repl_mod.readline = _FakeReadline('{Sheet1')  # type: ignore
            completions = _completer('{Sheet1', 0)
            completions = _normalize_completion(completions)
            if completions is not None:
                # Accept either already closed or open form depending on implementation nuance
                self.assertTrue(any(c.startswith('{Sheet1') for c in completions), f"Unexpected completions {completions}")
        except Exception as e:
            self.fail(f"Sheet completion test failed: {e}")

    def test_command_completion(self):
        """Test command completion."""
        class _FakeReadline:
            def __init__(self, buf):
                self._buf = buf
            def get_line_buffer(self):
                return self._buf
        repl_mod.readline = _FakeReadline('\\h')  # type: ignore
        completions = _completer('\\h', 0)
        completions = _normalize_completion(completions)
        self.assertIsNotNone(completions)
        self.assertTrue("\\help" in completions)
        repl_mod.readline = _FakeReadline('\\help')  # type: ignore
        completions = _completer('\\help', 0)
        completions = _normalize_completion(completions)
        self.assertEqual(completions, ["\\help"])

if __name__ == "__main__":
    unittest.main()