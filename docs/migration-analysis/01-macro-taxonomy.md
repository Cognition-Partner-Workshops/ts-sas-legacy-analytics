# Macro Taxonomy

> 92 reusable SAS macros in `Macro/`, classified by functional domain.

## 1. Parameter & Validation (3 macros)

| Macro | File | Purpose |
|-------|------|---------|
| `%parmv` | parmv.sas | Parameter validation (required, allowed values, type checks) — **used by 78 other macros** |
| `%IsNum` | IsNum.sas | Check if character input is numeric (DATA step) |
| `%IsNumD` | IsNumD.sas | Check if character input is numeric (DATA step variant) |
| `%IsNumM` | IsNumM.sas | Check if macro variable value is numeric |

## 2. Dataset Introspection & Metadata (9 macros)

| Macro | File | Purpose |
|-------|------|---------|
| `%nobs` | nobs.sas | Return observation count of a dataset |
| `%varexist` | varexist.sas | Check if a variable exists in a dataset |
| `%varlist` | varlist.sas | Return variable list from a dataset |
| `%varlist2` | varlist2.sas | Return variable list (alternate implementation) |
| `%get_data_attr` | get_data_attr.sas | Return dataset attribute (nobs, nvar, label, etc.) |
| `%get_lib_attr` | get_lib_attr.sas | Return library attribute (engine, path, etc.) |
| `%guess_pk` | guess_pk.sas | Guess primary key of a dataset/view |
| `%get_dups` | get_dups.sas | Identify duplicate records given key variables |
| `%check_if_empty` / `%empty` | check_if_empty.sas / empty.sas | Check if source dataset has zero observations |

## 3. Data Manipulation & Transformation (7 macros)

| Macro | File | Purpose |
|-------|------|---------|
| `%transpose` | transpose.sas | Transpose input dataset |
| `%subset_data` | subset_data.sas | Subset dataset by observations and variables |
| `%compare` | compare.sas | PROC COMPARE wrapper for two datasets |
| `%attrib` | attrib.sas | Generate ATTRIB statements from a template |
| `%CreateTableOrView` | CreateTableOrView.sas | Create either a SAS table or view dynamically |
| `%create_format` | create_format.sas | Create a format from an input dataset |
| `%randlist` | randlist.sas | Create a random sample list from a dataset |

## 4. Hash Object Utilities (3 macros)

| Macro | File | Purpose |
|-------|------|---------|
| `%hash_define` | hash_define.sas | Define a hash object for later lookup |
| `%hash_lookup` | hash_lookup.sas | Lookup satellite variables from a defined hash |
| `%hash_split_dataset` | hash_split_dataset.sas | Split dataset into multiple outputs via hash |

## 5. Export / Output (12 macros)

| Macro | File | Purpose |
|-------|------|---------|
| `%export` | export.sas | Replacement macro for PROC EXPORT |
| `%export_xlsx` | export_xlsx.sas | Wrapper for PROC EXPORT to Excel (XLSX) |
| `%export_csv` | export_csv.sas | Wrapper for delimited export (CSV) |
| `%export_dlm` | export_dlm.sas | Replacement for PROC EXPORT — delimited files |
| `%export_tab` | export_tab.sas | Wrapper for tab-delimited export |
| `%export_dbms` | export_dbms.sas | Wrapper for PROC EXPORT generic DBMS targets |
| `%export_sas` | export_sas.sas | Copy source dataset to target library |
| `%export_spss` | export_spss.sas | Export to SPSS format |
| `%export_stata` | export_stata.sas | Export to Stata format |
| `%export_saphari` | export_saphari.sas | Export to SQL Server or SAPHARI format |
| `%export_rldx` | export_rldx.sas | Router macro calling child export macros |
| `%excel2sas` | excel2sas.sas | Read Excel workbook into SAS dataset(s) |

## 6. String & List Manipulation (8 macros)

| Macro | File | Purpose |
|-------|------|---------|
| `%seplist` | seplist.sas | Emit word list with configurable delimiter/prefix |
| `%stp_seplist` | stp_seplist.sas | Transform STP multi-select macro array to separated list |
| `%count_words` | count_words.sas | Count words in a delimited string |
| `%dedup_mstring` | dedup_mstring.sas | Remove duplicate words from a macro variable |
| `%dedup_string` | dedup_string.sas | Remove duplicate items from a DATA step string |
| `%squote` | squote.sas | Wrap argument in single quotes |
| `%splitvar` | splitvar.sas | Insert split characters into DATA step variable |
| `%justify` | justify.sas | Left/center/right justify text in a macro variable |

## 7. Date & Time Utilities (4 macros)

| Macro | File | Purpose |
|-------|------|---------|
| `%age` | age.sas | Calculate person's age in configurable units |
| `%date_impute` | date_impute.sas | Impute partial dates |
| `%sql_datetime` | sql_datetime.sas | Convert SAS datetime literal to database format |
| `%create_datetime_range` | create_datetime_range.sas | Create min/max datetime values for a range |
| `%time_interval` | time_interval.sas | Create metadata dataset of date/time intervals |

## 8. Flow Control & Orchestration (7 macros)

