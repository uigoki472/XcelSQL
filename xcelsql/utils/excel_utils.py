"""Excel utility functions and classes."""
import re
import string
from typing import Dict, List, Optional, Tuple


class ExcelTransformError(Exception):
    """Exception raised for transformation failures."""
    pass

class SheetTableMapper:
    """Maps Excel sheet names to safe SQL table names."""
    
    def __init__(self):
        self.name_map: Dict[str, str] = {}
        self.reverse_map: Dict[str, str] = {}
        self.counter = 0
    
    def add_sheet(self, sheet_name: str) -> str:
        """Add sheet and return safe SQL table name."""
        if sheet_name in self.name_map:
            return self.name_map[sheet_name]
        
        # Generate SQL-safe name
        safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', sheet_name.lower())
        if not safe_name:
            safe_name = f"sheet_{self.counter}"
            self.counter += 1
        elif not re.match(r'^[a-zA-Z]', safe_name):
            safe_name = f"s_{safe_name}"
            
        # Avoid duplicates
        base_name = safe_name
        suffix = 1
        while safe_name in self.reverse_map:
            safe_name = f"{base_name}_{suffix}"
            suffix += 1
        
        self.name_map[sheet_name] = safe_name
        self.reverse_map[safe_name] = sheet_name
        return safe_name
    
    def get_table_name(self, sheet_name: str) -> str:
        """Get safe SQL table name for sheet."""
        if sheet_name not in self.name_map:
            return self.add_sheet(sheet_name)
        return self.name_map[sheet_name]
    
    def get_sheet_name(self, table_name: str) -> Optional[str]:
        """Get original sheet name from table name."""
        return self.reverse_map.get(table_name)

def excel_col_to_index(col_str: str) -> int:
    """Convert Excel column string (A, B, AA, etc) to 0-based index."""
    index = 0
    for char in col_str:
        index = index * 26 + (ord(char.upper()) - ord('A') + 1)
    return index - 1

def index_to_excel_col(index: int) -> str:
    """Convert 0-based index to Excel column string (A, B, AA, etc)."""
    if index < 0:
        raise ValueError("Index must be non-negative")
    result = ""
    index += 1  # Convert to 1-based for the calculation
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        result = string.ascii_uppercase[remainder] + result
    return result