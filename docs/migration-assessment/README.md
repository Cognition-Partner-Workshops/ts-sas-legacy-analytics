# SAS-to-Databricks Migration Assessment

Comprehensive discovery and assessment of the legacy SAS estate for migration to Databricks (dbt + Unity Catalog + Delta Lake).

## Documents

| # | Document | Description |
|---|----------|-------------|
| [00](00-executive-summary.md) | **Executive Summary** | Estate overview, readiness score, wave plan summary, key risks |
| [01](01-program-inventory.md) | **Program Inventory** | Detailed catalog of all 8 business programs + 2 orchestrators with inputs, outputs, constructs, and complexity ratings |
| [02](02-data-lineage-and-flow.md) | **Data Lineage & Flow** | End-to-end data flow diagrams, library reference map, Oracle/Teradata table inventory |
| [03](03-sas-construct-mapping.md) | **SAS Construct Mapping** | Every SAS language feature → Databricks/dbt equivalent with code examples |
| [04](04-complexity-and-risk-register.md) | **Complexity & Risk Register** | Per-program complexity scoring + 10 identified migration risks with mitigations |
| [05](05-macro-dependency-catalog.md) | **Macro Dependency Catalog** | All 92 macros classified by category and migration relevance (7 critical, 83 no-action) |
| [06](06-migration-wave-plan.md) | **Migration Wave Plan** | 5-wave phased plan with dbt model mapping, acceptance criteria, and parallel run validation |
| [07](07-gap-analysis-vs-dbt-target.md) | **Gap Analysis** | Current dbt target coverage (~15%) vs. full estate requirements (34 models to create) |

## Key Numbers

- **105 SAS files** (8 business programs, 92 macros, 2 orchestrators, 2 format catalogs, 1 config)
- **~27,400 lines of SAS code** across the full estate
- **14 SAS libraries** (3 raw, 3 staging, 3 curated, 3 format, 2 external DB)
- **8 Oracle DW tables** + **2 Teradata tables** referenced
- **14 custom formats** (9 banking, 5 insurance)
- **6 batch steps** across 2 pipelines (4 banking + 2 insurance)
- **Production volumes**: 847K accounts, 2.3M daily transactions, 67M cumulative

## Target Repository

[`uc-data-migration-sas-to-databricks`](https://github.com/Cognition-Partner-Workshops/uc-data-migration-sas-to-databricks) — dbt project with staging/intermediate/marts layers targeting Databricks Unity Catalog.

**Current coverage**: ~15% of estate (6 models + 4 macros exist).
**To build**: 34 additional components (24 models, 10 macros) + infrastructure (Workflows, Auto Loader, Unity Catalog foreign catalogs, alerting).
