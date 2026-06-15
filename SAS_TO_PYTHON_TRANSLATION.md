# SAS-to-Python Translation Guide

Translation of eight SAS data-transformation macros from `Macro/` into equivalent
Python/pandas functions in `python/sas_transforms/`.

## Quick Reference

| SAS Macro | Python Module | Python Function | Key pandas API |
|---|---|---|---|
| `%transpose` | `transpose.py` | `transpose()` | `DataFrame.pivot_table`, manual melt |
| `%subset_data` | `subset_data.py` | `subset_data()` | `iloc`, `query`, `eval`, `rename` |
| `%compare` | `compare.py` | `compare_datasets()`, `compare()` | `merge(indicator=True)`, vectorized `!=` |
| `%dedup_string` | `dedup_string.py` | `dedup_string()`, `dedup_string_series()` | `str.split`, `set` |
| `%dedup_mstring` | `dedup_mstring.py` | `dedup_mstring()` | `re.split`, `set` |
| `%export_csv` | `export_csv.py` | `export_csv()` | `DataFrame.to_csv` |
| `%export_xlsx` | `export_xlsx.py` | `export_xlsx()` | `DataFrame.to_excel` (openpyxl) |
| `%export_dbms` | `export_dbms.py` | `export_dbms()` | `to_excel`, `to_stata` |

---

## 1. `%transpose` → `transpose()`

### SAS Behaviour
`PROC TRANSPOSE` pivots a tall dataset into wide format.  The macro wraps
`PROC TRANSPOSE` with pre-sorting, column renaming (`_NAME_`, `_LABEL_`, `COL#`),
and BY-group support.

### Translation Decisions
| SAS Concept | Python Approach | Rationale |
|---|---|---|
| `PROC SORT` + `PROC TRANSPOSE` | Sort via `sort_values`, then manual group iteration | pandas has no single PROC TRANSPOSE equivalent; `pivot_table` only covers the `ID=` case |
| `BY` statement | `groupby` iteration | Preserves per-group transposition semantics |
| `_NAME_` / `_LABEL_` columns | Explicit columns in output dict | Matches SAS metadata columns |
| `COL1..COLn` naming | `f"COL{idx}"` with optional rename map | Mirrors SAS default naming |
| `ID=` parameter | `pivot_table` with `aggfunc="last"` | SAS keeps the last occurrence when `LET` is specified; `"last"` matches |
| `SORT=N` / `NOTSORTED=Y` | `sort=False` kwarg | Skips the pre-sort step |
| `WHERE=` dataset option | `df.query()` before transposing | Equivalent row filter |
| `COPY=` variables | Carried through from first row per group | SAS copies from last.bygroup; first row chosen for simplicity |

### Signature Mapping
```
SAS:    %transpose(DATA=, OUT=, BY=, VAR=, ID=, SORT=Y, COL=, NAME=_NAME_, LABEL=_LABEL_, WHERE=, COPY=)
Python: transpose(data, *, by=, var=, id_col=, sort=True, col=, name="_NAME_", label="_LABEL_", where=, copy=)
```

### Limitations
- `FORMAT=` / `LBL=` (temporary formats/labels on input) are not supported; apply formatting before calling.
- `PREFIX=` is not exposed; rename via `col=` instead.
- `IDLABEL=` is not implemented (rare use case).

---

## 2. `%subset_data` → `subset_data()`

### SAS Behaviour
Subsets a dataset by observations (rows) and variables (columns) in a single step.
Supports non-contiguous observation ranges (`1-5 or 11-15`), WHERE clauses,
subsetting IF, KEEP/DROP, RENAME, and FIRSTOBS/LASTOBS.

### Translation Decisions
| SAS Concept | Python Approach | Rationale |
|---|---|---|
| `OBS=1-5 or 11-15` range syntax | Regex parser → 0-based index list | Reproduces the SAS `prxparse` chain that converts ranges to subsetting-if |
| `FIRSTOBS=` / `LASTOBS=` | `iloc[start:end]` | Direct 1-to-0 index translation |
| `WHERE=` | `df.query()` | pandas query DSL closely matches SAS WHERE syntax |
| `IF=` subsetting if | `df.eval()` | Evaluates arbitrary expressions row-wise |
| `RENAME=` before `KEEP=` | `rename()` then column selection | Matches SAS order: rename is a dataset option applied before the data step body |
| `KEEP=` / `DROP=` | Column selection / `drop()` | Direct mapping |

### Signature Mapping
```
SAS:    %subset_data(DATA=, OUT=, WHERE=, IF=, FIRSTOBS=, LASTOBS=, OBS=, KEEP=, DROP=, RENAME=)
Python: subset_data(data, *, where=, if_expr=, firstobs=, lastobs=, obs=, keep=, drop=, rename=)
```

