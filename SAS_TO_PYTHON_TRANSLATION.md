# SAS-to-Python Translation Reference

This document maps each SAS macro in `Macro/` to its Python/pandas equivalent in `python/sas_transforms/`, explaining the key translation decisions.

---

## 1. `%transpose` → `transpose()`

| SAS | Python |
|-----|--------|
| `Macro/transpose.sas` | `python/sas_transforms/transpose.py` |

### What it does
Wraps `PROC TRANSPOSE`: sorts by BY variables, then pivots VAR columns into rows (long-form) or, with `ID=`, into columns named after ID values (wide-form).

### Translation decisions

| SAS construct | Python equivalent | Rationale |
|---|---|---|
| `PROC SORT` + `PROC TRANSPOSE` | `DataFrame.sort_values()` + custom `_transpose_group()` | pandas has no single PROC TRANSPOSE equivalent; `melt()` covers the common case but not the `COL1..COLn` naming convention |
| `BY` statement | `groupby(by, sort=False)` + per-group transpose | Preserves SAS semantics: each BY-group is transposed independently |
| `VAR` statement | Explicit column list; defaults to numeric columns | Matches SAS default: "all numeric variables" when VAR is omitted |
| `ID=` parameter | `pivot_table(columns=id)` | SAS ID turns values into column headers — this is a pivot, not a melt |
| `LET` option | `aggfunc='last'` in pivot_table | SAS LET keeps the last duplicate ID value per BY-group |
| `_NAME_` / `_LABEL_` | Configurable output columns; `None` drops them | SAS drops these when the macro parameters are blank |
| `COL=` rename | Post-transpose `rename(columns=...)` | SAS renames `COL1..COLn` via dataset options |
| `PREFIX=` | Custom prefix on generated column names | Direct mapping |
| `NOTSORTED` | `sort=False` on groupby | SAS `NOTSORTED` preserves input order |
| `COPY=` | Columns carried through via first-row lookup per group | SAS COPY passes variables through without transposing |
| `WHERE=` | `DataFrame.query(where)` before transpose | Applied at the input dataset level, same as SAS |

### Key difference
SAS PROC TRANSPOSE creates `COL1..COLn` where n = number of observations per BY-group. The Python version does the same. When using `ID=`, SAS creates columns named after the formatted ID values — `pivot_table` provides this naturally.

---

## 2. `%subset_data` → `subset_data()`

| SAS | Python |
|-----|--------|
| `Macro/subset_data.sas` | `python/sas_transforms/subset_data.py` |

### What it does
Subsets a dataset by rows (WHERE, IF, OBS ranges, FIRSTOBS/LASTOBS) and columns (KEEP, DROP, RENAME) in a single DATA step.

### Translation decisions

| SAS construct | Python equivalent | Rationale |
|---|---|---|
| `RENAME=` dataset option | `DataFrame.rename(columns=dict)` applied first | SAS RENAME is a dataset option on SET — it fires before IF/WHERE/KEEP/DROP |
| `WHERE` clause | `DataFrame.query(where)` | Direct pandas equivalent |
| Subsetting `IF` | `DataFrame.query(if_)` after WHERE | SAS IF executes after SET (including RENAME); separate from WHERE |
| `OBS=%str(1-5 or 11-15)` | `_parse_obs_ranges()` → list of 0-based indices | SAS uses 1-based `_N_`; regex parser converts `"M-N"` ranges and `"or"` conjunctions to index slices |
| `FIRSTOBS=` / `LASTOBS=` (obs=) | `DataFrame.iloc[start:end]` | SAS dataset options use 1-based inclusive ranges |
| `KEEP=` / `DROP=` | Column selection / `drop(columns=...)` | Applied last to match SAS DATA step order |

### Key difference
SAS evaluation order is: dataset options (FIRSTOBS/LASTOBS/RENAME) → WHERE (source-level filter) → subsetting IF (including OBS/_N_ checks). Python version replicates this: RENAME first, then FIRSTOBS/LASTOBS, then WHERE, then OBS ranges, then IF, then KEEP/DROP.

The `obs` parameter accepts SAS-style range syntax (`"1-5 or 11-15 or 20-30"`) and is parsed with regex into pandas integer location indices.

---

## 3. `%compare` → `compare()`

| SAS | Python |
|-----|--------|
| `Macro/compare.sas` | `python/sas_transforms/compare.py` |

### What it does
Wraps `PROC COMPARE` for dataset-level or library-level comparisons. Reports column differences, row differences, and cell-level value differences.

### Translation decisions

