"""CLI entry for XcelSQL with subcommands.

Subcommands:
  run          Execute a one-shot transformation
  repl         Start interactive REPL (optional workbook path)
  list-sheets  List sheets in an Excel workbook
  scaffold     Generate a template + Mapping scaffold
  functions    List registered custom expression functions
  cache        Manage the sheet cache
  config       View or update configuration
  profile      Enable performance profiling
"""
from __future__ import annotations
import argparse
import sys
import os
import logging
import pandas as pd
from typing import Optional, Dict, List
from xcelsql.core.transform_core import run_transform
from xcelsql.core.sheet_io import parse_sheet_info
from xcelsql.core.expr_eval import list_registered_functions
from xcelsql.cli.repl import start_repl
from xcelsql.utils.constants import SUPPORTED_OUTPUT_FORMATS, DEFAULT_OUTPUT_FORMAT
import xcelsql.core.custom_functions as custom_functions  # Import to register custom functions
from xcelsql.utils.logging_setup import configure_logging
from xcelsql.utils.config import config
from xcelsql.utils.cache_manager import cache_manager
from xcelsql.utils.profiler import profiler
from xcelsql.utils.validation import validate_input_file, ValidationError

logger = logging.getLogger(__name__)

ASCII_BANNER = r"""
\ \  /           |  ___|   _ \  |     
 \  /   __|  _ \ |\___ \  |   | |     
    \  (     __/ |      | |   | |     
 _/\_\\___|\___|_|_____/ \__\_\_____| 
                                      
    SQL-powered Excel transformations
"""


# --- Helpers shared across subcommands ---

def _infer_output_format(output_path: Optional[str]) -> str:
    if not output_path:
        return DEFAULT_OUTPUT_FORMAT
    lower = output_path.lower()
    if lower.endswith(('.xlsx', '.xlsm', '.xls')):
        return 'excel'
    if lower.endswith('.csv'):
        return 'csv'
    if lower.endswith(('.jsonl', '.ndjson')):
        return 'jsonl'
    if lower.endswith('.json'):
        return 'json'
    if lower.endswith(('.parquet', '.pq')):
        return 'parquet'
    return DEFAULT_OUTPUT_FORMAT


def _finalize_output_params(fmt: Optional[str], output: Optional[str], no_auto_ext: bool) -> tuple[str, Optional[str]]:
    resolved_fmt = fmt or _infer_output_format(output)
    path = output
    if resolved_fmt == 'table':
        if path:
            logger.warning("Ignoring output path '%s' for table format (stdout)", path)
            path = None
        return resolved_fmt, path
    if path:
        lower = path.lower()
        if resolved_fmt == 'excel' and not lower.endswith(('.xlsx', '.xlsm', '.xls')) and not no_auto_ext:
            path += '.xlsx'
            logger.info("Appended .xlsx extension -> %s", path)
        if resolved_fmt == 'parquet' and not lower.endswith(('.parquet', '.pq')) and not no_auto_ext:
            path += '.parquet'
            logger.info("Appended .parquet extension -> %s", path)
        if fmt:  # user provided explicit format
            inferred = _infer_output_format(path)
            if inferred != resolved_fmt:
                logger.warning("Explicit format '%s' differs from path extension (inferred '%s') - using explicit format", resolved_fmt, inferred)
    return resolved_fmt, path


def _parse_params(param_list: List[str]) -> Dict[str, str]:
    params: Dict[str, str] = {}
    for item in param_list:
        if '=' not in item:
            logger.warning("Ignoring malformed --param '%s' (expected k=v)", item)
            continue
        k, v = item.split('=', 1)
        k = k.strip()
        if not k.isidentifier():
            logger.warning("Parameter name '%s' is not a valid identifier; skipping", k)
            continue
        params[k] = v
    return params


def _validate_sheets(path: str, sheets: Optional[List[str]]) -> None:
    if sheets is None or not sheets:
        raise SystemExit("--sheet is required.")
    with pd.ExcelFile(path) as xls:
        available = xls.sheet_names
        for spec in sheets:
            sheet_name = parse_sheet_info(spec)[0]
            if sheet_name not in available:
                raise SystemExit("Sheet '%s' not found. Available sheets:\n  %s" % (sheet_name, "\n  ".join(available)))


