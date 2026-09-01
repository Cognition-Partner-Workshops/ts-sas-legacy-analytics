SELECT 'monthly_rwa' AS tbl, COUNT(*) AS n,
       SUM(hash(report_month, account_type, customer_segment, risk_weight, n_accounts,
                total_exposure, rwa)) AS checksum
FROM sas_legacy.sas_gold.monthly_rwa WHERE report_month='202401'
UNION ALL
SELECT 'delinquency_aging', COUNT(*),
       SUM(hash(report_month, account_type, region_code, delinq_bucket, n_accounts,
                total_balance, total_past_due))
FROM sas_legacy.sas_gold.delinquency_aging WHERE report_month='202401'
UNION ALL
SELECT 'llp_coverage', COUNT(*),
       SUM(hash(report_month, account_type, n_loans, gross_loans, total_allowance,
                ROUND(coverage_pct, 6), npl_balance, ROUND(npl_coverage_pct, 6)))
FROM sas_legacy.sas_gold.llp_coverage WHERE report_month='202401'
UNION ALL
SELECT 'capital_adequacy', COUNT(*),
       SUM(hash(report_month, total_rwa, cet1_capital, tier1_capital, total_capital,
                ROUND(cet1_ratio, 6), ROUND(tier1_ratio, 6), ROUND(total_capital_ratio, 6),
                cet1_status, tier1_status, total_capital_status))
FROM sas_legacy.sas_gold.capital_adequacy WHERE report_month='202401';
