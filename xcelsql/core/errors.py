# Minimal error taxonomy for future structured handling.
from enum import Enum, auto

class ErrorCategory(Enum):
    USER_INPUT = auto()
    RUNTIME = auto()
    MAPPING = auto()
    CONFIG = auto()
    INTERNAL = auto()

class XcelSQLException(Exception):
    category: ErrorCategory = ErrorCategory.INTERNAL

    def __init__(self, message: str, *, category: ErrorCategory | None = None):
        super().__init__(message)
        if category:
            self.category = category

class MappingError(XcelSQLException):
    category = ErrorCategory.MAPPING

class UserInputError(XcelSQLException):
    category = ErrorCategory.USER_INPUT

class ConfigError(XcelSQLException):
    category = ErrorCategory.CONFIG

__all__ = [
    'ErrorCategory','XcelSQLException','MappingError','UserInputError','ConfigError'
]