| Macro | File | Purpose |
|-------|------|---------|
| `%loop` | loop.sas | Wrapper to execute code over iterable items |
| `%loop_control` | loop_control.sas | Wrapper to execute code over a control table |
| `%RunAll` | RunAll.sas | Run SAS programs asynchronously |
| `%RunAll_ControlTable` | RunAll_ControlTable.sas | Run SAS programs asynchronously from a control table |
| `%batch_submit` | batch_submit.sas | Submit current DMS editor session in batch |
| `%stp_batch_submit` | stp_batch_submit.sas | Submit SAS batch program from a Stored Process |
| `%execute_macro` | execute_macro.sas | Execute a macro only if it exists |

## 9. Environment & System Utilities (10 macros)

| Macro | File | Purpose |
|-------|------|---------|
| `%lock` | lock.sas | Obtain or clear a dataset lock |
| `%kill` | kill.sas | Delete specified contents from a library |
| `%delete_file` | delete_file.sas | Delete an external file |
| `%create_directory` | create_directory.sas | Create a directory via dlcreatedir |
| `%dirlist` | dirlist.sas | Create dataset containing directory listing |
| `%execpath` | execpath.sas | Return full path or filename of executing program |
| `%optsave` | optsave.sas | Save current SAS options to a dataset |
| `%optload` | optload.sas | Load SAS options from a saved dataset |
| `%optval` | optval.sas | Return value of a SAS option |
| `%realloc_concat_libs` | realloc_concat_libs.sas | Reallocate concatenated libraries |

## 10. Notification & Logging (5 macros)

| Macro | File | Purpose |
|-------|------|---------|
| `%sendmail` | sendmail.sas | Send email notification via metadata dataset |
| `%logparse` | logparse.sas | Extract performance statistics from SAS log |
| `%log2pdf` | log2pdf.sas | Convert SAS log to PDF with syntax highlighting |
| `%dump_mvars` | dump_mvars.sas | Dump macro variables to the log |
| `%marker` | marker.sas | Process marker files for job flow control |

## 11. Reporting & Formatting (5 macros)

| Macro | File | Purpose |
|-------|------|---------|
| `%pagexofy` | pagexofy.sas | Add "Page X of Y" to output |
| `%align_decimals` | align_decimals.sas | Align decimal points in numeric display |
| `%max_decimals` | max_decimals.sas | Derive maximum decimal places in a variable |
| `%format_text` | format_text.sas | Format text with left/center/right alignment |
| `%fmtlist` | fmtlist.sas | Print contents of format catalogs |

## 12. Format & Catalog Utilities (2 macros)

| Macro | File | Purpose |
|-------|------|---------|
| `%fmtexist` | fmtexist.sas | Check if a format exists in the search path |
| `%get_permutations` | get_permutations.sas | Get all permutations of items |

## 13. Connectivity & Security (5 macros)

| Macro | File | Purpose |
|-------|------|---------|
| `%libname_sqlsvr` | libname_sqlsvr.sas | Allocate SQL Server library via ODBC |
| `%libname_attr_sqlsvr` | libname_attr_sqlsvr.sas | Retrieve SQL Server libname attributes |
| `%getpassword` | getpassword.sas | Get password from an external file |
| `%queryActiveDirectory` | queryActiveDirectory.sas | LDAP query against Active Directory |
| `%useridToEmail` | useridToEmail.sas | Resolve userid to email address |
| `%stp_session` | stp_session.sas | Wrap STP session functions for portability |

## 14. Measurement & Diagnostics (4 macros)

| Macro | File | Purpose |
|-------|------|---------|
| `%bench` | bench.sas | Measure elapsed time between successive calls |
| `%handle` | handle.sas | Print open file handles to the log |
| `%symget` | symget.sas | Get global macro variable hidden by local scope |
| `%reduce_pixel` | reduce_pixel.sas | Reduce a map based on pixel size |

## 15. Document Conversion (2 macros)

| Macro | File | Purpose |
|-------|------|---------|
| `%txt2pdf` | txt2pdf.sas | Convert text files to PDF documents |
| `%txt2rtf` | txt2rtf.sas | Convert text files to RTF documents |

## 16. Template (1 macro)

| Macro | File | Purpose |
|-------|------|---------|
| `%@TEMPLATE` | @TEMPLATE.sas | Macro boilerplate template |

---

### Summary by Category

| Category | Count |
|----------|-------|
| Parameter & Validation | 4 |
| Dataset Introspection & Metadata | 9 |
| Data Manipulation & Transformation | 7 |
| Hash Object Utilities | 3 |
| Export / Output | 12 |
| String & List Manipulation | 8 |
| Date & Time Utilities | 5 |
| Flow Control & Orchestration | 7 |
| Environment & System Utilities | 10 |
| Notification & Logging | 5 |
| Reporting & Formatting | 5 |
| Format & Catalog Utilities | 2 |
| Connectivity & Security | 6 |
| Measurement & Diagnostics | 4 |
| Document Conversion | 2 |
| Template | 1 |
| **Total** | **90** |

> Note: `@TEMPLATE.sas` is a boilerplate file, and `format_text.sas` has no header preamble. Two macros (`check_if_empty` and `empty`) overlap in functionality.
