# SAS estate census

Repository: `/home/ubuntu/repos/ts-sas-legacy-analytics`
Macro inventory: 92 entries across 93 Macro/ files; 128 total `%macro` statements were found (91 primary macro definitions plus support files).
Format inventory: banking_formats.sas=9, insurance_formats.sas=5
Sanity expectations vs observed: 92 macro entries / 92 observed; banking formats 10 / 9 observed; insurance formats 6 / 5 observed.

## Per-directory file table

| Directory group | Files | SAS files | Bytes |
| --- | --- | --- | --- |
| .gitignore | 1 | 0 | 86 |
| AMO | 12 | 0 | 8952809 |
| BatchJobs | 2 | 2 | 9821 |
| Config | 2 | 2 | 7990 |
| Data | 16 | 3 | 1791500 |
| EGProjects | 1 | 0 | 139728 |
| Formats | 2 | 2 | 5232 |
| Logs | 2 | 0 | 5583 |
| Macro | 93 | 92 | 882624 |
| Presentations | 3 | 0 | 2515251 |
| Programs/Banking | 4 | 4 | 32535 |
| Programs/Insurance | 2 | 2 | 14851 |
| Programs/Parent-Child-Index.sas | 1 | 1 | 6640 |
| Programs/Reports | 1 | 1 | 6402 |
| README.md | 1 | 0 | 6273 |
| UNLICENSE.txt | 1 | 0 | 1210 |

## Per-SAS-file table

