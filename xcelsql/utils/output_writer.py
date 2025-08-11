"""Utilities for writing output in various formats."""
from __future__ import annotations
import sys
import pandas as pd
import logging
from typing import Optional, TextIO, Dict, Any

logger = logging.getLogger(__name__)

def write_output(df: pd.DataFrame, path: Optional[str], format_name: str, **kwargs: Any) -> None:
    """Write dataframe to file or stdout in specified format."""
    if format_name == 'table':
        _print_table(df, sys.stdout, **kwargs)
    elif format_name == 'csv':
        if path:
            df.to_csv(path, index=False, **kwargs)
        else:
            df.to_csv(sys.stdout, index=False, **kwargs)
    elif format_name == 'excel':
        if not path:
            raise ValueError("Excel output requires a file path")
        df.to_excel(path, index=False, **kwargs)
    elif format_name == 'json':
        orient = kwargs.pop('orient', 'records')
        if path:
            df.to_json(path, orient=orient, indent=2, **kwargs)
        else:
            print(df.to_json(orient=orient, indent=2, **kwargs))
    elif format_name == 'jsonl':
        orient = kwargs.pop('orient', 'records')
        if path:
            df.to_json(path, orient=orient, lines=True, **kwargs)
        else:
            print(df.to_json(orient=orient, lines=True, **kwargs))
    else:
        raise ValueError(f"Unsupported output format: {format_name}")


def _print_table(df: pd.DataFrame, out: TextIO, max_rows: Optional[int] = None, 
                 max_cols: Optional[int] = None, max_colwidth: int = 50) -> None:
    """Pretty-print dataframe as an ASCII table."""
    with pd.option_context(
        'display.max_rows', max_rows or 100,
        'display.max_columns', max_cols or 20,
        'display.max_colwidth', max_colwidth,
        'display.width', None
    ):
        print(df.to_string(index=False), file=out)