def _scaffold_template(input_path: str, sheets: List[str], header_row: int, out_path: str) -> int:
    try:
        with pd.ExcelFile(input_path) as xls:
            first_sheet_name, hr = parse_sheet_info(sheets[0]) if sheets else (xls.sheet_names[0], header_row)
            df = pd.read_excel(input_path, sheet_name=first_sheet_name, header=(hr-1), nrows=0)
            empty = pd.DataFrame(columns=df.columns)
            with pd.ExcelWriter(out_path, engine='openpyxl') as writer:
                empty.to_excel(writer, index=False, sheet_name='Template')
                import pandas as _pd
                mapping_df = _pd.DataFrame({'template_column': df.columns, 'source_expression': df.columns})
                mapping_df.to_excel(writer, index=False, sheet_name='Mapping')
            logger.info("Scaffold template written to %s", out_path)
            return 0
    except Exception as e:
        logger.error("Failed to scaffold template: %s", e)
        return 1

# --- Subcommand handlers ---

def cmd_run(args: argparse.Namespace) -> int:
    logging.getLogger().setLevel(args.log_level)
    _validate_sheets(args.input, args.sheets)
    fmt, path = _finalize_output_params(args.output_format, args.output, args.no_auto_ext)
    params = _parse_params(args.param)
    try:
        run_transform(
            input_path=args.input,
            sheets=args.sheets,
            query=args.query,
            output_path=path,
            default_header_row=args.header_row,
            template_path=args.template,
            output_format=fmt,
            show_sql=args.show_sql,
            dry_run=args.dry_run,
            allow_eval=args.allow_eval,
            strict=args.strict,
            params=params,
            limit=args.limit,
            select_columns=args.select_columns,
            fail_on_mapping_error=args.fail_on_mapping_error,
            error_report=args.error_report,
            progress=not args.no_progress
        )
        return 0
    except SystemExit:
        raise
    except Exception as e:
        logger.error("Transformation failed: %s", e)
        return 1


def cmd_repl(args: argparse.Namespace) -> int:
    logging.getLogger().setLevel(args.log_level)
    if not getattr(args, 'no_banner', False):
        print(ASCII_BANNER)
    start_repl(initial_workbook=args.input, allow_eval=args.allow_eval, strict=args.strict)
    return 0


def cmd_list_sheets(args: argparse.Namespace) -> int:
    logging.getLogger().setLevel(args.log_level)
    try:
        with pd.ExcelFile(args.input) as xls:
            print("\n".join(xls.sheet_names))
        return 0
    except FileNotFoundError:
        logger.error("Input file not found: %s", args.input)
        return 1


def cmd_functions(_args: argparse.Namespace) -> int:
    funcs = list_registered_functions()
    if not funcs:
        print("No custom functions registered.")
    else:
        for name, doc in funcs:
            first = doc.strip().splitlines()[0] if doc else ''
            print(f"{name}\t{first}")
    return 0


def cmd_scaffold(args: argparse.Namespace) -> int:
    logging.getLogger().setLevel(args.log_level)
    if not args.sheets:
        print("At least one --sheet required to infer headers.")
        return 2
    return _scaffold_template(args.input, args.sheets, args.header_row, args.output)


def cmd_banner(_args: argparse.Namespace) -> int:
    print(ASCII_BANNER)
    return 0

def cmd_cache(args: argparse.Namespace) -> int:
    """Handle cache management commands."""
    logging.getLogger().setLevel(args.log_level)
    
    if args.clear:
        if args.file:
            try:
                validate_input_file(args.file)
                count = cache_manager.clear_cache(args.file)
                print(f"Cleared {count} cache files for {args.file}")
            except ValidationError as e:
                print(f"Error: {e}")
                return 1
        else:
            count = cache_manager.clear_cache()
            print(f"Cleared {count} cache files from cache directory")
    elif args.stats:
        # Get cache stats
        cache_dir = cache_manager.cache_dir
        try:
            files = os.listdir(cache_dir)
            cache_files = [f for f in files if f.endswith(('.pkl', '.json'))]
            total_size = sum(os.path.getsize(os.path.join(cache_dir, f)) for f in cache_files)
            
            from string_utils import format_bytes
            print(f"Cache directory: {cache_dir}")
            print(f"Cache files: {len(cache_files)}")
            print(f"Total size: {format_bytes(total_size)}")
        except Exception as e:
            print(f"Error reading cache: {e}")
            return 1
    elif args.disable:
        config.set("cache_enabled", False)
        config.save()
        print("Cache disabled")
    elif args.enable:
        config.set("cache_enabled", True)
        config.save()
        print("Cache enabled")
    else:
        print(f"Cache {'enabled' if config.get('cache_enabled') else 'disabled'}")
        print(f"Cache directory: {cache_manager.cache_dir}")
        
    return 0

