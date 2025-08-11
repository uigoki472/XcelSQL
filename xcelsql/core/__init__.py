"""Core package namespace and backward compatibility mapping."""
import sys

# Lazy legacy mapping helper
def _map_legacy(old: str, new: str):
    if old not in sys.modules:
        try:
            sys.modules[old] = __import__(new, fromlist=['*'])
        except Exception:
            pass

_legacy = {
    'xcelsql.transform_core': 'xcelsql.core.transform_core',
    'xcelsql.sql_engine': 'xcelsql.core.sql_engine',
    'xcelsql.sheet_io': 'xcelsql.core.sheet_io',
    'xcelsql.template_engine': 'xcelsql.core.template_engine',
    'xcelsql.output_writer': 'xcelsql.core.output_writer',
    'xcelsql.progress': 'xcelsql.core.progress',
}
for _o, _n in _legacy.items():
    _map_legacy(_o, _n)

__all__ = []