| Path | Lines | # proc | Top procs | # data steps | Reads | Writes |
| --- | --- | --- | --- | --- | --- | --- |
| BatchJobs/run_daily_banking.sas | 161 | 3 | append (1), print (1), sql (1) | 1 | — | ARCHIVE.BATCH_HISTORY |
| BatchJobs/run_daily_insurance.sas | 133 | 3 | append (1), print (1), sql (1) | 1 | — | ARCHIVE.BATCH_HISTORY |
| Config/autoexec.sas | 118 | 0 | — | 0 | — | — |
| Config/autoexec_local.sas | 97 | 0 | — | 0 | — | — |
| Data/load_seed_data.sas | 164 | 1 | sql (1) | 9 | CURATED.DAILY_TRANSACTIONS, ORA_DW.CUST_ACCOUNTS, RAW_BANK.TXN_FEED_20240131 | ORA_DW.BUREAU_SCORES, ORA_DW.COLLATERAL, ORA_DW.CUST_ACCOUNTS, ORA_DW.CUST_DEMOGRAPHICS, ORA_DW.LOAN_DETAILS, ORA_DW.PAYMENT_HISTORY, RAW_BANK.DAILY_RATES, STG_BANK.ACCT_EXCEPTIONS |
| Data/local/sendmail.sas | 17 | 0 | — | 0 | — | — |
| Data/run_local_banking.sas | 53 | 1 | sql (1) | 0 | CURATED.DAILY_TRANSACTIONS, CURATED.RISK_SCORES, CURATED.TXN_ANOMALIES, REPORTS.DELINQUENCY_AGING, REPORTS.LLP_COVERAGE, REPORTS.MONTHLY_RWA, STG_BANK.ACCT_EXCEPTIONS, STG_BANK.CUST_ACCOUNTS_DAILY | — |
| Formats/banking_formats.sas | 131 | 1 | format (1) | 0 | — | — |
| Formats/insurance_formats.sas | 85 | 1 | format (1) | 0 | — | — |
| Macro/@TEMPLATE.sas | 118 | 0 | — | 0 | — | — |
| Macro/CreateTableOrView.sas | 1541 | 9 | sql (6), sort (2), datasets (1) | 9 | DICTIONARY.COLUMNS | — |
| Macro/IsNum.sas | 165 | 0 | — | 0 | — | — |
| Macro/IsNumD.sas | 165 | 0 | — | 0 | — | — |
| Macro/IsNumM.sas | 276 | 0 | — | 0 | — | — |
| Macro/RunAll.sas | 303 | 6 | format (1), optload (1), optsave (1), report (1), sort (1) | 4 | — | — |
| Macro/RunAll_ControlTable.sas | 160 | 0 | — | 1 | — | — |
| Macro/age.sas | 106 | 0 | — | 0 | — | — |
| Macro/align_decimals.sas | 442 | 0 | — | 0 | — | — |
| Macro/attrib.sas | 294 | 0 | — | 0 | — | — |
| Macro/batch_submit.sas | 179 | 0 | — | 0 | — | — |
| Macro/bench.sas | 284 | 1 | delete (1) | 4 | — | — |
| Macro/check_if_empty.sas | 154 | 0 | — | 0 | — | — |
| Macro/compare.sas | 522 | 6 | sort (2), compare (1), print (1), report (1), sql (1) | 6 | DICTIONARY.TABLES, WORKSPDE.CHECK, WORKSPDE.COMPARE_LIBRARIES | WORKSPDE.CHECK, WORKSPDE.COMPARE_LIBRARIES, WORKSPDE._BASE_, WORKSPDE._COMP_ |
| Macro/count_words.sas | 148 | 0 | — | 0 | — | — |
| Macro/create_datetime_range.sas | 172 | 0 | — | 1 | — | — |
| Macro/create_directory.sas | 134 | 0 | — | 0 | — | — |
| Macro/create_format.sas | 408 | 2 | format (1), sort (1) | 1 | _CRTFMT_._CNTLIN_ | — |
| Macro/date_impute.sas | 326 | 0 | — | 0 | — | — |
| Macro/dedup_mstring.sas | 186 | 0 | — | 0 | — | — |
| Macro/dedup_string.sas | 121 | 0 | — | 0 | — | — |
| Macro/delete_file.sas | 195 | 0 | — | 0 | — | — |
| Macro/dirlist.sas | 226 | 0 | — | 1 | — | — |
| Macro/dump_mvars.sas | 224 | 1 | sql (1) | 0 | DICTIONARY.MACROS | — |
| Macro/empty.sas | 154 | 0 | — | 0 | — | — |
| Macro/excel2sas.sas | 557 | 2 | import (1), sql (1) | 3 | DICTIONARY.TABLES | — |
| Macro/execpath.sas | 156 | 0 | — | 0 | — | — |
| Macro/execute_macro.sas | 145 | 0 | — | 0 | — | — |
| Macro/export.sas | 355 | 0 | — | 1 | — | — |
| Macro/export_csv.sas | 113 | 0 | — | 0 | — | — |
| Macro/export_dbms.sas | 520 | 1 | export (1) | 0 | — | — |
| Macro/export_dlm.sas | 614 | 0 | — | 1 | — | — |
| Macro/export_rldx.sas | 390 | 0 | — | 0 | — | — |
| Macro/export_saphari.sas | 336 | 2 | datasets (1), sql (1) | 3 | — | — |
| Macro/export_sas.sas | 363 | 2 | copy (1), datasets (1) | 0 | — | — |
| Macro/export_spss.sas | 99 | 0 | — | 0 | — | — |
| Macro/export_stata.sas | 101 | 0 | — | 0 | — | — |
| Macro/export_tab.sas | 115 | 0 | — | 0 | — | — |
| Macro/export_xlsx.sas | 101 | 0 | — | 0 | — | — |
| Macro/fmtexist.sas | 136 | 0 | — | 0 | — | — |
| Macro/fmtlist.sas | 299 | 5 | sql (4), format (1) | 0 | DICTIONARY.FORMATS | — |
| Macro/format_text.sas | 32 | 0 | — | 0 | — | — |
| Macro/get_data_attr.sas | 226 | 0 | — | 0 | — | — |
| Macro/get_dups.sas | 327 | 7 | eq (3), means (1), print (1), sort (1), sql (1) | 0 | — | WORKSPDE._SORTED_ |
| Macro/get_lib_attr.sas | 177 | 0 | — | 0 | — | — |
| Macro/get_parameters.sas | 446 | 1 | sql (1) | 1 | — | — |
| Macro/get_permutations.sas | 501 | 4 | datasets (1), print (1), sql (1), transpose (1) | 3 | — | — |
| Macro/getpassword.sas | 147 | 0 | — | 0 | — | — |
| Macro/guess_pk.sas | 915 | 9 | sql (3), datasets (2), append (1), freq (1), print (1) | 6 | DICTIONARY.COLUMNS | — |
| Macro/handle.sas | 451 | 1 | sql (1) | 4 | — | — |
| Macro/hash_define.sas | 499 | 0 | — | 0 | — | — |
| Macro/hash_lookup.sas | 310 | 0 | — | 0 | — | — |
| Macro/hash_split_dataset.sas | 161 | 3 | sql (2), contents (1) | 1 | — | — |
| Macro/justify.sas | 242 | 0 | — | 0 | — | — |
| Macro/kill.sas | 206 | 2 | datasets (1), sql (1) | 0 | DICTIONARY.LIBNAMES | — |
| Macro/libname_attr_sqlsvr.sas | 262 | 1 | sql (1) | 0 | SASHELP.VLIBNAM | — |
| Macro/libname_sqlsvr.sas | 204 | 0 | — | 0 | — | — |
| Macro/lock.sas | 352 | 0 | — | 2 | — | — |
| Macro/log2pdf.sas | 59 | 1 | report (1) | 1 | — | — |
| Macro/logparse.sas | 655 | 1 | datasets (1) | 2 | — | — |
| Macro/loop.sas | 248 | 0 | — | 0 | — | — |
| Macro/loop_control.sas | 230 | 0 | — | 0 | — | — |
| Macro/marker.sas | 184 | 0 | — | 0 | — | — |
| Macro/max_decimals.sas | 238 | 2 | contents (1), sql (1) | 3 | — | — |
| Macro/nobs.sas | 253 | 1 | sql (1) | 0 | — | — |
| Macro/optload.sas | 91 | 1 | optload (1) | 0 | — | — |
| Macro/optsave.sas | 87 | 1 | optsave (1) | 0 | — | — |
| Macro/optval.sas | 96 | 0 | — | 0 | — | — |
| Macro/pagexofy.sas | 471 | 0 | — | 3 | — | — |
| Macro/parmv.sas | 359 | 0 | — | 0 | — | — |
| Macro/queryActiveDirectory.sas | 480 | 0 | — | 1 | — | — |
| Macro/randlist.sas | 294 | 2 | sql (2) | 0 | — | — |
| Macro/realloc_concat_libs.sas | 100 | 2 | delete (1), sql (1) | 1 | DICTIONARY.LIBNAMES | — |
| Macro/reduce_pixel.sas | 211 | 3 | greduce (1), sort (1), summary (1) | 3 | — | — |
| Macro/sendmail.sas | 260 | 0 | — | 2 | — | — |
| Macro/seplist.sas | 200 | 0 | — | 0 | — | — |
| Macro/splitvar.sas | 221 | 0 | — | 0 | — | — |
| Macro/sql_datetime.sas | 200 | 0 | — | 0 | — | — |
| Macro/squote.sas | 124 | 0 | — | 0 | — | — |
| Macro/stp_batch_submit.sas | 350 | 1 | sql (1) | 4 | DICTIONARY.MACROS | SAVE.PARAMETERS |
| Macro/stp_seplist.sas | 209 | 0 | — | 0 | — | — |
| Macro/stp_session.sas | 54 | 0 | — | 0 | — | — |
| Macro/subset_data.sas | 208 | 0 | — | 1 | — | — |
| Macro/symget.sas | 148 | 0 | — | 0 | — | — |
| Macro/time_interval.sas | 197 | 1 | sql (1) | 1 | — | — |
| Macro/transpose.sas | 352 | 2 | sort (1), transpose (1) | 0 | — | — |
| Macro/txt2pdf.sas | 733 | 0 | — | 3 | — | — |
| Macro/txt2rtf.sas | 199 | 0 | — | 1 | — | — |
| Macro/useridToEmail.sas | 112 | 0 | — | 1 | — | — |
| Macro/varexist.sas | 142 | 0 | — | 0 | — | — |
| Macro/varlist.sas | 136 | 0 | — | 0 | — | — |
| Macro/varlist2.sas | 230 | 2 | contents (1), sql (1) | 0 | — | — |
| Programs/Banking/credit_risk_scoring.sas | 270 | 6 | append (2), sql (2), datasets (1), means (1) | 1 | ORA_DW.BUREAU_SCORES, ORA_DW.COLLATERAL, ORA_DW.PAYMENT_HISTORY, STG_BANK.CUST_ACCOUNTS_DAILY | CURATED.RISK_MIGRATION, CURATED.RISK_SCORES, REPORTS.RISK_SUMMARY |
| Programs/Banking/daily_transaction_processing.sas | 246 | 6 | sql (3), append (2), datasets (1) | 3 | CURATED.DAILY_TRANSACTIONS, STG_BANK.CUST_ACCOUNTS_DAILY | CURATED.DAILY_TRANSACTIONS, CURATED.RUNNING_BALANCES, CURATED.TXN_ANOMALIES |
| Programs/Banking/load_customer_accounts.sas | 216 | 4 | sql (2), datasets (1), means (1) | 1 | ORA_DW.CUST_ACCOUNTS, ORA_DW.CUST_DEMOGRAPHICS, STG_BANK.CUST_ACCOUNTS_DAILY | STG_BANK.ACCT_EXCEPTIONS, STG_BANK.CUST_ACCOUNTS_DAILY |
| Programs/Banking/monthly_regulatory_reporting.sas | 199 | 4 | sql (4) | 0 | ORA_DW.LOAN_DETAILS, REPORTS.DELINQUENCY_AGING, REPORTS.LLP_COVERAGE, REPORTS.MONTHLY_RWA, STG_BANK.CUST_ACCOUNTS_DAILY | REPORTS.CAPITAL_ADEQUACY, REPORTS.DELINQUENCY_AGING, REPORTS.LLP_COVERAGE, REPORTS.MONTHLY_RWA |
| Programs/Insurance/claims_processing.sas | 238 | 5 | append (3), datasets (1), sql (1) | 4 | TERA_DW.FRAUD_INDICATORS | STG_INS.CLAIMS_REGISTER, STG_INS.CLAIMS_REVIEW_QUEUE, STG_INS.FRAUD_ALERTS |
| Programs/Insurance/policy_valuation.sas | 206 | 5 | sql (3), datasets (1), means (1) | 2 | RAW_INS.CLAIMS, RAW_INS.POLICIES, RAW_INS.PREMIUMS, REPORTS.LOSS_RATIO_SUMMARY, STG_INS.POLICY_VALUATION | REPORTS.LOSS_RATIO_SUMMARY, STG_INS.POLICY_VALUATION |
| Programs/Parent-Child-Index.sas | 286 | 9 | sql (4), summary (3), contents (2) | 9 | — | — |
| Programs/Reports/customer_profitability.sas | 176 | 6 | sql (3), means (2), datasets (1) | 1 | CURATED.DAILY_TRANSACTIONS, CURATED.RISK_SCORES, REPORTS.CUSTOMER_PNL, REPORTS.SEGMENT_PROFITABILITY, STG_BANK.CUST_ACCOUNTS_DAILY | REPORTS.BRANCH_PROFITABILITY, REPORTS.CUSTOMER_PNL, REPORTS.SEGMENT_PROFITABILITY |

