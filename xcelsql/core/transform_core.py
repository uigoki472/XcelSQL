"""Core transformation orchestration function."""
from __future__ import annotations
from typing import List, Optional, Dict
import pandas as pd
import logging
import time
from xcelsql.utils.excel_utils import SheetTableMapper, ExcelTransformError  # type: ignore
from xcelsql.core.sheet_io import load_excel_sheets
from xcelsql.core.sql_engine import execute_query  # type: ignore
from xcelsql.core.template_engine import apply_template_transform
from xcelsql.core.output_writer import write_output
from xcelsql.core.expr_eval import set_eval_fallback
from xcelsql.core.progress import spinner

logger = logging.getLogger(__name__)


def _ensure_logging() -> None:
    """Attach a basic stream handler if none configured (ensures user sees logs by default)."""
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
        )


def _format_bytes(num: int) -> str:
    for unit in ['B','KB','MB','GB','TB']:
        if num < 1024:
            return f"{num:.1f}{unit}"
        num /= 1024
    return f"{num:.1f}PB"


def _approx_df_mem(dfs: Dict[str, pd.DataFrame]) -> int:
    try:
        return sum(df.memory_usage(deep=True).sum() for df in dfs.values())
    except Exception:
        return 0


def run_transform(
    input_path: str,
    sheets: List[str],
    query: Optional[str],
    output_path: Optional[str],
    default_header_row: int,
    template_path: Optional[str],
    output_format: str,
    show_sql: bool,
    dry_run: bool,
    allow_eval: bool,
    strict: bool,
    params: Optional[Dict[str, str]],
    limit: Optional[int],
    select_columns: Optional[List[str]],
    fail_on_mapping_error: bool,
    error_report: Optional[str] = None,
    progress: bool = False
) -> None:
    _ensure_logging()
    start = time.time()
    set_eval_fallback(allow_eval)
    mapper = SheetTableMapper()
    try:
        with spinner("Loading sheets", enabled=progress):
            with pd.ExcelFile(input_path) as xls:
                sheet_data = load_excel_sheets(xls, sheets, default_header_row, mapper)
    except FileNotFoundError:
        logger.error("Input file not found: %s", input_path)
        raise ExcelTransformError(f"Input file not found: {input_path}")
    total_rows = sum(len(df) for df in sheet_data.values())
    mem_bytes = _approx_df_mem(sheet_data)
    if mem_bytes:
        logger.info("Loaded %d sheets (%d rows, ~%s in memory)", len(sheet_data), total_rows, _format_bytes(mem_bytes))
    else:
        logger.info("Loaded %d sheets (%d rows)", len(sheet_data), total_rows)
    if len(sheets) > 1:
        mapper.print_mappings()
    effective_query = query
    if select_columns and not query:
        first_sheet = sheets[0]
        proj = ', '.join(select_columns)
        effective_query = f"SELECT {proj} FROM {{{first_sheet.split(':',1)[0]}}}"
    result_df = execute_query(sheet_data, effective_query, mapper, show_sql=show_sql, dry_run=dry_run, strict=strict, params=params)
    if limit and not (show_sql or dry_run):
        result_df = result_df.head(limit)
    if show_sql and not dry_run:
        logger.info("SQL displayed (use without --show-sql to execute). Elapsed %.2fs", time.time() - start)
        return
    if dry_run:
        logger.info("Dry run completed (no execution). Elapsed %.2fs", time.time() - start)
        return
    if template_path:
        result_df, errors = apply_template_transform(result_df, template_path, fail_on_error=fail_on_mapping_error)
        if errors and error_report:
            try:
                import json
                with open(error_report, 'w', encoding='utf-8') as f:
                    json.dump(errors, f, indent=2)
                logger.info("Wrote mapping error report to %s", error_report)
            except Exception as e:
                logger.warning("Failed to write error report: %s", e)
    write_output(result_df, output_path, output_format)
    logger.info("Output rows: %d (%.2fs total)", len(result_df), time.time() - start)