| SAS construct | Python equivalent | Rationale |
|---|---|---|
| Dataset vs library detection (`EXIST` / `LIBREF`) | `isinstance(base, dict)` vs `isinstance(base, DataFrame)` | Python uses type dispatch; dict of DataFrames ≈ SAS libref |
| `PROC COMPARE ... BY id;` | Sort + outer merge on BY keys | Identifies rows unique to base/comp and shared rows |
| PROC COMPARE value comparison | Per-cell iteration over common columns | Checks each value pair for differences |
| `METHOD=EXACT` | `bv != cv` | SAS EXACT is bitwise equality |
| `METHOD=ABSOLUTE` | `abs(bv - cv) > criterion` | Numeric tolerance |
| `METHOD=RELATIVE` | `abs(bv - cv) / max(abs(bv), abs(cv)) > criterion` | Proportional tolerance |
| `METHOD=PERCENT` | `abs((bv - cv) / bv) * 100 > criterion` | Percentage difference |
| `CRITERION=.000001` | `criterion=1e-6` default | Same default fuzz factor |
| `MAXPRINT=(50,1000)` | `maxprint=50` (max diffs to collect) | Limits output volume |
| Library comparison report | `LibraryCompareResult` with matched/unmatched members | Recursive call to dataset compare for each matched pair |
| `FILTER=cla*\|shoes` | `re.compile(filter).search(name)` | SAS uses PRXMATCH; Python uses re module |
| Keys dataset for per-table BY vars | Not implemented — pass BY directly | This is a SAS convenience for metadata-driven comparisons |

### Return types
- `CompareResult` — for dataset comparisons: contains `base_only_cols`, `comp_only_cols`, `common_cols`, `base_only_rows`, `comp_only_rows`, `value_diffs`, and `equal` flag.
- `LibraryCompareResult` — for library comparisons: contains member-level matching info and per-member `CompareResult`.

---

## 4. `%dedup_string` → `dedup_string()`

| SAS | Python |
|-----|--------|
| `Macro/dedup_string.sas` | `python/sas_transforms/dedup_string.py` |

### What it does
DATA-step macro that removes duplicate tokens from a character variable, preserving the order of first appearance. Case-insensitive comparison.

### Translation decisions

| SAS construct | Python equivalent | Rationale |
|---|---|---|
| `SCAN(__temp, __i, ' ')` | `invar.split(dlm)` | Token splitting |
| `INDEXW(UPCASE(&outvar), UPCASE(__word))` | `set` lookup on `token.upper()` | Case-insensitive dedup; O(1) lookup vs O(n) INDEXW |
| `CATX(' ', &outvar, __word)` | `" ".join(result)` | Reconstruct output |
| In-place update (`OUTVAR=INVAR`) | Returns new string (immutable in Python) | Python strings are immutable |
| `DLM=` parameter | `dlm` keyword arg, defaults to space | Same delimiter concept |

### Additional utility
`dedup_string_series()` applies the function element-wise to a pandas Series, useful when the SAS macro would be called inside a DATA step processing multiple rows.

---

## 5. `%dedup_mstring` → `dedup_mstring()`

| SAS | Python |
|-----|--------|
| `Macro/dedup_mstring.sas` | `python/sas_transforms/dedup_mstring.py` |

### What it does
Pure macro (compile-time) that removes duplicate words from a macro variable string. Supports separate input and output delimiters.

### Translation decisions

| SAS construct | Python equivalent | Rationale |
|---|---|---|
| `%SCAN(%superq(in), &i, %str(&indlm))` | `str.split(indlm)` or `re.split(pattern, in_)` | Single-char indlm uses `split()`; multi-char indlm uses regex with character class |
| `INDEXW(&out, &word, %str(&dlm))` | `set` lookup (case-sensitive) | SAS macro INDEXW with explicit delimiter is case-sensitive |
| Output delimiter logic | `dlm` defaults: 1-char indlm → same; multi-char → space | Matches SAS: "If len(indlm)=1, use indlm; else use space" |
| `%UNQUOTE(&out)` | No equivalent needed | Python has no macro quoting layer |

### Key difference from `dedup_string`
- `dedup_mstring` is **case-sensitive** (SAS macro context). `dedup_string` is **case-insensitive** (SAS DATA step context with `UPCASE()`).
- `dedup_mstring` supports multi-character input delimiters where each character is a separate delimiter.

---

## 6. `%export_csv` → `export_csv()`