### Notes
- SAS `IF=` is renamed to `if_expr=` to avoid shadowing Python's `if` keyword.
- `RENAME=` accepts a `dict` (`{"old": "new"}`) instead of SAS `old=new` pairs.
- Observation indices use 1-based numbering in the `obs` string to match SAS, but
  are converted to 0-based internally.

---

## 3. `%compare` → `compare_datasets()` / `compare()`

### SAS Behaviour
Wraps `PROC COMPARE` for dataset-level comparison (column differences, row
differences, value differences with numeric tolerance).  Also supports library-level
comparison (iterate over matching datasets in two librefs).

### Translation Decisions
| SAS Concept | Python Approach | Rationale |
|---|---|---|
| `PROC COMPARE` dataset mode | `merge(how="outer", indicator=True)` | Identifies left-only, right-only, and matched rows |
| `BY=` key variables | `merge(on=by)` | Aligns rows by key before comparing |
| Positional comparison (no BY) | Row-by-row comparison via `iloc[:min_rows]` | Matches SAS positional comparison |
| `METHOD=EXACT` | `!=` with NaN-aware logic | Exact equality |
| `METHOD=ABSOLUTE` + `CRITERION=` | `abs(a - b) > criterion` | Numeric fuzzy match |
| Library comparison | `dict[str, DataFrame]` input | Python has no libref; a dict of named DataFrames serves the same purpose |
| `FILTER=` regex | `re.compile(pattern).search()` | Mirrors SAS `prxmatch` filter |
| Structured output | `CompareResult` dataclass | Replaces SAS printed report with programmatic access |

### Signature Mapping
```
SAS:    %compare(BASE=, COMP=, BY=, FILTER=, CRITERION=.000001, METHOD=EXACT)
Python: compare_datasets(base, comp, *, by=, criterion=1e-6, method="exact")
        compare(base, comp, *, by=, filter_pattern=, criterion=, method=)
```

### Notes
- `compare()` auto-dispatches: two DataFrames → dataset mode, two dicts → library mode.
- `CHECKOBS=` and `MAXPRINT=` (display limits) have no equivalent; all differences are
  returned in `CompareResult.value_diffs`.

---

## 4. `%dedup_string` → `dedup_string()`

### SAS Behaviour
A DATA-step macro that removes duplicate tokens from a character variable using
`indexw(upcase(...))` for case-insensitive comparison.  Operates within a running
data step; the Python version operates on a plain string.

### Translation Decisions
| SAS Concept | Python Approach | Rationale |
|---|---|---|
| `scan()` tokenization | `str.split(dlm)` | Equivalent delimiter-based splitting |
| `indexw(upcase(...))` duplicate check | `set` with `upper()` keys | O(1) lookup vs SAS O(n) scan; same semantics |
| `catx(' ', ...)` output | `" ".join(result)` | SAS `catx` always uses single delimiter |
| In-place update (`OUTVAR=INVAR`) | Return value replaces original | Python strings are immutable; caller reassigns |
| DATA step context | `dedup_string_series()` for vectorized use | Wraps scalar function over a pandas Series |

### Signature Mapping
```
SAS:    %dedup_string(INVAR=, OUTVAR=, DLM=)
Python: dedup_string(value, *, dlm=None, case_sensitive=False)
```

---

## 5. `%dedup_mstring` → `dedup_mstring()`

### SAS Behaviour
A pure macro-level dedup (runs at compile time).  Removes duplicate words from a
macro variable string.  Supports separate input and output delimiters and
multi-character input delimiter lists.

### Translation Decisions
| SAS Concept | Python Approach | Rationale |
|---|---|---|
| `%scan(..., indlm)` tokenization | `re.split("[chars]", ...)` for multi-char delimiters | SAS treats each char in a multi-char delimiter as a separate delimiter |
| Output delimiter defaulting | `dlm = indlm if len(indlm)==1 else " "` | Reproduces SAS conditional logic |
| Macro-level vs data-step | Plain function | No meaningful distinction in Python |
| `indexw` duplicate check | `set` with `upper()` keys | Same as `dedup_string` |
| Token stripping | `token.strip()` after split | SAS `%scan` auto-strips leading/trailing spaces around tokens |

### Signature Mapping
```
SAS:    %dedup_mstring(IN, INDLM=, DLM=)
Python: dedup_mstring(value, *, indlm=None, dlm=None)
```

---

## 6. `%export_csv` → `export_csv()`

### SAS Behaviour
Wrapper around `%export_dlm` with `DBMS=CSV`.  Exports a SAS dataset to a
comma-separated file with options for header, labels, and replace.