def cmd_config(args: argparse.Namespace) -> int:
    """Handle configuration commands."""
    logging.getLogger().setLevel(args.log_level)
    
    if args.list:
        for key, value in config.settings.items():
            print(f"{key} = {value}")
    elif args.get:
        value = config.get(args.get)
        print(f"{args.get} = {value}")
    elif args.set and args.value is not None:
        # Convert value to appropriate type
        value = args.value
        if value.lower() == 'true':
            value = True
        elif value.lower() == 'false':
            value = False
        elif value.lower() == 'none':
            value = None
        elif value.isdigit():
            value = int(value)
        
        config.set(args.set, value)
        config.save()
        print(f"Set {args.set} = {value}")
    else:
        print(f"Configuration file: {config.config_file}")
        
    return 0

def cmd_profile(args: argparse.Namespace) -> int:
    """Configure and manage profiling."""
    logging.getLogger().setLevel(args.log_level)
    
    if args.enable:
        profiler.enabled = True
        config.set("profiling_enabled", True)
        config.save()
        print("Profiling enabled")
    elif args.disable:
        profiler.enabled = False
        config.set("profiling_enabled", False)
        config.save()
        print("Profiling disabled")
    elif args.reset:
        profiler.reset()
        print("Profiling statistics reset")
    else:
        profiler.print_report()
        
    return 0

