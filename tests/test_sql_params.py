#!/usr/bin/env python3
"""Test SQL parameter substitution.

This script tests the fixed apply_params function to ensure it properly 
handles SQL parameter substitution without relying on duckdb.escape_string.
"""
import unittest
import sys
from xcelsql.core.sql_engine import apply_params

class TestSQLParams(unittest.TestCase):
    """Test case for SQL parameter substitution."""
    
    def test_basic_substitution(self):
        """Test basic parameter substitution."""
        sql = "SELECT * FROM table WHERE col = :param"
        params = {"param": "value"}
        expected = "SELECT * FROM table WHERE col = 'value'"
        self.assertEqual(apply_params(sql, params), expected)
    
    def test_escaping_quotes(self):
        """Test escaping of single quotes."""
        sql = "SELECT * FROM table WHERE name = :name"
        params = {"name": "O'Brien"}
        expected = "SELECT * FROM table WHERE name = 'O''Brien'"
        self.assertEqual(apply_params(sql, params), expected)
    
    def test_multiple_params(self):
        """Test multiple parameter substitutions."""
        sql = "SELECT * FROM table WHERE col1 = :param1 AND col2 = :param2"
        params = {"param1": "value1", "param2": "value2"}
        expected = "SELECT * FROM table WHERE col1 = 'value1' AND col2 = 'value2'"
        self.assertEqual(apply_params(sql, params), expected)
    
    def test_invalid_identifier(self):
        """Test handling of invalid identifiers."""
        sql = "SELECT * FROM table WHERE col = :123invalid"
        params = {"123invalid": "value"}
        expected = "SELECT * FROM table WHERE col = :123invalid"
        self.assertEqual(apply_params(sql, params), expected)
    
    def test_sql_injection_prevention(self):
        """Test prevention of SQL injection."""
        sql = "SELECT * FROM table WHERE name = :name"
        params = {"name": "'; DROP TABLE users; --"}
        expected = "SELECT * FROM table WHERE name = '''; DROP TABLE users; --'"
        self.assertEqual(apply_params(sql, params), expected)
    
    def test_null_value(self):
        """Test handling of NULL values."""
        sql = "SELECT * FROM table WHERE col = :param"
        params = {"param": None}
        expected = "SELECT * FROM table WHERE col = NULL"
        self.assertEqual(apply_params(sql, params), expected)
    
    def test_param_not_in_query(self):
        """Test parameter that doesn't appear in the query."""
        sql = "SELECT * FROM table"
        params = {"param": "value"}
        expected = "SELECT * FROM table"
        self.assertEqual(apply_params(sql, params), expected)
    
    def test_empty_params(self):
        """Test empty params dictionary."""
        sql = "SELECT * FROM table WHERE col = :param"
        params = {}
        expected = "SELECT * FROM table WHERE col = :param"
        self.assertEqual(apply_params(sql, params), expected)
    
    def test_none_params(self):
        """Test None params."""
        sql = "SELECT * FROM table WHERE col = :param"
        params = None
        expected = "SELECT * FROM table WHERE col = :param"
        self.assertEqual(apply_params(sql, params), expected)

if __name__ == "__main__":
    unittest.main()