## Macro usage

| Macro | Definition | Lines | Calls | Call files |
| --- | --- | --- | --- | --- |
| parmv | Macro/parmv.sas:134 | 359 | 469 | Macro/@TEMPLATE.sas, Macro/CreateTableOrView.sas, Macro/IsNum.sas, Macro/IsNumD.sas, Macro/IsNumM.sas, Macro/age.sas, Macro/align_decimals.sas, Macro/attrib.sas, Macro/bench.sas, Macro/check_if_empty.sas, Macro/compare.sas, Macro/count_words.sas, Macro/create_datetime_range.sas, Macro/create_directory.sas, Macro/create_format.sas, Macro/dedup_mstring.sas, Macro/dedup_string.sas, Macro/delete_file.sas, Macro/dirlist.sas, Macro/dump_mvars.sas, Macro/empty.sas, Macro/excel2sas.sas, Macro/execpath.sas, Macro/export.sas, Macro/export_csv.sas, Macro/export_dbms.sas, Macro/export_dlm.sas, Macro/export_rldx.sas, Macro/export_saphari.sas, Macro/export_sas.sas, Macro/export_spss.sas, Macro/export_stata.sas, Macro/export_tab.sas, Macro/export_xlsx.sas, Macro/fmtexist.sas, Macro/fmtlist.sas, Macro/get_data_attr.sas, Macro/get_dups.sas, Macro/get_lib_attr.sas, Macro/get_parameters.sas, Macro/get_permutations.sas, Macro/getpassword.sas, Macro/guess_pk.sas, Macro/handle.sas, Macro/hash_define.sas, Macro/hash_lookup.sas, Macro/hash_split_dataset.sas, Macro/justify.sas, Macro/kill.sas, Macro/libname_attr_sqlsvr.sas, Macro/libname_sqlsvr.sas, Macro/lock.sas, Macro/loop.sas, Macro/loop_control.sas, Macro/marker.sas, Macro/max_decimals.sas, Macro/nobs.sas, Macro/optload.sas, Macro/optsave.sas, Macro/optval.sas, Macro/pagexofy.sas, Macro/queryActiveDirectory.sas, Macro/randlist.sas, Macro/reduce_pixel.sas, Macro/sendmail.sas, Macro/seplist.sas, Macro/splitvar.sas, Macro/sql_datetime.sas, Macro/stp_batch_submit.sas, Macro/stp_seplist.sas, Macro/subset_data.sas, Macro/symget.sas, Macro/time_interval.sas, Macro/transpose.sas, Macro/txt2rtf.sas, Macro/useridToEmail.sas, Macro/varexist.sas, Macro/varlist.sas, Macro/varlist2.sas, Programs/Banking/credit_risk_scoring.sas, Programs/Banking/daily_transaction_processing.sas, Programs/Banking/load_customer_accounts.sas, Programs/Banking/monthly_regulatory_reporting.sas, Programs/Insurance/claims_processing.sas, Programs/Insurance/policy_valuation.sas, Programs/Reports/customer_profitability.sas |
| seplist | Macro/seplist.sas:92 | 200 | 32 | Macro/CreateTableOrView.sas, Macro/create_directory.sas, Macro/dump_mvars.sas, Macro/excel2sas.sas, Macro/fmtlist.sas, Macro/get_dups.sas, Macro/get_parameters.sas, Macro/get_permutations.sas, Macro/guess_pk.sas, Macro/hash_define.sas, Macro/hash_split_dataset.sas, Macro/max_decimals.sas, Macro/sendmail.sas, Macro/stp_seplist.sas, Macro/symget.sas, Programs/Parent-Child-Index.sas |
| nobs | Macro/nobs.sas:139 | 253 | 22 | Macro/create_format.sas, Macro/export_saphari.sas, Macro/get_permutations.sas, Macro/guess_pk.sas, Macro/handle.sas, Macro/randlist.sas, Programs/Banking/credit_risk_scoring.sas, Programs/Banking/daily_transaction_processing.sas, Programs/Banking/load_customer_accounts.sas, Programs/Insurance/claims_processing.sas, Programs/Insurance/policy_valuation.sas, Programs/Reports/customer_profitability.sas |
| loop | Macro/loop.sas:212 | 248 | 13 | Macro/CreateTableOrView.sas, Macro/compare.sas, Macro/create_directory.sas, Macro/excel2sas.sas, Macro/export_saphari.sas, Macro/fmtlist.sas, Macro/guess_pk.sas, Macro/handle.sas, Macro/hash_define.sas, Macro/transpose.sas |
| lock | Macro/lock.sas:86 | 352 | 8 | Macro/stp_batch_submit.sas, Programs/Banking/credit_risk_scoring.sas, Programs/Banking/daily_transaction_processing.sas |
| varexist | Macro/varexist.sas:78 | 142 | 7 | Macro/CreateTableOrView.sas, Macro/compare.sas, Macro/randlist.sas, Macro/txt2pdf.sas |
| kill | Macro/kill.sas:117 | 206 | 6 | Macro/compare.sas, Macro/excel2sas.sas, Macro/hash_split_dataset.sas, Macro/transpose.sas |
| sendmail | Macro/sendmail.sas:134 | 260 | 6 | BatchJobs/run_daily_banking.sas, BatchJobs/run_daily_insurance.sas, Macro/handle.sas, Programs/Banking/load_customer_accounts.sas, Programs/Insurance/claims_processing.sas |
| export_xlsx | Macro/export_xlsx.sas:47 | 101 | 5 | Macro/export_rldx.sas, Programs/Banking/monthly_regulatory_reporting.sas, Programs/Reports/customer_profitability.sas |
| dump_mvars | Macro/dump_mvars.sas:128 | 224 | 3 | Macro/CreateTableOrView.sas, Macro/batch_submit.sas |
| export_dbms | Macro/export_dbms.sas:306 | 520 | 3 | Macro/export_spss.sas, Macro/export_stata.sas, Macro/export_xlsx.sas |
| export_dlm | Macro/export_dlm.sas:350 | 614 | 2 | Macro/export_csv.sas, Macro/export_tab.sas |
| get_permutations | Macro/get_permutations.sas:264 | 501 | 2 | Macro/guess_pk.sas |
| handle | Macro/handle.sas:148 | 451 | 2 | Macro/lock.sas |
| loop_control | Macro/loop_control.sas:172 | 230 | 2 | Macro/guess_pk.sas |
| splitvar | Macro/splitvar.sas:115 | 221 | 2 | Macro/CreateTableOrView.sas |
| count_words | Macro/count_words.sas:91 | 148 | 1 | Macro/CreateTableOrView.sas |
| create_format | Macro/create_format.sas:145 | 408 | 1 | Macro/export_saphari.sas |
| dedup_mstring | Macro/dedup_mstring.sas:131 | 186 | 1 | Macro/guess_pk.sas |
| export_csv | Macro/export_csv.sas:47 | 113 | 1 | Macro/export_rldx.sas |
| export_saphari | Macro/export_saphari.sas:138 | 336 | 1 | Macro/export_rldx.sas |
| export_sas | Macro/export_sas.sas:254 | 363 | 1 | Macro/export_rldx.sas |
| export_spss | Macro/export_spss.sas:47 | 99 | 1 | Macro/export_rldx.sas |
| export_stata | Macro/export_stata.sas:47 | 101 | 1 | Macro/export_rldx.sas |
| get_data_attr | Macro/get_data_attr.sas:72 | 226 | 1 | Macro/lock.sas |
| hash_define | Macro/hash_define.sas:323 | 499 | 1 | Programs/Parent-Child-Index.sas |
| hash_lookup | Macro/hash_lookup.sas:195 | 310 | 1 | Programs/Parent-Child-Index.sas |
| queryactivedirectory | Macro/queryActiveDirectory.sas:245 | 480 | 1 | Macro/useridToEmail.sas |
| runall | Macro/RunAll.sas:113 | 303 | 1 | Macro/RunAll_ControlTable.sas |
| subset_data | Macro/subset_data.sas:108 | 208 | 1 | Macro/excel2sas.sas |
| useridtoemail | Macro/useridToEmail.sas:60 | 112 | 1 | Macro/handle.sas |
| varlist | Macro/varlist.sas:87 | 136 | 1 | Macro/guess_pk.sas |
| (support file; no macro definition) | Macro/RunAll_ControlTable.sas:None | 160 | 0 | — |
| age | Macro/age.sas:62 | 106 | 0 | — |
| align_decimals | Macro/align_decimals.sas:294 | 442 | 0 | — |
| attrib | Macro/attrib.sas:157 | 294 | 0 | — |
| batch_submit | Macro/batch_submit.sas:98 | 179 | 0 | — |
| bench | Macro/bench.sas:112 | 284 | 0 | — |
| check_if_empty | Macro/check_if_empty.sas:108 | 154 | 0 | — |
| compare | Macro/compare.sas:200 | 522 | 0 | — |
| create_datetime_range | Macro/create_datetime_range.sas:119 | 172 | 0 | — |
| create_directory | Macro/create_directory.sas:81 | 134 | 0 | — |
| createtableorview | Macro/CreateTableOrView.sas:476 | 1541 | 0 | — |
| date_impute | Macro/date_impute.sas:209 | 326 | 0 | — |
| dedup_string | Macro/dedup_string.sas:70 | 121 | 0 | — |
| delete_file | Macro/delete_file.sas:114 | 195 | 0 | — |
| dirlist | Macro/dirlist.sas:131 | 226 | 0 | — |
| empty | Macro/empty.sas:108 | 154 | 0 | — |
| excel2sas | Macro/excel2sas.sas:141 | 557 | 0 | — |
| execpath | Macro/execpath.sas:87 | 156 | 0 | — |
| execute_macro | Macro/execute_macro.sas:53 | 145 | 0 | — |
| export | Macro/export.sas:205 | 355 | 0 | — |
| export_rldx | Macro/export_rldx.sas:171 | 390 | 0 | — |
| export_tab | Macro/export_tab.sas:47 | 115 | 0 | — |
| fmtexist | Macro/fmtexist.sas:63 | 136 | 0 | — |
| fmtlist | Macro/fmtlist.sas:139 | 299 | 0 | — |
| format_text | Macro/format_text.sas:1 | 32 | 0 | — |
| get_dups | Macro/get_dups.sas:196 | 327 | 0 | — |
| get_lib_attr | Macro/get_lib_attr.sas:105 | 177 | 0 | — |
| get_parameters | Macro/get_parameters.sas:264 | 446 | 0 | — |
| getpassword | Macro/getpassword.sas:93 | 147 | 0 | — |
| guess_pk | Macro/guess_pk.sas:514 | 915 | 0 | — |
| hash_split_dataset | Macro/hash_split_dataset.sas:87 | 161 | 0 | — |
| isnum | Macro/IsNum.sas:127 | 165 | 0 | — |
| isnumd | Macro/IsNumD.sas:127 | 165 | 0 | — |
| isnumm | Macro/IsNumM.sas:178 | 276 | 0 | — |
| justify | Macro/justify.sas:169 | 242 | 0 | — |
| libname_attr_sqlsvr | Macro/libname_attr_sqlsvr.sas:158 | 262 | 0 | — |
| libname_sqlsvr | Macro/libname_sqlsvr.sas:135 | 204 | 0 | — |
| log2pdf | Macro/log2pdf.sas:22 | 59 | 0 | — |
| logparse | Macro/logparse.sas:10 | 655 | 0 | — |
| marker | Macro/marker.sas:109 | 184 | 0 | — |
| max_decimals | Macro/max_decimals.sas:100 | 238 | 0 | — |
| optload | Macro/optload.sas:62 | 91 | 0 | — |
| optsave | Macro/optsave.sas:62 | 87 | 0 | — |
| optval | Macro/optval.sas:62 | 96 | 0 | — |
| pagexofy | Macro/pagexofy.sas:234 | 471 | 0 | — |
| randlist | Macro/randlist.sas:130 | 294 | 0 | — |
| realloc_concat_libs | Macro/realloc_concat_libs.sas:48 | 100 | 0 | — |
| reduce_pixel | Macro/reduce_pixel.sas:93 | 211 | 0 | — |
| sql_datetime | Macro/sql_datetime.sas:155 | 200 | 0 | — |
| squote | Macro/squote.sas:114 | 124 | 0 | — |
| stp_batch_submit | Macro/stp_batch_submit.sas:141 | 350 | 0 | — |
| stp_seplist | Macro/stp_seplist.sas:138 | 209 | 0 | — |
| stp_session | Macro/stp_session.sas:25 | 54 | 0 | — |
| symget | Macro/symget.sas:75 | 148 | 0 | — |
| template | Macro/@TEMPLATE.sas:86 | 118 | 0 | — |
| time_interval | Macro/time_interval.sas:43 | 197 | 0 | — |
| transpose | Macro/transpose.sas:125 | 352 | 0 | — |
| txt2pdf | Macro/txt2pdf.sas:69 | 733 | 0 | — |
| txt2rtf | Macro/txt2rtf.sas:1 | 199 | 0 | — |
| varlist2 | Macro/varlist2.sas:157 | 230 | 0 | — |

