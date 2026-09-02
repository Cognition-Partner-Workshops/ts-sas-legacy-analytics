# Dependency Register

| ID | Class | Item | Evidence | Owner | Status | Blocks |
|---|---|---|---|---|---|---|
| D1-001 | D1 | In-scope table→table lineage | `[PROPOSED]` Populated by inventory phase from `%include`, `libname`, `set`/`merge`/`from`/`out=` and orchestrator order. | Devin | OPEN | All units |
| D2-001 | D2 | Shared macro library | `[FACT]` 92 macros in `Macro/` (93 files including template/support file); most-used calls across `Programs/` and `BatchJobs/`: `%nobs` 15, `%parmv` 10, `%lock` 6, `%sendmail` 5, `%export_xlsx` 4, `%run_step` 6. Examples: `Programs/Banking/load_customer_accounts.sas:19-20,71,162,175,186`; `BatchJobs/run_daily_banking.sas:121-130`. | Devin | OPEN | Wave 0; all units |
| D2-002 | D2 | Format catalogs | `[FACT]` `Formats/banking_formats.sas` has 10 `value` statements; `Formats/insurance_formats.sas` has 6 (`banking_formats.sas:15-117`; `insurance_formats.sas:14-73`). | Devin | OPEN | Wave 0; banking and insurance |
| D2-003 | D2 | Autoexec variables and librefs | `[FACT]` `Config/autoexec.sas:34-57,62-72,84-100` defines libraries and macro variables including `CURR_DT`; `Config/autoexec_local.sas:43-88` supplies local equivalents. | Devin | OPEN | Wave 0; all units |
| D3-001 | D3 | `ORA_DW.BUREAU_SCORES` | `[FACT]` Read by `credit_risk_scoring` at `Programs/Banking/credit_risk_scoring.sas:7,74,76`; seed present: `Data/csv/oracle_dw/BUREAU_SCORES.csv`. | Devin | RESOLVED (seeded) | credit_risk_scoring |
| D3-002 | D3 | `ORA_DW.PAYMENT_HISTORY` | `[FACT]` Read by `credit_risk_scoring` at `Programs/Banking/credit_risk_scoring.sas:8,79`; seed present: `Data/csv/oracle_dw/PAYMENT_HISTORY.csv`. | Devin | RESOLVED (seeded) | credit_risk_scoring |
| D3-003 | D3 | `ORA_DW.COLLATERAL` | `[FACT]` Read by `credit_risk_scoring` and `monthly_regulatory_reporting` at `Programs/Banking/credit_risk_scoring.sas:8,81` and `monthly_regulatory_reporting.sas:10,92`; seed present: `Data/csv/oracle_dw/COLLATERAL.csv`. | Devin | RESOLVED (seeded) | credit_risk_scoring; monthly_regulatory_reporting |
| D3-004 | D3 | `ORA_DW.CUST_ACCOUNTS` | `[FACT]` Read by `load_customer_accounts` at `Programs/Banking/load_customer_accounts.sas:6,59`; seed present: `Data/csv/oracle_dw/CUST_ACCOUNTS.csv`. | Devin | RESOLVED (seeded) | load_customer_accounts |
| D3-005 | D3 | `ORA_DW.CUST_DEMOGRAPHICS` | `[FACT]` Read by `load_customer_accounts` at `Programs/Banking/load_customer_accounts.sas:6,60`; seed present: `Data/csv/oracle_dw/CUST_DEMOGRAPHICS.csv`. | Devin | RESOLVED (seeded) | load_customer_accounts |
| D3-006 | D3 | `ORA_DW.LOAN_DETAILS` | `[FACT]` Read by `monthly_regulatory_reporting` at `Programs/Banking/monthly_regulatory_reporting.sas:10,61,92,135`; seed present: `Data/csv/oracle_dw/LOAN_DETAILS.csv`. | Devin | RESOLVED (seeded) | monthly_regulatory_reporting |
| D3-007 | D3 | `ORA_DW.COST_OF_FUNDS` | `[FACT]` Read by `customer_profitability` at `Programs/Reports/customer_profitability.sas:8`; no seed CSV under `Data/csv/`; specifically called out as absent in `03_recon_tolerances.md` §"Units convertible but NOT reconcilable". | Customer | OPEN | customer_profitability |
| D3-008 | D3 | `RAW_BANK.DAILY_RATES` | `[FACT]` Read by `load_customer_accounts` at `Programs/Banking/load_customer_accounts.sas:7`; seed present: `Data/csv/raw_bank/DAILY_RATES.csv`. | Devin | RESOLVED (seeded) | load_customer_accounts |
| D3-009 | D3 | `RAW_BANK.TXN_FEED_yyyymmdd` | `[FACT]` Read by `daily_transaction_processing` at `Programs/Banking/daily_transaction_processing.sas:6,30,36-48`; seed present: `Data/csv/raw_bank/TXN_FEED_20240131.csv`. | Devin | RESOLVED (seeded) | daily_transaction_processing |
| D3-010 | D3 | `RAW_INS.CLAIMS_FEED_yyyymmdd` | `[FACT]` Read by `claims_processing` at `Programs/Insurance/claims_processing.sas:6,33-41`; no seed CSV under `Data/csv/`. | Customer | OPEN | claims_processing |
| D3-011 | D3 | `RAW_INS.POLICIES` | `[FACT]` Read by `claims_processing` and `policy_valuation` at `Programs/Insurance/claims_processing.sas:6,47` and `policy_valuation.sas:6,62`; no seed CSV under `Data/csv/`. | Customer | OPEN | claims_processing; policy_valuation |
| D3-012 | D3 | `RAW_INS.CLAIMS` | `[FACT]` Read by `policy_valuation` at `Programs/Insurance/policy_valuation.sas:6,92`; no seed CSV under `Data/csv/`. | Customer | OPEN | policy_valuation |
| D3-013 | D3 | `RAW_INS.PREMIUMS` | `[FACT]` Read by `policy_valuation` at `Programs/Insurance/policy_valuation.sas:6,113`; no seed CSV under `Data/csv/`. | Customer | OPEN | policy_valuation |
| D3-014 | D3 | `TERA_DW.FRAUD_INDICATORS` | `[FACT]` Read by `claims_processing` at `Programs/Insurance/claims_processing.sas:7,105`; no seed CSV under `Data/csv/`. | Customer | OPEN | claims_processing |
| D3-015 | D3 | `TERA_DW.ACTUARIAL_TABLES` | `[FACT]` Read by `policy_valuation` at `Programs/Insurance/policy_valuation.sas:7`; no seed CSV under `Data/csv/`. | Customer | OPEN | policy_valuation |
| D4-001 | D4 | Report tables | `[FACT]` `REPORTS.*` outputs are declared/read in `Programs/Banking/credit_risk_scoring.sas:9,249`, `monthly_regulatory_reporting.sas:11-12,41,73,115,170`, `Programs/Insurance/policy_valuation.sas:8-9,173-185`, and `Programs/Reports/customer_profitability.sas:9-10,100,143,153`. | Customer | OPEN | customer_profitability; monthly_regulatory_reporting; policy_valuation; credit_risk_scoring |
| D4-002 | D4 | Excel workbook consumers | `[FACT]` `%export_xlsx` is used by `monthly_regulatory_reporting` at `Programs/Banking/monthly_regulatory_reporting.sas:146-159` and `customer_profitability` at `Programs/Reports/customer_profitability.sas:159-160`; downstream openpyxl task required. | Customer | OPEN | monthly_regulatory_reporting; customer_profitability |
| D4-003 | D4 | Email consumers | `[FACT]` `%sendmail` is used by `load_customer_accounts.sas:175`, `claims_processing.sas:209`, and banking/insurance orchestrators at `BatchJobs/run_daily_banking.sas:106,146` and `run_daily_insurance.sas:96`. | Customer | OPEN | load_customer_accounts; claims_processing; both orchestrators |
| D5-001 | D5 | Control-M definitions | `[FACT]` No scheduler export exists in the repository; Control-M is named in `BatchJobs/run_daily_banking.sas:6` and `run_daily_insurance.sas:4`. | Customer | OPEN | Both orchestrators |
| D5-002 | D5 | Banking order | `[FACT]` `run_daily_banking` executes steps 1→4 at `BatchJobs/run_daily_banking.sas:121-130`: load accounts, daily transactions, credit risk scoring, monthly regulatory reporting. | Customer | OPEN | banking wave |
| D5-003 | D5 | Insurance order | `[FACT]` `run_daily_insurance` executes steps 1→2 at `BatchJobs/run_daily_insurance.sas:109-112`: claims processing, policy valuation. | Customer | OPEN | insurance wave |
| D5-004 | D5 | Coexistence recon schedule | `[FACT]` Job `sas_legacy_recon` (id `1058116656072070`, bundle target `dev`), 5 independent serverless tasks `recon_U1`..`recon_U5`, schedule `0 15 6 * * ?` UTC `UNPAUSED`, `max_concurrent_runs: 1`; reads silver/gold, writes only `sas_recon.run_log`. Alerting: WEBHOOK: NOT WIRED — GAP for STOP E (creating a notification destination needs workspace-admin; `notification-destinations list` empty on 2026-09-02); remediation carried by Devin automation "sas_legacy P1 coexistence: recon ledger + remediation" (automation id: TBD, filled by parent). Ledger: `.migration/09_parallel_run_ledger.md`. `sas_legacy_run_daily_banking` stays PAUSED (Control-M remains trigger authority). | Devin (job) / Customer (webhook destination) | OPEN (webhook GAP) | STOP E |
| D6-001 | D6 | BI tools | `[DISCOVERED]` N/A: no Power BI, Tableau, Qlik, or other BI-tool references found in the in-scope SAS directories. | Customer | ACCEPTED | None |
| D7-001 | D7 | External APIs | `[DISCOVERED]` N/A: no HTTP/REST/API integration found in the in-scope pipeline and orchestrator directories. | Customer | ACCEPTED | None |
| D8-001 | D8 | Externally consumed views | `[DISCOVERED]` N/A as a dependency class: view references found are local WORK/macro implementation helpers (for example `Macro/guess_pk.sas:635,653`), not persistent pipeline outputs. | Customer | ACCEPTED | None |
| D9-001 | D9 | ML report consumer | `[FACT]` `customer_profitability` reads `CURATED.RISK_SCORES` at `Programs/Reports/customer_profitability.sas:8,90-91`. | Customer | OPEN | customer_profitability |
| D9-002 | D9 | Risk-rating consumers | `[FACT]` `monthly_regulatory_reporting` reads risk-rating fields through its account/loan population; risk-rating production and migration fields are explicit in `Programs/Banking/credit_risk_scoring.sas:183-212` and are consumed downstream in banking sources such as `daily_transaction_processing.sas:124`. | Customer | OPEN | monthly_regulatory_reporting; daily_transaction_processing |
| D10-001 | D10 | No SAS runtime | `[DISCOVERED]` `which sas sas94` is empty; `Data/README.md:47-56` requires Base SAS/bootstrap execution. | Customer | OPEN | All recon work |
| D10-002 | D10 | No Oracle/Teradata connectivity | `[DISCOVERED]` No connectivity or credentials are available for `ORA_DW`/`TERA_DW`; source declarations are in `Config/autoexec.sas:62-72`. | Customer | OPEN | All source-dependent units |
| D10-003 | D10 | Insurance seed data absent | `[FACT]` `Data/README.md:100-101` states insurance has no seed data. | Customer | OPEN | claims_processing; policy_valuation |
| D10-004 | D10 | `ORA_DW.COST_OF_FUNDS` seed absent | `[FACT]` Explicitly listed in `03_recon_tolerances.md` §"Units convertible but NOT reconcilable"; source use is `Programs/Reports/customer_profitability.sas:8`. | Customer | OPEN | customer_profitability |
| D10-005 | D10 | Control-M export absent | `[FACT]` No export exists in repo; Control-M schedule annotations are present at `BatchJobs/run_daily_banking.sas:6` and `run_daily_insurance.sas:4`. | Customer | OPEN | Both orchestrators |
| D10-006 | D10 | Catalog `sas_legacy` not provisioned | `[DISCOVERED]` `databricks catalogs get sas_legacy` reported that the catalog does not exist; Devin can self-create it, gated on STOP A. | Devin | OPEN | Wave 0 |
| D10-007 | D10 | Legacy output baseline absent | `[FACT]` R-0 in `03_recon_tolerances.md` §R-0 requires customer SAS outputs or an independent reference implementation. | Customer | OPEN | All RECON phases |
| D2-INV-001 | D2 | Shared-macro closure | `[FACT]` Transitive `%call` closure from the 7 programs + 2 orchestrators reaches 12 of 92 `Macro/*.sas` files (`parmv nobs lock sendmail export_xlsx export_dbms handle get_data_attr loop seplist useridToEmail queryActiveDirectory`); the other 80 + `handle_email.txt` have zero reachable calls (`.migration/tools/census.json`). Proposal: port only the closure; the rest is PROPOSED-unused. | Customer | UNDECIDED | Wave 0 scope |
| D3-INV-001 | D3 | Header-only inputs | `[FACT]` `monthly_regulatory_reporting.sas:9-10` declares `CURATED.DAILY_TRANSACTIONS` and `ORA_DW.COLLATERAL` as inputs; the code reads only `STG_BANK.CUST_ACCOUNTS_DAILY` and `ORA_DW.LOAN_DETAILS` (lines 60-61, 91-92, 134-135). `customer_profitability.sas:8` declares `ORA_DW.COST_OF_FUNDS`; no code read exists. D10-004 may be closable as not-required. | Customer | UNDECIDED | monthly_regulatory_reporting; customer_profitability |
| D6-INV-001 | D6 | `customer_profitability` trigger | `[FACT]` Not invoked by either orchestrator and not referenced by any scanned file; trigger unknown pending the Control-M export (D10-005). | Customer | UNDECIDED | customer_profitability |
| D9-INV-001 | D9 | `ARCHIVE.BATCH_HISTORY` shared write target | `[FACT]` Appended by both `run_daily_banking.sas` and `run_daily_insurance.sas`; must be registered once in `05_progress.md` before either orchestrator loads it. | Devin | UNDECIDED | both orchestrators |
| D7-INV-001 | D7 | Last-run evidence gap | `[FACT]` `Logs/` covers only `load_customer_accounts` and `daily_transaction_processing` (2024-01-15); no run evidence for units 3-7 or orchestrators. | Customer | UNDECIDED | credit_risk_scoring; monthly_regulatory_reporting; customer_profitability; insurance units |
| D10-INV-001 | D10 | Estate completeness | `[FACT]` `autoexec.sas:14` and all `%include`s point at `/opt/sas/...` server paths outside the repo; no `sasautos` listing, metadata export, or scheduler job list exists. Completeness UNVERIFIABLE. | Customer | UNDECIDED | Whole estate |