# --- Parser construction ---

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog='xcelsql', description='Excel transformation utility')
    sub = p.add_subparsers(dest='command', required=True)

    # run
    run_p = sub.add_parser('run', help='Execute a transformation')
    run_p.add_argument('input', help='Input Excel file')
    run_p.add_argument('--sheet', action='append', dest='sheets', required=True, help="Sheet spec Sheet[:header]")
    run_p.add_argument('--header-row', type=int, default=1, help='Default header row index (1-based)')
    run_p.add_argument('--query', help='SELECT query (use {SheetName} placeholders)')
    run_p.add_argument('--template', help='Template Excel path (with optional Mapping sheet)')
    run_p.add_argument('--output', help='Output file path (omit to print table)')
    run_p.add_argument('--output-format', choices=SUPPORTED_OUTPUT_FORMATS, help='Explicit output format')
    run_p.add_argument('--no-auto-ext', action='store_true', help='Do not append .xlsx if missing')
    run_p.add_argument('--allow-eval', action='store_true', help='Enable Python eval fallback for expressions')
    run_p.add_argument('--show-sql', action='store_true', help='Print resolved SQL and exit')
    run_p.add_argument('--dry-run', action='store_true', help='Validate and exit without executing')
    run_p.add_argument('--strict', action='store_true', help='Strict validation (sheet name pattern, placeholders)')
    run_p.add_argument('--param', action='append', default=[], metavar='k=v', help='SQL param :k substitution (repeatable)')
    run_p.add_argument('--limit', type=int, help='Limit output rows (post-query)')
    run_p.add_argument('--select', action='append', dest='select_columns', help='Column projection when no --query (repeatable)')
    run_p.add_argument('--fail-on-mapping-error', action='store_true', help='Exit on any template mapping errors')
    run_p.add_argument('--error-report', help='Write JSON mapping error report to path')
    run_p.add_argument('--log-level', default='INFO', choices=['DEBUG','INFO','WARNING','ERROR','CRITICAL'])
    run_p.add_argument('--no-progress', action='store_true', help='Disable progress spinner')
    run_p.add_argument('--no-cache', action='store_true', help='Disable cache for this operation')

    # repl
    repl_p = sub.add_parser('repl', help='Start interactive REPL')
    repl_p.add_argument('input', nargs='?', help='Optional Excel file to preload')
    repl_p.add_argument('--allow-eval', action='store_true', help='Enable Python eval fallback')
    repl_p.add_argument('--strict', action='store_true', help='Strict validation mode')
    repl_p.add_argument('--log-level', default='INFO', choices=['DEBUG','INFO','WARNING','ERROR','CRITICAL'])
    repl_p.add_argument('--no-banner', action='store_true', help='Suppress ASCII banner on start')
    repl_p.add_argument('--no-cache', action='store_true', help='Disable cache for this session')

    # list-sheets
    ls_p = sub.add_parser('list-sheets', help='List sheets of a workbook')
    ls_p.add_argument('input', help='Excel file')
    ls_p.add_argument('--log-level', default='INFO', choices=['DEBUG','INFO','WARNING','ERROR','CRITICAL'])

    # functions
    sub.add_parser('functions', help='List registered custom functions')

    # scaffold
    sc_p = sub.add_parser('scaffold', help='Create template scaffold from first sheet')
    sc_p.add_argument('input', help='Excel file')
    sc_p.add_argument('--sheet', action='append', dest='sheets', help='Sheet spec (at least one required)')
    sc_p.add_argument('--header-row', type=int, default=1, help='Header row for scaffold sheet')
    sc_p.add_argument('--output', required=True, help='Output template path (.xlsx)')
    sc_p.add_argument('--log-level', default='INFO', choices=['DEBUG','INFO','WARNING','ERROR','CRITICAL'])

    # banner
    sub.add_parser('banner', help='Show ASCII logo banner')
    
    # cache management
    cache_p = sub.add_parser('cache', help='Manage sheet cache')
    cache_p.add_argument('--clear', action='store_true', help='Clear the cache')
    cache_p.add_argument('--file', help='Clear cache only for specific file')
    cache_p.add_argument('--stats', action='store_true', help='Show cache statistics')
    cache_p.add_argument('--disable', action='store_true', help='Disable caching')
    cache_p.add_argument('--enable', action='store_true', help='Enable caching')
    cache_p.add_argument('--log-level', default='INFO', choices=['DEBUG','INFO','WARNING','ERROR','CRITICAL'])
    
    # config management
    config_p = sub.add_parser('config', help='View or update configuration')
    config_p.add_argument('--list', action='store_true', help='List all configuration values')
    config_p.add_argument('--get', metavar='KEY', help='Get specific configuration value')
    config_p.add_argument('--set', metavar='KEY', help='Set configuration value')
    config_p.add_argument('--value', help='Value to set (used with --set)')
    config_p.add_argument('--log-level', default='INFO', choices=['DEBUG','INFO','WARNING','ERROR','CRITICAL'])
    
    # profile management
    profile_p = sub.add_parser('profile', help='Performance profiling tools')
    profile_p.add_argument('--enable', action='store_true', help='Enable profiling')
    profile_p.add_argument('--disable', action='store_true', help='Disable profiling')
    profile_p.add_argument('--reset', action='store_true', help='Reset profiling statistics')
    profile_p.add_argument('--log-level', default='INFO', choices=['DEBUG','INFO','WARNING','ERROR','CRITICAL'])

    return p

# --- Main entry ---

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    
    # Configure logging first
    if hasattr(args, 'log_level'):
        configure_logging(args.log_level)
        
    # Set up profiling if enabled in config
    profiler.enabled = config.get('profiling_enabled', False)
    
    # Set cache state if needed
    if hasattr(args, 'no_cache') and args.no_cache:
        cache_manager.enabled = False
    
    # Handle command
    try:
        if args.command == 'run':
            code = cmd_run(args)
        elif args.command == 'repl':
            code = cmd_repl(args)
        elif args.command == 'list-sheets':
            code = cmd_list_sheets(args)
        elif args.command == 'functions':
            code = cmd_functions(args)
        elif args.command == 'scaffold':
            code = cmd_scaffold(args)
        elif args.command == 'banner':
            code = cmd_banner(args)
        elif args.command == 'cache':
            code = cmd_cache(args)
        elif args.command == 'config':
            code = cmd_config(args)
        elif args.command == 'profile':
            code = cmd_profile(args)
        else:
            parser.error('Unknown command')
            return
        
        # Print profile report if enabled
        if profiler.enabled:
            profiler.print_report()
            
        sys.exit(code)
    except ValidationError as e:
        logging.error(f"Validation error: {e}")
        sys.exit(2)
    except KeyboardInterrupt:
        logging.warning("Operation interrupted by user")
        sys.exit(130)
    except Exception as e:
        logging.error(f"Unhandled error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