## Format list

| File | Format | Line |
| --- | --- | --- |
| Formats/banking_formats.sas | ACCTTYPE | 15 |
| Formats/banking_formats.sas | ACCTSTAT | 31 |
| Formats/banking_formats.sas | RISKRATE | 44 |
| Formats/banking_formats.sas | TXNCAT | 56 |
| Formats/banking_formats.sas | DELQBKT | 71 |
| Formats/banking_formats.sas | BALRANGE | 82 |
| Formats/banking_formats.sas | REGION | 94 |
| Formats/banking_formats.sas | CUSTSEG | 106 |
| Formats/banking_formats.sas | LNPURP | 117 |
| Formats/insurance_formats.sas | POLTYPE | 14 |
| Formats/insurance_formats.sas | CLMSTAT | 32 |
| Formats/insurance_formats.sas | RISKCAT | 49 |
| Formats/insurance_formats.sas | COVTYPE | 59 |
| Formats/insurance_formats.sas | LOSSRANGE | 73 |

## Batch run_step order

### BatchJobs/run_daily_banking.sas

| Order | Step | Step name | Program | Line |
| --- | --- | --- | --- | --- |
| 1 | 1 | Load Customer Accounts | /opt/sas/custom/programs/Banking/load_customer_accounts.sas | 121 |
| 2 | 2 | Daily Transaction Processing | /opt/sas/custom/programs/Banking/daily_transaction_processing.sas | 124 |
| 3 | 3 | Credit Risk Scoring | /opt/sas/custom/programs/Banking/credit_risk_scoring.sas | 127 |
| 4 | 4 | Monthly Regulatory Reporting | /opt/sas/custom/programs/Banking/monthly_regulatory_reporting.sas | 130 |