| SAS | Python |
|-----|--------|
| `Macro/export_csv.sas` → `Macro/export_dlm.sas` | `python/sas_transforms/export_csv.py` |

### What it does
Wrapper around `%export_dlm` that exports a SAS dataset to a CSV file using a DATA step (not PROC EXPORT), giving control over header labels and record length.

### Translation decisions

| SAS construct | Python equivalent | Rationale |
|---|---|---|
| `DATA _null_; FILE &path DSD DLM=","` | `DataFrame.to_csv(path, index=False)` | pandas CSV writer handles quoting/escaping |
| `LABEL` option (column labels as header) | `header=[labels.get(c, c) for c in columns]` | Labels passed as a dict mapping; SAS reads from dataset metadata |
| `HEADER=N` | `header=False` in `to_csv()` | Direct mapping |
| `REPLACE=N` | `FileExistsError` check | SAS prints a WARNING; Python raises |
| `LRECL=32767` | Accepted but ignored | pandas handles line length automatically |
| Directory-only PATH → auto-name | `Path.is_dir()` check + derive name from `df.name` | SAS derives from the dataset name in the libref |

---

## 7. `%export_xlsx` → `export_xlsx()`

| SAS | Python |
|-----|--------|
| `Macro/export_xlsx.sas` → `Macro/export_dbms.sas` | `python/sas_transforms/export_xlsx.py` |

### What it does
Wrapper around `%export_dbms` that exports to XLSX format.

### Translation decisions

| SAS construct | Python equivalent | Rationale |
|---|---|---|
| `PROC EXPORT ... DBMS=XLSX` | `DataFrame.to_excel(path, engine='openpyxl')` | openpyxl is the standard pandas Excel engine |
| `LABEL` option | Column rename via `labels` dict before writing | SAS uses `LABEL` statement on PROC EXPORT |
| `.bak` file cleanup | Not needed | pandas doesn't create backup files |
| REPLACE logic | `FileExistsError` check | Same pattern as export_csv |

---

## 8. `%export_dbms` → `export_dbms()`

| SAS | Python |
|-----|--------|
| `Macro/export_dbms.sas` | `python/sas_transforms/export_dbms.py` |

### What it does
General-purpose PROC EXPORT wrapper supporting XLSX, XLS, SPSS (.sav), and Stata (.dta) formats.

### Translation decisions

| SAS construct | Python equivalent | Rationale |
|---|---|---|
| `DBMS=XLSX` | `DataFrame.to_excel(engine='openpyxl')` | Standard pandas engine |
| `DBMS=XLS` | `DataFrame.to_excel(engine='openpyxl')` | xlwt is deprecated; write as xlsx via openpyxl |
| `DBMS=SPSS` | `pyreadstat.write_sav()` | pandas doesn't have native SPSS write; pyreadstat is the community standard |
| `DBMS=STATA` | `DataFrame.to_stata(write_index=False)` | Native pandas support |
| `LABEL` option | `DataFrame.rename(columns=labels)` before export | Renames columns to label values for the output file |
| Path resolution (dir → dir/dsname.ext) | `Path.is_dir()` + derive filename | Same logic as SAS: if path is a directory, append dataset name + extension |
| Fileref support | Not implemented | Python doesn't have SAS filerefs; use file paths directly |
| `.bak` file cleanup | Not needed | pandas export doesn't create backup files |

---

## Cross-Cutting Translation Patterns

### SAS `&syslast` defaults
Several macros default `DATA=` and `OUT=` to `&syslast` (the last dataset created). Python has no global "last DataFrame" state. All functions require explicit `data` arguments.

### Parameter validation (`%parmv`)
SAS macros use `%parmv` for parameter validation (required, word lists, case normalisation, boolean coercion). Python equivalents use type hints, default arguments, and explicit `ValueError` / `TypeError` raises.

### Boolean parameters
SAS accepts `0 1 OFF N NO F FALSE ON Y YES T TRUE` for boolean options. Python functions accept native `bool` values.

### Dataset options
SAS dataset options like `WHERE=()`, `KEEP=`, `DROP=`, `RENAME=()` are applied inline on dataset references. Python separates these into explicit function parameters.

### Missing values
SAS `.` (numeric missing) and `""` (character missing) map to `numpy.nan` / `None` / `pandas.NA`. The `compare` function handles NaN-to-NaN equality correctly.

### 1-based vs 0-based indexing
SAS uses 1-based observation numbers (`_N_`, FIRSTOBS, LASTOBS). Python/pandas uses 0-based indexing. All translation functions accept 1-based parameters (matching SAS signatures) and convert internally.