## P1 plan decisions (2026-09-01, DEC-013, APPROVED at STOP C 2026-09-01)

Full contract/routing/cutover/decommission columns are in `docs/migration/ts-sas-legacy-analytics_P1_banking_core_plan.md` §1; STOP C approved 2026-09-01: PROPOSED-* below reads as DECIDED / DEFERRED / ACCEPTED.

| ID | Decision | Status | Request |
|---|---|---|---|
| D2-001, D2-002, D2-003, D2-INV-001 | Port 12-file closure as behaviour; 9 banking formats → `sas_ref`; autoexec → libref map + job parameters | PROPOSED-DECIDED | — |
| D3-001..006, 008, 009, D10-002 | Bronze snapshot from `Data/csv`; live ingestion DEFERRED-with-condition | PROPOSED-DEFERRED | REQ-01 |
| D3-INV-001 | Header-only declarations are not lineage; edges dropped | PROPOSED-DECIDED | — |
| D4-001, D4-002, D4-003 | Gold Delta = contract; xlsx via openpyxl task (T-12); email → Jobs notifications; DEFERRED-with-condition on destinations | PROPOSED-DEFERRED | REQ-02 |
| D5-001, D5-002, D10-005 | Workflow task order 1→4; job PAUSED; Control-M remains trigger until STOP E | PROPOSED-DEFERRED | REQ-03 |
| D9-002 | Intra-P1, handled by wave order | PROPOSED-DECIDED | — |
| D9-INV-001 | P1 owns `sas_silver.archive_batch_history` | PROPOSED-DECIDED | — |
| D9-001, D6-INV-001, D10-003, D10-004 | Not touched by P1; deferred to P2/P3 plans | OUT OF P1 SCOPE | — |
| D7-INV-001, D10-INV-001 | Accepted as scope constraints | PROPOSED-ACCEPTED | REQ-04 |
| D10-001, D10-007 | Reference-derived recon (DEC-004); STOP E requires customer in-perimeter recon | PROPOSED-ACCEPTED | REQ-05 |
| D10-006 | Devin creates `sas_legacy` in wave 0 | PROPOSED-DECIDED | — |

### Fired requests

| Req | Ask | Recipient | Lead time | Status |
|---|---|---|---|---|
| REQ-01 | Oracle DW / RAW_BANK delivery path to target (extract to volume or federation; secret names only) | requester → source DBA | ≥ 1 week assumed | FIRED 2026-09-01 (STOP C DM) |
| REQ-02 | `REPORTS.*` consumers, xlsx delivery path, notification destination | requester | days | FIRED 2026-09-01 |
| REQ-03 | Control-M export for `run_daily_banking` | requester → scheduler team | days | FIRED 2026-09-01 |
| REQ-04 | `sasautos` listing / SAS metadata export | requester | days | FIRED 2026-09-01 |
| REQ-05 | In-perimeter SAS run of the 31JAN2024 bootstrap, outputs as CSV | requester | unknown | FIRED 2026-09-01 |