### BatchJobs/run_daily_insurance.sas

| Order | Step | Step name | Program | Line |
| --- | --- | --- | --- | --- |
| 1 | 1 | Claims Processing | /opt/sas/custom/programs/Insurance/claims_processing.sas | 109 |
| 2 | 2 | Policy Valuation | /opt/sas/custom/programs/Insurance/policy_valuation.sas | 112 |

## Libnames

| File | Libref | Engine | Path | Line |
| --- | --- | --- | --- | --- |
| Config/autoexec.sas | RAW | BASE | /data/sas/raw | 34 |
| Config/autoexec.sas | RAW_BANK | BASE | /data/sas/raw/banking | 35 |
| Config/autoexec.sas | RAW_INS | BASE | /data/sas/raw/insurance | 36 |
| Config/autoexec.sas | STAGING | BASE | /data/sas/staging | 41 |
| Config/autoexec.sas | STG_BANK | BASE | /data/sas/staging/banking | 42 |
| Config/autoexec.sas | STG_INS | BASE | /data/sas/staging/insurance | 43 |
| Config/autoexec.sas | CURATED | BASE | /data/sas/curated | 48 |
| Config/autoexec.sas | REPORTS | BASE | /data/sas/reports | 49 |
| Config/autoexec.sas | ARCHIVE | BASE | /data/sas/archive | 50 |
| Config/autoexec.sas | BANKING | BASE | /data/sas/formats/banking | 55 |
| Config/autoexec.sas | INSURANCE | BASE | /data/sas/formats/insurance | 56 |
| Config/autoexec.sas | COMMON | BASE | /data/sas/formats/common | 57 |
| Config/autoexec.sas | ORA_DW | ORACLE | FINPROD | 62 |
| Config/autoexec.sas | TERA_DW | TERADATA | tdprod.internal.corp | 72 |
| Config/autoexec_local.sas | RAW | BASE | &DATA_ROOT/raw | 43 |
| Config/autoexec_local.sas | RAW_BANK | BASE | &DATA_ROOT/raw/banking | 44 |
| Config/autoexec_local.sas | RAW_INS | BASE | &DATA_ROOT/raw/insurance | 45 |
| Config/autoexec_local.sas | STAGING | BASE | &DATA_ROOT/staging | 47 |
| Config/autoexec_local.sas | STG_BANK | BASE | &DATA_ROOT/staging/banking | 48 |
| Config/autoexec_local.sas | STG_INS | BASE | &DATA_ROOT/staging/insurance | 49 |
| Config/autoexec_local.sas | CURATED | BASE | &DATA_ROOT/curated | 51 |
| Config/autoexec_local.sas | REPORTS | BASE | &DATA_ROOT/reports | 52 |
| Config/autoexec_local.sas | ARCHIVE | BASE | &DATA_ROOT/archive | 53 |
| Config/autoexec_local.sas | BANKING | BASE | &DATA_ROOT/formats/banking | 55 |
| Config/autoexec_local.sas | INSURANCE | BASE | &DATA_ROOT/formats/insurance | 56 |
| Config/autoexec_local.sas | COMMON | BASE | &DATA_ROOT/formats/common | 57 |
| Config/autoexec_local.sas | ORA_DW | BASE | &DATA_ROOT/oracle_dw | 61 |
| Config/autoexec_local.sas | TERA_DW | BASE | &DATA_ROOT/teradata_dw | 62 |

