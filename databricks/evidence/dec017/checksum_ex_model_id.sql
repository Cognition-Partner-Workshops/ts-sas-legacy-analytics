-- DEC-017 parity checksum: every column except score_timestamp (T-7) AND model_id (the label being corrected);
-- doubles rounded 9dp. Identical before/after proves PD/LGD/EAD/EL/rating unchanged.
SELECT 'risk_scores' AS tbl, COUNT(*) AS n, COUNT(DISTINCT score_timestamp) AS n_ts,
       SUM(hash(account_id, customer_id, account_type, current_balance, credit_limit, acct_age_months,
                days_inactive, ROUND(utilization_pct, 9), customer_segment, region_code, fico_score,
                vantage_score, bureau_inqs_6mo, bureau_trades_open, bureau_derogs, ROUND(bureau_util_pct, 9),
                bureau_oldest_trade_mo, pmt_ontime_12mo, pmt_late_30_12mo, pmt_late_60_12mo, pmt_late_90_12mo,
                max_days_past_due_ever, months_since_last_dpd, ROUND(avg_pmt_ratio_12mo, 9), collateral_value,
                last_appraisal_date, ROUND(ltv, 9), ROUND(pd, 9), ROUND(lgd, 9), ROUND(ead, 9),
                ROUND(expected_loss, 9), new_risk_rating, score_date)) AS checksum,
       ARRAY_JOIN(ARRAY_SORT(COLLECT_SET(model_id)), ',') AS model_ids
FROM sas_legacy.sas_silver.risk_scores WHERE score_date = DATE'2024-01-31'
UNION ALL
SELECT 'risk_migration', COUNT(*), 0,
       SUM(hash(score_date, account_id, prev_rating, curr_rating, migration_direction, ROUND(pd, 9),
                ROUND(expected_loss, 9))), NULL
FROM sas_legacy.sas_silver.risk_migration WHERE score_date = DATE'2024-01-31'
UNION ALL
SELECT 'risk_summary', COUNT(*), 0,
       SUM(hash(account_type, new_risk_rating, n_accounts, ROUND(avg_pd, 9), ROUND(avg_lgd, 9),
                ROUND(total_ead, 6), ROUND(total_el, 6))), NULL
FROM sas_legacy.sas_gold.risk_summary
