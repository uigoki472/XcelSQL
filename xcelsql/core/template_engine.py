"""Template-based data transformation engine."""
from __future__ import annotations
import re
import pandas as pd
import logging
from typing import Any, Dict, List, Optional, Set, Tuple
from xcelsql.core.expr_eval import evaluate_expression

logger = logging.getLogger(__name__)

# Error record type: {column: [{row: int, expression: str, error: str}]}

def extract_template_mapping(template_path: str) -> Tuple[List[str], Dict[str, str], Dict[str, Any]]:
    """Extract mapping from template file.
    
    Returns (template_columns, expressions, metadata)
    """
    try:
        with pd.ExcelFile(template_path) as xls:
            sheets = xls.sheet_names
            if 'Mapping' not in sheets:
                logger.warning("Template has no 'Mapping' sheet, will use column names directly")
                if 'Template' not in sheets:
                    raise ValueError("Template file must have 'Template' sheet when no 'Mapping' provided")
                template_df = pd.read_excel(template_path, sheet_name='Template')
                columns = list(template_df.columns)
                expressions = {col: col for col in columns}
                return columns, expressions, {}
            
            # Load mapping
            mapping_df = pd.read_excel(template_path, sheet_name='Mapping')
            required_cols = ['template_column', 'source_expression']
            missing = [c for c in required_cols if c not in mapping_df.columns]
            if missing:
                raise ValueError(f"Mapping sheet missing required columns: {', '.join(missing)}")
            
            # Build mapping dictionary
            mapping: Dict[str,str] = {}
            meta: Dict[str,Any] = {}
            for _, row in mapping_df.iterrows():
                template_col = str(row['template_column']).strip()
                source_expr = row['source_expression']
                if pd.isna(source_expr):
                    # Skip blank expression
                    continue
                mapping[template_col] = str(source_expr)
                
                # Extract any metadata columns
                for col in mapping_df.columns:
                    if col.startswith('meta_') and col != 'meta_disabled':
                        meta.setdefault(col, {})[template_col] = row.get(col)
            
            # Load template structure if available
            if 'Template' in sheets:
                template_df = pd.read_excel(template_path, sheet_name='Template')
                columns = list(template_df.columns)
            else:
                # Use mapping keys as template columns
                columns = list(mapping.keys())
            
            # Filter columns with expressions
            filtered_columns = [c for c in columns if c in mapping]
            if len(filtered_columns) < len(columns):
                logger.warning("%d columns ignored (no mapping expression)", len(columns) - len(filtered_columns))
            
            return filtered_columns, mapping, meta
    except Exception as e:
        logger.error("Failed to load template: %s", e)
        raise


def apply_template_transform(
    data: pd.DataFrame, 
    template_path: str, 
    fail_on_error: bool = False
) -> Tuple[pd.DataFrame, Dict[str, List[Dict[str, Any]]]]:
    """Apply template transformation to data.
    
    Returns (transformed_df, error_dict) where error_dict maps column -> list of error records.
    """
    try:
        columns, expressions, metadata = extract_template_mapping(template_path)
        
        # Build output dataframe
        rows = []
        errors: Dict[str, List[Dict[str, Any]]] = {}
        
        for idx, source_row in data.iterrows():
            row_data = source_row.to_dict()
            target_row: Dict[str,Any] = {}
            
            for col in columns:
                expr = expressions.get(col)
                if not expr:
                    continue
                
                try:
                    value = evaluate_expression(expr, row_data)
                    target_row[col] = value
                except Exception as e:  # collect detailed error
                    rec = {"row": int(idx)+1, "expression": expr, "error": str(e)}
                    errors.setdefault(col, []).append(rec)
                    if fail_on_error:
                        raise ValueError(f"Mapping error column={col} row={idx+1}: {e}") from e
                    # Use error message as value
                    target_row[col] = f"[Error: {e}]"
            
            rows.append(target_row)
        
        result_df = pd.DataFrame(rows, columns=columns)
        return result_df, errors
    
    except Exception as e:
        if fail_on_error:
            raise
        logger.error("Template transformation failed: %s", e)
        # Return original data and error
        return data, {"template_error": [{"row": None, "expression": None, "error": str(e)}]}