## Autoexec `%let` variables

| File | Variable | Line |
| --- | --- | --- |
| Config/autoexec.sas | ENVIRONMENT | 84 |
| Config/autoexec.sas | BASE_PATH | 85 |
| Config/autoexec.sas | LOG_PATH | 86 |
| Config/autoexec.sas | REPORT_PATH | 87 |
| Config/autoexec.sas | ARCHIVE_PATH | 88 |
| Config/autoexec.sas | CURR_DT | 89 |
| Config/autoexec.sas | CURR_YM | 90 |
| Config/autoexec.sas | PREV_YM | 91 |
| Config/autoexec.sas | FY_START | 92 |
| Config/autoexec.sas | EMAIL_DL | 95 |
| Config/autoexec.sas | EMAIL_ONCALL | 96 |
| Config/autoexec.sas | MAX_OBS_WARN | 99 |
| Config/autoexec.sas | ABORT_ON_ERR | 100 |
| Config/autoexec_local.sas | REPO_ROOT | 16 |
| Config/autoexec_local.sas | REPO_ROOT | 17 |
| Config/autoexec_local.sas | DATA_ROOT | 19 |
| Config/autoexec_local.sas | DATA_ROOT | 20 |
| Config/autoexec_local.sas | ENVIRONMENT | 69 |
| Config/autoexec_local.sas | BASE_PATH | 70 |
| Config/autoexec_local.sas | LOG_PATH | 71 |
| Config/autoexec_local.sas | REPORT_PATH | 72 |
| Config/autoexec_local.sas | ARCHIVE_PATH | 73 |
| Config/autoexec_local.sas | CURR_DT | 74 |
| Config/autoexec_local.sas | CURR_YM | 75 |
| Config/autoexec_local.sas | PREV_YM | 76 |
| Config/autoexec_local.sas | FY_START | 77 |
| Config/autoexec_local.sas | EMAIL_DL | 79 |
| Config/autoexec_local.sas | EMAIL_ONCALL | 80 |
| Config/autoexec_local.sas | MAX_OBS_WARN | 82 |
| Config/autoexec_local.sas | ABORT_ON_ERR | 83 |

