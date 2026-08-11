# Program → Macro Dependency Graph

> Which programs call which macros, and how macros depend on each other.

## 1. Program-Level Dependencies

### Batch Orchestrators

```
run_daily_banking.sas
├── %include autoexec.sas
├── %sendmail          (error notification + summary)
└── %include (dynamic via %run_step)
    ├── load_customer_accounts.sas       [Step 1]
    ├── daily_transaction_processing.sas [Step 2]
    ├── credit_risk_scoring.sas          [Step 3]
    └── monthly_regulatory_reporting.sas [Step 4]

run_daily_insurance.sas
├── %include autoexec.sas
├── %sendmail          (error notification)
└── %include (dynamic via %run_step)
    ├── claims_processing.sas            [Step 1]
    └── policy_valuation.sas             [Step 2]
```

### Banking Programs

```
load_customer_accounts.sas
├── %parmv       (parameter validation)
├── %nobs        (row count checks)
├── %lock        (not directly called but included)
└── %sendmail    (conditional: >100 exceptions)

daily_transaction_processing.sas
├── %parmv       (parameter validation)
├── %nobs        (row count checks)
└── %lock        (dataset lock/unlock for CURATED.DAILY_TRANSACTIONS)

credit_risk_scoring.sas
├── %parmv       (parameter validation)
├── %nobs        (row count checks)
└── %lock        (dataset lock/unlock for CURATED.RISK_SCORES, CURATED.RISK_MIGRATION)

monthly_regulatory_reporting.sas
├── %parmv       (parameter validation)
├── %nobs        (row count checks)
└── %export_xlsx (3 calls: RWA, Delinquency, LLP_Coverage sheets)
```

### Insurance Programs

```
claims_processing.sas
├── %parmv       (parameter validation)
├── %nobs        (row count checks)
└── %sendmail    (fraud alert notification to SIU)

policy_valuation.sas
├── %parmv       (parameter validation)
└── %nobs        (row count checks)
```

### Reports

```
customer_profitability.sas
├── %parmv       (parameter validation)
├── %nobs        (row count checks)
└── %export_xlsx (segment profitability export)
```

### Standalone / Utility Programs

```
Parent-Child-Index.sas
├── %seplist     (SQL separated list generation — 2 calls)
├── %hash_define (define hash for dimension lookup)
└── %hash_lookup (lookup from defined hash)
```

## 2. Macro-to-Macro Dependencies (Internal Call Graph)

Key utility macros and what they depend on:

```
%parmv ─── (self-contained, leaf node)
  └── used by: 78 of 92 macros

%nobs ──── %parmv
  └── used by: 7 programs + several macros

%lock ──── %parmv, %get_data_attr, %handle
  └── %handle ── %parmv, %loop, %nobs, %sendmail

%sendmail ── %parmv, %seplist
  └── %seplist ── %parmv

%export_xlsx ── %parmv, %export_dbms
  └── %export_dbms ── %parmv

%hash_define ── %parmv, %seplist, %loop
%hash_lookup ── %parmv

%seplist ── %parmv
  └── used by: 14 macros

%loop ── %parmv
  └── used by: 11 macros (compare, create_directory, excel2sas, etc.)

%kill ── %parmv
  └── used by: compare, excel2sas, hash_split_dataset, transpose
```

## 3. Full Adjacency List (Program → Macros Used)

| Program | Macros Called Directly |
|---------|-----------------------|
| `run_daily_banking.sas` | `%sendmail` |
| `run_daily_insurance.sas` | `%sendmail` |
| `load_customer_accounts.sas` | `%parmv`, `%nobs`, `%sendmail` |
| `daily_transaction_processing.sas` | `%parmv`, `%nobs`, `%lock` |
| `credit_risk_scoring.sas` | `%parmv`, `%nobs`, `%lock` |
| `monthly_regulatory_reporting.sas` | `%parmv`, `%nobs`, `%export_xlsx` |
| `claims_processing.sas` | `%parmv`, `%nobs`, `%sendmail` |
| `policy_valuation.sas` | `%parmv`, `%nobs` |
| `customer_profitability.sas` | `%parmv`, `%nobs`, `%export_xlsx` |
| `Parent-Child-Index.sas` | `%seplist`, `%hash_define`, `%hash_lookup` |

## 4. Macro Usage Heatmap

| Macro | # Programs Using It | Transitive Dependents |
|-------|--------------------|-----------------------|
| `%parmv` | 7 (all main programs) | 78 macros |
| `%nobs` | 7 (all main programs) | `create_format`, `get_permutations`, `handle`, `randlist`, `reduce_pixel`, `export_saphari`, `guess_pk` |
| `%sendmail` | 4 (load_customer_accounts, claims_processing, run_daily_banking, run_daily_insurance) | `handle` |
| `%lock` | 2 (daily_transaction_processing, credit_risk_scoring) | `stp_batch_submit` |
| `%export_xlsx` | 2 (monthly_regulatory_reporting, customer_profitability) | — |
| `%seplist` | 1 (Parent-Child-Index) | 14 macros internally |
| `%hash_define` | 1 (Parent-Child-Index) | — |
| `%hash_lookup` | 1 (Parent-Child-Index) | — |

## 5. %include Chain (Static File Inclusions)

```
autoexec.sas
  included by → run_daily_banking.sas, run_daily_insurance.sas

parmv.sas
  included by → all 7 main programs

nobs.sas
  included by → all 7 main programs

lock.sas
  included by → load_customer_accounts, daily_transaction_processing,
                credit_risk_scoring (3 programs, note: not all use %lock directly)

sendmail.sas
  included by → load_customer_accounts (conditional), claims_processing

export_xlsx.sas
  included by → monthly_regulatory_reporting, customer_profitability
```

## 6. Data Flow Dependencies (Program Execution Order)

```
                    autoexec.sas (environment)
                         │
            ┌────────────┴────────────┐
            ▼                         ▼
    BANKING PIPELINE            INSURANCE PIPELINE
            │                         │
    ┌───────┴───────┐         ┌───────┴───────┐
    ▼               │         ▼               ▼
 load_customer   (waits)   claims_       policy_
 _accounts         │       processing    valuation
    │               │
    ▼               │
 daily_transaction  │
 _processing        │
    │               │
    ▼               │
 credit_risk_       │
 _scoring           │
    │               │
    ▼               │
 monthly_regulatory◄┘
 _reporting
    │
    ▼
 customer_profitability (monthly, cross-cutting)
```