### Translation Decisions
| SAS Concept | Python Approach | Rationale |
|---|---|---|
| `%export_dlm(dbms=csv)` | `DataFrame.to_csv()` | Direct pandas equivalent |
| `REPLACE=N` default | `FileExistsError` if file exists | Matches SAS warning + no-output behaviour |
| `LABEL=Y` header | Rename columns from `attrs["_labels"]` before writing | SAS uses dataset labels; pandas has no built-in label system |
| `HEADER=N` | `header=False` in `to_csv` | Direct mapping |
| `LRECL=32767` | Not applicable | Line length limit is a SAS file I/O concept |
| `DBMS=TAB` / `DBMS=DLM` | `delimiter=` parameter | Unified via delimiter arg |
| Directory-only PATH | Derive filename from `DataFrame.name` | Mirrors SAS dataset name derivation |

### Signature Mapping
```
SAS:    %export_csv(DATA=, PATH=, REPLACE=N, LABEL=N, HEADER=Y, LRECL=32767)
Python: export_csv(data, path, *, replace=False, label=False, header=True, delimiter=",")
```

---

## 7. `%export_xlsx` → `export_xlsx()`

### SAS Behaviour
Wrapper around `%export_dbms` with `DBMS=XLSX`.

### Translation Decisions
| SAS Concept | Python Approach | Rationale |
|---|---|---|
| `%export_dbms(dbms=xlsx)` | Delegates to `export_dbms()` | Matches SAS wrapper pattern |
| openpyxl engine | `engine="openpyxl"` in `to_excel` | Required for `.xlsx` format |
| Sheet name | Configurable `sheet_name` (default `"Sheet1"`) | SAS PROC EXPORT uses "Sheet1" |

### Signature Mapping
```
SAS:    %export_xlsx(DATA=, PATH=, REPLACE=N, LABEL=N)
Python: export_xlsx(data, path, *, replace=False, label=False, sheet_name="Sheet1")
```

---

## 8. `%export_dbms` → `export_dbms()`

### SAS Behaviour
General-purpose `PROC EXPORT` wrapper supporting XLSX, XLS, SPSS, and STATA
output formats.  Handles path resolution (directory vs file), existence checking,
replace logic, label substitution, and cleanup of `.bak` files.

### Translation Decisions
| SAS Concept | Python Approach | Rationale |
|---|---|---|
| `PROC EXPORT` dispatch | `to_excel` / `to_stata` / `pyreadstat.write_sav` | pandas + pyreadstat cover all four formats |
| `DBMS=` validation | `ValueError` for unsupported types | Matches SAS `%parmv` validation |
| Path = directory → derive filename | `Path.is_dir()` + `DataFrame.name` | Mirrors SAS logic |
| `.bak` file cleanup | `Path.unlink()` after export | Matches SAS post-export cleanup |
| Fileref concept | Not applicable | SAS filerefs have no Python equivalent; physical paths only |
| `REPLACE=N` + file exists | `FileExistsError` | Matches SAS warning behaviour |
| `LABEL=Y` | Rename columns from `attrs["_labels"]` | Consistent with export_csv approach |

### Signature Mapping
```
SAS:    %export_dbms(DATA=, PATH=, DBMS=XLSX, REPLACE=N, LABEL=N)
Python: export_dbms(data, path, *, dbms="xlsx", replace=False, label=False, sheet_name="Sheet1")
```

---

## General Translation Patterns

### Parameter Validation
SAS uses `%parmv` for parameter validation (required, case, allowed values).
Python uses type hints + explicit `ValueError`/`TypeError` raises.

### Dataset Identity
SAS macros default `DATA=&syslast` (last created dataset).  Python functions require
an explicit `data` argument — there is no global "last dataset" concept.

### Output Dataset
SAS macros write to `OUT=` datasets.  Python functions return new DataFrames
(or file paths for export functions).  This is more Pythonic and avoids side effects.

### Column Labels
SAS datasets have a built-in label system (`LABEL` statement).  Python DataFrames
do not.  We store labels in `DataFrame.attrs["_labels"]` as a `dict[str, str]`
and apply them on demand during export.

### Boolean Parameters
SAS uses `0/1/Y/N/YES/NO/TRUE/FALSE` with `%parmv` normalization.
Python uses native `bool` (`True`/`False`).

### Missing Values
SAS distinguishes between `.` (numeric missing) and `""` (character missing).
Python uses `NaN` / `None` / `pd.NaT` uniformly via pandas.

---

## Running the Tests

```bash
cd python/
pip install pandas openpyxl pytest
python -m pytest tests/ -v
```

All tests validate that the Python functions produce equivalent results to the
SAS originals for the sample inputs documented in each macro's header.