## Step-3 cross-reference table

| Target | Referenced | Cites |
| --- | --- | --- |
| AMO/SNUG_2013Q1_sbass/2013Q1_Scott Bass_AMO.pptx | no | — |
| AMO/SNUG_2013Q1_sbass/Book1.xlsm | no | — |
| AMO/SNUG_2013Q1_sbass/Book2.xlsm | no | — |
| AMO/SNUG_2013Q1_sbass/Book3.xlsm | no | — |
| AMO/SNUG_2013Q1_sbass/Book4.xlsm | no | — |
| AMO/SNUG_2013Q1_sbass/Book5.xlsm | no | — |
| AMO/SNUG_2013Q1_sbass/Book6.xlsm | no | — |
| AMO/SNUG_2013Q1_sbass/Book7.xlsm | no | — |
| AMO/SNUG_2013Q1_sbass/Book8.xlsm | no | — |
| AMO/SNUG_2013Q1_sbass/Book9.xlsm | no | — |
| AMO/SNUG_2013Q1_sbass/README.rtf | yes | Macro/logparse.sas:6 |
| AMO/SNUG_2013Q1_sbass/SNUG-2013Q1-sbass.spk | no | — |
| Data/bootstrap_local_env.sh | yes | Config/autoexec_local.sas:41 |
| Data/generate_seed_data.py | no | — |
| Data/load_seed_data.sas | yes | Config/autoexec_local.sas:60 |
| Data/local/sendmail.sas | yes | BatchJobs/run_daily_banking.sas:106, BatchJobs/run_daily_banking.sas:146, BatchJobs/run_daily_insurance.sas:96, Macro/handle.sas:436, Macro/sendmail.sas:134, Macro/sendmail.sas:2, Macro/sendmail.sas:57, Macro/sendmail.sas:85, Macro/sendmail.sas:90, Programs/Banking/load_customer_accounts.sas:174, Programs/Banking/load_customer_accounts.sas:175, Programs/Insurance/claims_processing.sas:16, Programs/Insurance/claims_processing.sas:209 |
| Data/run_local_banking.sas | no | — |
| Data/validate_seed_data.py | no | — |
| EGProjects/V6.1/SCD2 Processing - Template.egp | no | — |
| Logs/daily_transaction_processing_20240115.log | no | — |
| Logs/load_customer_accounts_20240115.log | no | — |
| Presentations/SNUG/SNUG Q4 2016.egp | no | — |
| Presentations/SNUG/SNUG Tips and Tricks From The Committee - Q4 2016-Bonus Tips.docx | no | — |
| Presentations/SNUG/SNUG Tips and Tricks From The Committee - Q4 2016.docx | no | — |
| Programs/Parent-Child-Index.sas | no | — |

