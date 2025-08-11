#!/usr/bin/env python
"""Unit tests for the xcelsql package."""
import unittest
import pandas as pd
from xcelsql.utils.excel_utils import SheetTableMapper
from xcelsql.core.sql_engine import (
    validate_query, validate_sheet_names, resolve_query, apply_params
)

class SQLTests(unittest.TestCase):
    """Tests for SQL processing functions."""
    
    def test_query_validation(self):
        # This should pass
        validate_query("SELECT * FROM {Sheet1}", ["Sheet1"], False)
        
        # These should fail
        with self.assertRaises(ValueError):
            validate_query("DELETE FROM {Sheet1}", ["Sheet1"], False)
        
        with self.assertRaises(ValueError):
            validate_query("SELECT * FROM {Unknown}", ["Sheet1"], True)
    
    def test_query_resolution(self):
        mapper = SheetTableMapper()
        mapper.add_sheet("Sheet1")
        df = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
        sheets = {"Sheet1": df}
        
        sql = resolve_query("SELECT * FROM {Sheet1}", sheets, mapper)
        self.assertEqual(sql, "SELECT * FROM sheet1")
    
    def test_param_application(self):
        # Test basic parameter substitution
        sql = "SELECT * FROM table WHERE col = :param"
        params = {"param": "value"}
        result = apply_params(sql, params)
        self.assertEqual(result, "SELECT * FROM table WHERE col = 'value'")
        
        # Test escaping single quotes
        sql = "SELECT * FROM table WHERE name = :name"
        params = {"name": "O'Brien"}
        result = apply_params(sql, params)
        self.assertEqual(result, "SELECT * FROM table WHERE name = 'O''Brien'")
        
        # Test NULL handling
        sql = "SELECT * FROM table WHERE col = :param"
        params = {"param": None}
        result = apply_params(sql, params)
        self.assertEqual(result, "SELECT * FROM table WHERE col = NULL")


class SheetMapperTests(unittest.TestCase):
    """Tests for the SheetTableMapper class."""
    
    def test_sheet_mapper(self):
        mapper = SheetTableMapper()
        
        # Basic mapping
        self.assertEqual(mapper.add_sheet("Sheet1"), "sheet1")
        
        # Sheet with special chars
        self.assertEqual(mapper.add_sheet("Sheet With Spaces"), "sheet_with_spaces")
        
        # Non-ASCII characters
        sheet_name = "データ"  # Japanese characters
        mapped_name = mapper.add_sheet(sheet_name)
        self.assertTrue(len(mapped_name) > 0)
        
        # Leading numeric
        self.assertEqual(mapper.add_sheet("123Sheet"), "s_123sheet")
        
        # Get mapped name
        self.assertEqual(mapper.get_table_name("Sheet1"), "sheet1")
        
        # Reverse lookup
        self.assertEqual(mapper.get_sheet_name("sheet1"), "Sheet1")


if __name__ == "__main__":
    unittest.main()