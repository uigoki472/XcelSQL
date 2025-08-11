"""Output writing utilities (core implementation)."""
from __future__ import annotations
import logging
from pathlib import Path
from typing import Optional
import pandas as pd

logger = logging.getLogger(__name__)


def _print_table(df: pd.DataFrame, max_rows: int = 100, max_cols: int = 20, max_colwidth: int = 50) -> None:
    with pd.option_context(
        'display.max_rows', max_rows,
        'display.max_columns', max_cols,
        'display.max_colwidth', max_colwidth,
        'display.width', None
    ):
        print(df.to_string(index=False))


def write_output(df: pd.DataFrame, output_path: Optional[str], output_format: Optional[str]) -> None:
    """Write dataframe to the desired destination.

    Supported formats: table, csv, excel(xlsx), json, jsonl, parquet.
    If output_path is None and format != table -> write to stdout where sensible.
    """
    if df is None:
        logger.warning("write_output called with df=None")
        return
    if not isinstance(df, pd.DataFrame):  # defensive
        raise TypeError("write_output expects a pandas DataFrame")
    fmt = (output_format or "csv").lower()

    # Default: if no path and not table, we still allow stdout for csv/json/jsonl
    path: Optional[Path] = Path(output_path) if output_path else None
    if path:
        path.parent.mkdir(parents=True, exist_ok=True)

    if fmt == 'table':
        _print_table(df)
        return
    if fmt == 'csv':
        if path:
            df.to_csv(path, index=False)
        else:
            print(df.to_csv(index=False))
    elif fmt in ('xlsx', 'xls', 'excel'):  # treat synonyms as Excel
        if not path:
            raise ValueError("Excel output requires an output path")
        try:
            df.to_excel(path, index=False)
        except ImportError:  # pragma: no cover
            raise RuntimeError("openpyxl required for Excel output. Install with: pip install openpyxl")
    elif fmt == 'parquet':
        if not path:
            raise ValueError("Parquet output requires an output path")
        try:
            df.to_parquet(path, index=False)
        except ImportError:  # pragma: no cover
            raise RuntimeError("pyarrow or fastparquet required for parquet output. Install with: pip install pyarrow")
    elif fmt == 'json':
        if path:
            df.to_json(path, orient='records', indent=2)
        else:
            print(df.to_json(orient='records', indent=2))
    elif fmt == 'jsonl':
        if path:
            df.to_json(path, orient='records', lines=True)
        else:
            print(df.to_json(orient='records', lines=True))
    else:
        raise ValueError(f"Unsupported output format: {fmt}")
    if path:
        logger.info("Wrote %d rows to %s (%s)", len(df), path, fmt)
