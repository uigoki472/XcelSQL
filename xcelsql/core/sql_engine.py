"""SQL validation, resolution, and execution utilities."""
from __future__ import annotations
from typing import Dict, List, Optional
import pandas as pd
import duckdb
import re
import logging
from xcelsql.utils.excel_utils import SheetTableMapper
from xcelsql.utils.constants import FORBIDDEN_SQL_TOKENS, FORBIDDEN_SHEET_NAME_PATTERN

logger = logging.getLogger(__name__)
FORBIDDEN_SQL_REGEX = re.compile(r'\b(' + '|'.join(FORBIDDEN_SQL_TOKENS) + r')\b', re.IGNORECASE)
SHEET_NAME_RE = re.compile(FORBIDDEN_SHEET_NAME_PATTERN)


def validate_query(query: Optional[str], available_sheets: List[str], strict: bool) -> None:
    if not query:
        return
    stripped = query.lstrip()
    if not stripped.upper().startswith("SELECT"):
        raise ValueError("Only SELECT queries are permitted.")
    sanitized = re.sub(r"'[^']*'", "''", stripped)
    for match in FORBIDDEN_SQL_REGEX.finditer(sanitized):
        raise ValueError(f"Query contains forbidden token: {match.group(1).upper()}")
    refs = list(re.finditer(r'\{([^}]+)\}', query))
    if not refs and strict:
        raise ValueError("No sheet placeholders found in query under --strict mode.")
    for m in refs:
        ref = m.group(1)
        if ref not in available_sheets:
            raise ValueError(f"Query references unknown sheet: '{ref}' (available: {', '.join(available_sheets)})")


def validate_sheet_names(sheet_names: List[str], strict: bool) -> None:
    for name in sheet_names:
        if strict and not SHEET_NAME_RE.match(name):
            raise ValueError(f"Sheet name '{name}' fails strict pattern {FORBIDDEN_SHEET_NAME_PATTERN}")


def resolve_query(query: Optional[str], sheet_data: Dict[str, pd.DataFrame], mapper: SheetTableMapper) -> str:
    if not query:
        first_sheet_name = next(iter(sheet_data.keys()))
        return f"SELECT * FROM {mapper.get_table_name(first_sheet_name)}"
    def repl(m: re.Match) -> str:
        return mapper.get_table_name(m.group(1))
    pattern = re.compile(r'\{(' + '|'.join(re.escape(s) for s in sheet_data.keys()) + r')\}')
    return pattern.sub(repl, query)


def apply_params(sql: str, params: Optional[Dict[str, str]]) -> str:
    """Apply parameter substitutions to SQL.
    
    Replaces :param references with properly escaped values.
    """
    if not params:
        return sql
        
    for k, v in params.items():
        if not isinstance(k, str) or not k.isidentifier():
            continue  # Skip invalid identifiers
            
        # Properly escape the value for SQL
        if v is None:
            escaped_value = 'NULL'
        else:
            # Standard SQL escaping: double single quotes
            escaped_value = "'" + v.replace("'", "''") + "'"
            
        # Replace :param with the escaped value
        sql = re.sub(rf':{re.escape(k)}\b', escaped_value, sql)
    return sql


def apply_limit(sql: str, limit: Optional[int]) -> str:
    if limit is None:
        return sql
    return f"SELECT * FROM ({sql}) sub LIMIT {limit}"


def execute_query(
    sheet_data: Dict[str, pd.DataFrame],
    query: Optional[str],
    mapper: SheetTableMapper,
    show_sql: bool = False,
    dry_run: bool = False,
    strict: bool = False,
    params: Optional[Dict[str, str]] = None,
    limit: Optional[int] = None
) -> pd.DataFrame:
    if not sheet_data:
        raise ValueError("No sheet data provided")
    validate_sheet_names(list(sheet_data.keys()), strict)
    validate_query(query, list(sheet_data.keys()), strict)
    sql = resolve_query(query, sheet_data, mapper)
    if params:
        sql = apply_params(sql, params)
    sql = apply_limit(sql, limit)
    logger.info("Resolved SQL:\n%s", sql)
    if show_sql or dry_run:
        if dry_run:
            logger.info("Dry run: skipping execution.")
        return pd.DataFrame()
    with duckdb.connect() as con:
        for sheet_name, df in sheet_data.items():
            con.register(mapper.get_table_name(sheet_name), df)
        try:
            return con.execute(sql).df()
        except Exception as e:
            logger.error("Query execution failed: %s", e)
            raise RuntimeError("Query execution failed") from e