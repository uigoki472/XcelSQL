"""Excel sheet input/output operations."""
from __future__ import annotations
import re
import pandas as pd
from typing import Dict, List, Tuple, Optional
from xcelsql.utils.excel_utils import SheetTableMapper

AUTO_HEADER_SENTINELS = {"auto","infer","infer_header"}


def parse_sheet_info(sheet_spec: str) -> Tuple[str, int]:
    """Parse sheet specification into sheet name and header row.
    
    Format: SheetName[:HeaderRowNum|auto]
    header_row=0 indicates auto-inference should be applied.
    """
    parts = sheet_spec.split(':', 1)
    sheet_name = parts[0]
    if len(parts) == 1:
        return sheet_name, 1
    raw = parts[1].strip().lower()
    if raw in AUTO_HEADER_SENTINELS or raw == '0':
        return sheet_name, 0
    try:
        return sheet_name, int(raw)
    except ValueError:
        raise ValueError(f"Invalid header row spec in '{sheet_spec}'. Use integer or 'auto'.")


def infer_header_row(xls: pd.ExcelFile, sheet_name: str, max_scan: int = 10) -> int:
    """Infer header row (1-based) by scanning up to max_scan rows.
    Heuristic: choose row with max score where score = count of non-null string-like unique cells.
    Fallback: 1.
    """
    try:
        sample = xls.parse(sheet_name, header=None, nrows=max_scan)
    except Exception:
        return 1
    best_row = 0
    best_score = -1
    for idx in range(len(sample)):
        row = sample.iloc[idx]
        # Treat a cell as a header candidate if it is a non-empty string and not purely numeric
        cleaned = [str(c).strip() for c in row if pd.notna(c)]
        tokens = [c for c in cleaned if c and not re.fullmatch(r"\d+(\.\d+)?", c)]
        # Penalize duplicates
        unique_tokens = set(tokens)
        score = len(unique_tokens)
        if score > best_score:
            best_score = score
            best_row = idx
    return best_row + 1  # 1-based


def load_excel_sheets(
    excel_file: pd.ExcelFile,
    sheet_specs: List[str],
    default_header_row: int = 1,
    mapper: Optional[SheetTableMapper] = None
) -> Dict[str, pd.DataFrame]:
    """Load multiple Excel sheets into DataFrames.
    Supports header auto-inference when header row resolves to 0 (auto) or specification uses ':auto'.
    """
    if mapper is None:
        mapper = SheetTableMapper()
        
    result: Dict[str, pd.DataFrame] = {}
    for spec in sheet_specs:
        sheet_name, header_row = parse_sheet_info(spec)
        # Ensure the sheet is registered with the mapper
        mapper.add_sheet(sheet_name)
        # Determine actual header row
        effective_header_row = header_row
        if effective_header_row == 0:  # explicit auto
            effective_header_row = infer_header_row(excel_file, sheet_name)
        elif effective_header_row is None or effective_header_row < 1:
            effective_header_row = default_header_row
        try:
            df = excel_file.parse(sheet_name, header=effective_header_row-1)  # pandas is 0-based
            result[sheet_name] = df
        except Exception as e:
            raise RuntimeError(f"Failed to load sheet '{sheet_name}': {e}") from e
    return result

def _normalize_headers(cols):
    seen = {}
    out = []
    for c in cols:
        name = str(c).strip()
        base = name
        if base in seen:
            seen[base] += 1
            name = f"{base}_{seen[base]}"
        else:
            seen[base] = 0
        out.append(name)
    return out

try:  # wrap original loader
    _ORIG_LOAD_EXCEL_SHEETS = load_excel_sheets  # type: ignore[name-defined]
except Exception:  # pragma: no cover
    _ORIG_LOAD_EXCEL_SHEETS = None

if _ORIG_LOAD_EXCEL_SHEETS:
    def load_excel_sheets(*args, **kwargs):  # type: ignore[override]
        dfs = _ORIG_LOAD_EXCEL_SHEETS(*args, **kwargs)
        try:
            for k, df in dfs.items():
                df.columns = _normalize_headers(df.columns)
        except Exception:
            pass
        return dfs