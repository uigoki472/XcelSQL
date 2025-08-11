# XcelSQL

SQL-powered Excel transformation engine


![XcelSQL Logo](./logo.svg#gh-light-mode-only)
![XcelSQL Logo Dark](./logo_dark.svg#gh-dark-mode-only)


## Why XcelSQL?
Organizations still rely on Excel for critical operational and analytical data, yet need repeatable, inspectable, automatable data flows. Traditional ETL tooling is heavyweight for ad‑hoc or departmental use; copy/paste workflows are error‑prone and opaque.

XcelSQL provides a lightweight, scriptable interface allowing teams to:
- Treat Excel sheets as queriable relations via familiar SQL semantics.
- Apply reproducible transformations & mappings with optional templating.
- Automate exports (Excel / CSV / JSON / JSONL / Parquet / tabular stdout) without opening Excel.
- Prototype interactively, then operationalize the same logic non‑interactively (CI/CD / scheduled jobs).

Business value:
- Reduces manual spreadsheet manipulation risk.
- Accelerates “Excel → downstream system” pipelines.
- Improves governance: transformations exist as versioned text (queries + mapping sheets).
- Bridges Excel‑first analysts and SQL‑first engineers.

---
## Current Capabilities Snapshot
| Domain | Capability | Status |
|--------|------------|--------|
| Ingestion | Multiple sheets; explicit per‑sheet header spec (`Sheet[:header]`) | Implemented (explicit & auto inference) |
| Projection | Column selection without full SQL (`--select`) | Implemented |
| Parameters | Named SQL params via `--param k=v` | Implemented |
| SQL Placeholders | `{SheetName}` substitution in query text | Implemented |
| Templates | Scaffold template + Mapping sheet | Implemented |
| Mapping Validation | Fail/report issues (`--fail-on-mapping-error`) | Basic (enhanced diagnostics planned) |
| Output Formats | excel, csv, json, jsonl, parquet, table | Implemented |
| REPL | Interactive exploration (colors, history, search, functions) | Evolving |
| Custom Functions | Discovery / listing | Implemented |
| Progress Feedback | Optional spinner / stats progress | Implemented (basic) |
| Strict Mode | Stricter validation toggles | Implemented |
| Eval Fallback | Opt‑in Python `eval` for expressions | Implemented (unsafe by design) |
| Dry Run | Validate without side effects | Implemented |
| CLI Extensibility | Subcommand architecture | Implemented |
| Caching | Optional sheet / metadata cache | Implemented (docs minimal) |

---
## Quick Start
```bash
# List sheets
xcelsql list-sheets data/workbook.xlsx

# Simple projection without writing SQL
xcelsql run data/workbook.xlsx \
  --sheet Sales:2 \
  --select OrderID --select Amount --select Region \
  --output sales.csv

# SQL join with parameter
xcelsql run data/datamart.xlsx \
  --sheet Sales:2 --sheet Regions:1 \
  --query "SELECT s.OrderID, r.RegionName FROM {Sales} s JOIN {Regions} r ON s.RegionID=r.ID WHERE s.RegionID=r.ID AND s.OrderDate >= :start" \
  --param start=2024-01-01 \
  --output enriched.jsonl

# Export to Parquet directly
xcelsql run data/workbook.xlsx \
  --sheet Sales:2 \
  --query "SELECT * FROM {Sales}" \
  --output sales.parquet

# Generate scaffold (Template + Mapping sheets)
xcelsql scaffold data/source.xlsx --sheet Sales:2 --output sales_template.xlsx
```

### Quick Start (Sample Workbook)
Using the bundled Microsoft Financial sample (sheet name: `Sheet1`).
```bash
# Inspect sheet list
xcelsql list-sheets samples/financial.xlsx

# Describe columns & inferred types (lightweight)
xcelsql run samples/financial.xlsx \
  --sheet Sheet1 \
  --select Segment --select Country --select Product --select Sales \
  --output sample_subset.csv

# Aggregate profit by year & segment
xcelsql run samples/financial.xlsx \
  --sheet Sheet1 \
  --query "SELECT Year, Segment, SUM(Profit) AS TotalProfit FROM {Sheet1} GROUP BY Year, Segment ORDER BY Year, TotalProfit DESC" \
  --output profit_by_segment.parquet

# Parameterized minimum year filter
xcelsql run samples/financial.xlsx \
  --sheet Sheet1 \
  --query "SELECT Year, Country, SUM(Sales) AS SalesUSD FROM {Sheet1} WHERE Year >= :min_year GROUP BY Year, Country ORDER BY Year, SalesUSD DESC" \
  --param min_year=2013 \
  --output sales_since_2013.jsonl

# Open REPL for exploratory analysis
xcelsql repl samples/financial.xlsx
# Inside REPL examples:
#  xlsql> SELECT DISTINCT Segment FROM Sheet1;
#  xlsql> \limit 20
#  xlsql> SELECT Country, SUM(Profit) p FROM Sheet1 GROUP BY Country ORDER BY p DESC;
#  xlsql> \export csv top_countries.csv
```

---
## Sample Data
A sample workbook is included for experimentation:
- samples/financial.xlsx (Microsoft Power BI "Financial sample")

Attribution: Financial sample data © Microsoft. Source and download instructions: https://learn.microsoft.com/en-us/power-bi/create-reports/sample-financial-download. Provided strictly for demonstration/testing; original Microsoft terms apply. Not covered by this project's MIT license. Remove before distributing derivative works if license terms require.

---
## Installation
Project uses uv for environment & dependency management.

Status: package not yet published to PyPI.

Optional dependency (Parquet export): install pyarrow (recommended) or fastparquet yourself. Planned extras syntax after publish: pip install xcelsql[parquet]. Until then:
```
uv add pyarrow   # enable --output *.parquet
```
If pyarrow/fastparquet is missing and you request parquet output, an explicit runtime error will explain how to install it.

1. Install uv (if needed)
   curl -LsSf https://astral.sh/uv/install.sh | sh
   # or see https://docs.astral.sh/uv/ for Windows / alternative methods

2. Clone & sync
```bash
git clone https://github.com/naqvis/xcelsql.git
cd xcelsql
uv sync        # creates .venv & installs project + dev deps (from [tool.uv])
```

3. Use the CLI
```bash
uv run xcelsql --help
```

Common dev tasks:
```bash
# Run tests (core + dev dependencies already installed by 'uv sync')
uv run pytest

# Run with coverage (pytest-cov already in dev-dependencies)
uv run pytest --cov

# Add a NEW runtime dependency (only if you introduce one)
uv add <package>

# Add an optional Parquet dependency (if you need Parquet export)
uv add pyarrow   # or: uv add fastparquet

# Add a NEW dev dependency
uv add --dev <package>

# Remove a dependency
uv remove <package>
```
The core dependencies (duckdb, pandas, openpyxl) are defined in pyproject.toml and installed automatically; no manual add needed.

Editable install is automatic with uv (no separate pip -e needed). The virtual environment lives under .venv by default.

Future (after publish):
```bash
uv add xcelsql     # or: pip install xcelsql
xcelsql --help
```

Environment variable overrides (optional):
- XCELSQL_DISPLAY_LIMIT
- XCELSQL_MAX_COL_WIDTH
- XCELSQL_HEADER_ROW
- XCELSQL_TIMING=1 (enable timing)
- XCELSQL_COLOR=1 (ANSI color)
- (Planned) XCELSQL_PARAM_<NAME>=value to predefine parameters

---
## Security & Safety
- `--allow-eval` enables Python `eval` fallback for expressions: only use in trusted environments; never feed untrusted input.
- Future: sandbox / AST whitelist for safe expression evaluation.
- Principle: secure by default (explicit opt‑in for risky features).
- openpyxl loads cell values only (formulas are evaluated by Excel, macros/VBA are NOT executed here).
- No external network I/O performed by core engine.

---
## Recipes (Common Patterns)
Short examples for fast onboarding.

Projection without SQL (subset of columns):
```
xcelsql run data/book.xlsx --sheet Sales:2 --select OrderID --select Amount --output sales.csv
```
Join + parameter filter:
```
xcelsql run data/datamart.xlsx \
  --sheet Sales:2 --sheet Regions:1 \
  --query "SELECT s.OrderID, r.RegionName FROM {Sales} s JOIN {Regions} r ON s.RegionID=r.ID WHERE s.RegionID=r.ID AND s.OrderDate >= :start" \
  --param start=2024-01-01 --output enriched.jsonl
```
Force header override (bad first line):
```
xcelsql run data/raw.xlsx --sheet RawData:3 --query "SELECT * FROM {RawData}" --output cleaned.parquet
```
Watch a query (quick dashboard):
```
xcelsql repl data/book.xlsx
xlsql> \watch 5 SELECT Region, SUM(Amount) amt FROM "Sales" GROUP BY 1 ORDER BY 2 DESC;
```
Mapping workflow (scaffold → edit → run):
```
xcelsql scaffold data/source.xlsx --sheet Sales:2 --output sales_template.xlsx
# Edit Mapping sheet expressions, then:
xcelsql run sales_template.xlsx --sheet Sales:2 --query "SELECT * FROM {Template}" --output final.xlsx
```
Parquet export for downstream analytics:
```
xcelsql run data/book.xlsx --sheet Sales:2 --query "SELECT * FROM {Sales}" --output sales.parquet
```

---
## Error Taxonomy (Initial)
| Category | Typical Cause | Example |
|----------|---------------|---------|
| USER_INPUT | Bad flag, unknown sheet, invalid header row | sheet name typo |
| MAPPING | Expression in mapping sheet fails | unknown function in source_expression |
| RUNTIME | DuckDB execution issue | type mismatch in join |
| CONFIG | Missing required option / conflicting flags | mutually exclusive flags (future) |
| INTERNAL | Unexpected unhandled condition | please file issue |

(Structured codes & dedicated exit codes beyond 0–2 are planned.)

---
## Performance Tips
- Narrow columns early: `SELECT col1,col2,...` instead of `SELECT *` when large sheets.
- Use WHERE filters to reduce in-memory result size quickly.
- Prefer Parquet for large downstream exports (columnar & compressed).
- Disable color (`\color off`) if piping output or when rendering huge tables.
- Use `--select` for quick thin extracts without parsing full SQL.
- Reuse REPL session: repeat queries faster (in‑process DuckDB, cached sheets).
- For very wide sheets, increase clarity with `\x` (vertical) or reduce columns.

---
## Large Workbook Navigation
- List metrics: `\dt+` (loaded marker * with rows & memory for loaded sheets).
- Regex search: `\search Revenue` or `\search ^Q[1-4]_`.
- Quick column peek: `\columns "Some Sheet"` (does not fully load data).
- Infered header sanity: `\hdrshow` then override via `\hdr SheetName 2`.
- Use smaller targeted queries before broad joins to cut initial load time.

---
## Output Formats (Characteristics)
| Format | Human Friendly | Streaming-ish | Excel Compatible | Notes |
|--------|----------------|---------------|------------------|-------|
| table  | Yes (TTY) | No (buffered) | N/A | REPL only, pretty ANSI optional |
| csv    | Moderate | Yes | Yes | UTF-8 with BOM for Excel compatibility |
| json   | Readable | No | Yes (import) | Pretty printed records array |
| jsonl  | Grep-able | Yes | Yes | One JSON object per line |
| parquet| No | Columnar | Yes (via tools) | Requires pyarrow or fastparquet (optional install) |
| excel  | Native | No | Yes | Written via openpyxl |

Parquet install quick start (if missing):
```
uv add pyarrow  # or: pip install pyarrow
```

---
## Unicode & Locale
- Assumes UTF-8 input/output.
- CSV exports include UTF-8 BOM to ensure Excel opens with correct encoding.
- East Asian wide characters accounted for in table width calculations.
- No locale-specific date parsing beyond what pandas / DuckDB provide.

---
## FAQ
Q: Why DuckDB?  
A: In-process analytics engine with strong SQL coverage, fast columnar execution, zero external service to manage.

Q: Difference between `--select` and full `--query`?  
A: `--select` builds a simple projection query automatically; `--query` provides full SQL power (joins, filters, expressions).

Q: When to use a template + mapping sheet vs direct SQL?  
A: Mapping sheet shines when business users iteratively adjust column expressions without editing SQL files; SQL preferred for quicker ad‑hoc joins/filters.

Q: How are headers inferred?  
A: Simple heuristic: picks first sampled row with highest count of textual (letter‑containing) cells; override with `Sheet:row` or `\hdr`.

Q: Are Excel formulas executed?  
A: No. Only stored values are read; macros/VBA ignored.

Q: How to reduce memory footprint?  
A: Limit columns, push filters into SQL, export to Parquet, avoid loading unneeded sheets (lazy loading is default).

Q: How do parameters work?  
A: Pass `--param name=value` then reference as `:name` in SQL; inside REPL use `\set name=value`.

Q: Can I chain transformations?  
A: Yes—use CTEs (`WITH ...`) or create intermediate Parquet/Excel exports then re-run.

---
## Limitations (Current)
- REPL: Enhanced, but still missing: richer completion (context-aware suggestions beyond prefixes), configurable history persistence, and advanced metadata caching (only basic lazy load now).
- Header auto-inference heuristic is simplistic; can mis-detect in sparse / multi-line header sheets (workaround: explicit `Sheet:row` or `\hdr`).
- Mapping diagnostics: lacks severity tiers, aggregated summaries, and machine-readable structured report export (planned improvements).
- Windows: minimal real-world path / console testing (needs broader verification).
- Error taxonomy is preliminary: unified error codes & exit codes (>2) not finalized; structured JSON error output pending.
- Distribution: not yet published to PyPI (install requires repo clone + uv).

---
## Contributing
1. Fork & branch (`feature/<topic>`)
2. Add / update tests
3. Ensure tests pass (`uv run pytest`)
4. Submit PR with concise rationale & usage example

Using uv:
```bash
uv run pytest
```

Planned tooling: pre-commit hooks, GitHub Actions (tests, build).

---
## CLI Reference (Abbrev.)
```
xcelsql run <file.xlsx> --sheet Sheet1:1 [--query SQL | --select Col ...] [--output out.xlsx]
xcelsql scaffold <file.xlsx> --sheet Sheet1 --output template.xlsx
xcelsql repl [file.xlsx]
xcelsql list-sheets <file.xlsx>
xcelsql functions
xcelsql cache --stats
```
REPL key commands:
```
\dt / \dt+            list sheets (basic / with metrics)
\loaded               list only loaded sheets
\open <sheet>         force-load sheet
\reload <sheet>       reload sheet
\search <pattern>     filter sheet names (regex or substring fallback)
\d <sheet>            describe columns (sample dtypes)
\columns <sheet>      quick column name list
\hdr <sheet> <row>    set header row (override inference)
\hdrshow [sheet]      show header rows
\limit [n]            show/set display limit
\format [fmt]         table|csv|json|jsonl|parquet
\x                    toggle expanded row display
\colwidth [n]         max column width
\params / \set / \unset manage SQL params
\save <name> <sql>    save query
\run <name>           execute saved query
\showsql              show last transformed SQL
\history [n|clear]    show or clear recent queries
\version              show XcelSQL & DuckDB versions
\functions            list available DuckDB functions
\watch <sec> [sql]    rerun query periodically
\stats                workbook stats (with progress + scan time)
\export <fmt> <path>  export last result (excel|csv|json|jsonl|parquet)
\savefmt <fmt> <path> export without changing current format
\color [on|off]       toggle ANSI color
\timing [on|off]      toggle timing
\cache [on|off]       toggle caching flag (placeholder)
\clear                clear loaded data
\restart              full session reset
\show / \showconfig   show session JSON
\help [cmd]           command help
```
---
## Support
- Issues: https://github.com/naqvis/xcelsql/issues


---
## License
MIT License (see LICENSE file).

---
## Trademark & Branding
"XcelSQL" name & logos (logo*.svg) belong to this project; attribute if reused.

---
© 2025 XcelSQL Project