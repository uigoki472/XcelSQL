"""Constants used throughout the xcelsql package."""

# Output formats supported by the tool
SUPPORTED_OUTPUT_FORMATS = ['table', 'csv', 'excel', 'json', 'jsonl', 'parquet']
DEFAULT_OUTPUT_FORMAT = 'table'

# SQL security restrictions
FORBIDDEN_SQL_TOKENS = [
    'CREATE', 'ALTER', 'DROP', 'TRUNCATE', 'DELETE', 'UPDATE', 'INSERT', 
    'MERGE', 'GRANT', 'REVOKE', 'COMMIT', 'ROLLBACK', 'SAVEPOINT', 'CONNECT',
    'SET', 'PRAGMA', 'COPY', 'VACUUM', 'ANALYZE', 'ATTACH', 'DETACH',
    'BEGIN', 'END', 'TRANSACTION'
]

# Sheet name validation (strict mode)
FORBIDDEN_SHEET_NAME_PATTERN = r'^[A-Za-z][A-Za-z0-9_]*$'