## Unused macros

Macros with zero calls from `Programs/`, `BatchJobs/`, and `Config/`; the final column identifies calls from other macro files.

| Macro | Definition | Called by other macros |
| --- | --- | --- |
| loop | Macro/loop.sas | yes |
| varexist | Macro/varexist.sas | yes |
| kill | Macro/kill.sas | yes |
| dump_mvars | Macro/dump_mvars.sas | yes |
| export_dbms | Macro/export_dbms.sas | yes |
| export_dlm | Macro/export_dlm.sas | yes |
| get_permutations | Macro/get_permutations.sas | yes |
| handle | Macro/handle.sas | yes |
| loop_control | Macro/loop_control.sas | yes |
| splitvar | Macro/splitvar.sas | yes |
| count_words | Macro/count_words.sas | yes |
| create_format | Macro/create_format.sas | yes |
| dedup_mstring | Macro/dedup_mstring.sas | yes |
| export_csv | Macro/export_csv.sas | yes |
| export_saphari | Macro/export_saphari.sas | yes |
| export_sas | Macro/export_sas.sas | yes |
| export_spss | Macro/export_spss.sas | yes |
| export_stata | Macro/export_stata.sas | yes |
| get_data_attr | Macro/get_data_attr.sas | yes |
| queryactivedirectory | Macro/queryActiveDirectory.sas | yes |
| runall | Macro/RunAll.sas | yes |
| subset_data | Macro/subset_data.sas | yes |
| useridtoemail | Macro/useridToEmail.sas | yes |
| varlist | Macro/varlist.sas | yes |
| age | Macro/age.sas | no |
| align_decimals | Macro/align_decimals.sas | no |
| attrib | Macro/attrib.sas | no |
| batch_submit | Macro/batch_submit.sas | no |
| bench | Macro/bench.sas | no |
| check_if_empty | Macro/check_if_empty.sas | no |
| compare | Macro/compare.sas | no |
| create_datetime_range | Macro/create_datetime_range.sas | no |
| create_directory | Macro/create_directory.sas | no |
| createtableorview | Macro/CreateTableOrView.sas | no |
| date_impute | Macro/date_impute.sas | no |
| dedup_string | Macro/dedup_string.sas | no |
| delete_file | Macro/delete_file.sas | no |
| dirlist | Macro/dirlist.sas | no |
| empty | Macro/empty.sas | no |
| excel2sas | Macro/excel2sas.sas | no |
| execpath | Macro/execpath.sas | no |
| execute_macro | Macro/execute_macro.sas | no |
| export | Macro/export.sas | no |
| export_rldx | Macro/export_rldx.sas | no |
| export_tab | Macro/export_tab.sas | no |
| fmtexist | Macro/fmtexist.sas | no |
| fmtlist | Macro/fmtlist.sas | no |
| format_text | Macro/format_text.sas | no |
| get_dups | Macro/get_dups.sas | no |
| get_lib_attr | Macro/get_lib_attr.sas | no |
| get_parameters | Macro/get_parameters.sas | no |
| getpassword | Macro/getpassword.sas | no |
| guess_pk | Macro/guess_pk.sas | no |
| hash_split_dataset | Macro/hash_split_dataset.sas | no |
| isnum | Macro/IsNum.sas | no |
| isnumd | Macro/IsNumD.sas | no |
| isnumm | Macro/IsNumM.sas | no |
| justify | Macro/justify.sas | no |
| libname_attr_sqlsvr | Macro/libname_attr_sqlsvr.sas | no |
| libname_sqlsvr | Macro/libname_sqlsvr.sas | no |
| log2pdf | Macro/log2pdf.sas | no |
| logparse | Macro/logparse.sas | no |
| marker | Macro/marker.sas | no |
| max_decimals | Macro/max_decimals.sas | no |
| optload | Macro/optload.sas | no |
| optsave | Macro/optsave.sas | no |
| optval | Macro/optval.sas | no |
| pagexofy | Macro/pagexofy.sas | no |
| randlist | Macro/randlist.sas | no |
| realloc_concat_libs | Macro/realloc_concat_libs.sas | no |
| reduce_pixel | Macro/reduce_pixel.sas | no |
| sql_datetime | Macro/sql_datetime.sas | no |
| squote | Macro/squote.sas | no |
| stp_batch_submit | Macro/stp_batch_submit.sas | no |
| stp_seplist | Macro/stp_seplist.sas | no |
| stp_session | Macro/stp_session.sas | no |
| symget | Macro/symget.sas | no |
| template | Macro/@TEMPLATE.sas | no |
| time_interval | Macro/time_interval.sas | no |
| transpose | Macro/transpose.sas | no |
| txt2pdf | Macro/txt2pdf.sas | no |
| txt2rtf | Macro/txt2rtf.sas | no |
| varlist2 | Macro/varlist2.sas | no |

## Graphviz check

- Result: `already installed`
- `which dot`: `/usr/bin/dot`
