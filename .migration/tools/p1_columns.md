# P1 banking-core column extraction

Repository: `/home/ubuntu/repos/ts-sas-legacy-analytics`

Mechanical extraction of output-table columns from the five requested SAS programs.
Types are SAS types/evidence only; no Delta types are computed.

## Output tables

### STG_BANK.CUST_ACCOUNTS_DAILY

Created/appended by: Programs/Banking/load_customer_accounts.sas:82

| # | Column | Expression/source | SAS type | Format | Key | Evidence | Cite | CSV evidence |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | ACCOUNT_ID | ORA_DW.CUST_ACCOUNTS.ACCOUNT_ID | carried from ORA_DW.CUST_ACCOUNTS.ACCOUNT_ID | — | yes | INFERRED | Programs/Banking/load_customer_accounts.sas:85 | Data/csv/oracle_dw/CUST_ACCOUNTS.csv::ACCOUNT_ID=A00000001 |
| 2 | CUSTOMER_ID | ORA_DW.CUST_ACCOUNTS.CUSTOMER_ID | carried from ORA_DW.CUST_ACCOUNTS.CUSTOMER_ID | — | yes | INFERRED | Programs/Banking/load_customer_accounts.sas:85 | Data/csv/oracle_dw/CUST_ACCOUNTS.csv::CUSTOMER_ID=C0000001 |
| 3 | ACCOUNT_TYPE | ORA_DW.CUST_ACCOUNTS.ACCOUNT_TYPE | carried from ORA_DW.CUST_ACCOUNTS.ACCOUNT_TYPE | $ACCTTYPE. | no | INFERRED | Programs/Banking/load_customer_accounts.sas:85 | Data/csv/oracle_dw/CUST_ACCOUNTS.csv::ACCOUNT_TYPE=CC |
| 4 | ACCOUNT_STATUS | ORA_DW.CUST_ACCOUNTS.ACCOUNT_STATUS | carried from ORA_DW.CUST_ACCOUNTS.ACCOUNT_STATUS | $ACCTSTAT. | yes | INFERRED | Programs/Banking/load_customer_accounts.sas:85 | Data/csv/oracle_dw/CUST_ACCOUNTS.csv::ACCOUNT_STATUS=A |
| 5 | OPEN_DATE | ORA_DW.CUST_ACCOUNTS.OPEN_DATE | carried from ORA_DW.CUST_ACCOUNTS.OPEN_DATE | DATE9. | yes | INFERRED | Programs/Banking/load_customer_accounts.sas:85 | Data/csv/oracle_dw/CUST_ACCOUNTS.csv::OPEN_DATE=27NOV2011 |
| 6 | CLOSE_DATE | ORA_DW.CUST_ACCOUNTS.CLOSE_DATE | carried from ORA_DW.CUST_ACCOUNTS.CLOSE_DATE | DATE9. | no | INFERRED | Programs/Banking/load_customer_accounts.sas:85 | Data/csv/oracle_dw/CUST_ACCOUNTS.csv::CLOSE_DATE= |
| 7 | CURRENT_BALANCE | ORA_DW.CUST_ACCOUNTS.CURRENT_BALANCE | carried from ORA_DW.CUST_ACCOUNTS.CURRENT_BALANCE | DOLLAR18.2 | no | INFERRED | Programs/Banking/load_customer_accounts.sas:85 | Data/csv/oracle_dw/CUST_ACCOUNTS.csv::CURRENT_BALANCE=880.19 |
| 8 | AVAILABLE_BALANCE | ORA_DW.CUST_ACCOUNTS.AVAILABLE_BALANCE | carried from ORA_DW.CUST_ACCOUNTS.AVAILABLE_BALANCE | DOLLAR18.2 | no | INFERRED | Programs/Banking/load_customer_accounts.sas:85 | Data/csv/oracle_dw/CUST_ACCOUNTS.csv::AVAILABLE_BALANCE=619.81 |
| 9 | CREDIT_LIMIT | ORA_DW.CUST_ACCOUNTS.CREDIT_LIMIT | carried from ORA_DW.CUST_ACCOUNTS.CREDIT_LIMIT | DOLLAR18.2 | no | INFERRED | Programs/Banking/load_customer_accounts.sas:85 | Data/csv/oracle_dw/CUST_ACCOUNTS.csv::CREDIT_LIMIT=1500.00 |
| 10 | INTEREST_RATE | ORA_DW.CUST_ACCOUNTS.INTEREST_RATE | carried from ORA_DW.CUST_ACCOUNTS.INTEREST_RATE | — | no | INFERRED | Programs/Banking/load_customer_accounts.sas:85 | Data/csv/oracle_dw/CUST_ACCOUNTS.csv::INTEREST_RATE=0.2009 |
| 11 | BRANCH_ID | ORA_DW.CUST_ACCOUNTS.BRANCH_ID | carried from ORA_DW.CUST_ACCOUNTS.BRANCH_ID | — | no | INFERRED | Programs/Banking/load_customer_accounts.sas:85 | Data/csv/oracle_dw/CUST_ACCOUNTS.csv::BRANCH_ID=B015 |
| 12 | OFFICER_ID | ORA_DW.CUST_ACCOUNTS.OFFICER_ID | carried from ORA_DW.CUST_ACCOUNTS.OFFICER_ID | — | no | INFERRED | Programs/Banking/load_customer_accounts.sas:85 | Data/csv/oracle_dw/CUST_ACCOUNTS.csv::OFFICER_ID=O0088 |
| 13 | LAST_ACTIVITY_DATE | ORA_DW.CUST_ACCOUNTS.LAST_ACTIVITY_DATE | carried from ORA_DW.CUST_ACCOUNTS.LAST_ACTIVITY_DATE | DATE9. | no | INFERRED | Programs/Banking/load_customer_accounts.sas:85 | Data/csv/oracle_dw/CUST_ACCOUNTS.csv::LAST_ACTIVITY_DATE=03NOV2023 |
| 14 | FIRST_NAME | ORA_DW.CUST_DEMOGRAPHICS.FIRST_NAME | carried from ORA_DW.CUST_DEMOGRAPHICS.FIRST_NAME | — | no | INFERRED | Programs/Banking/load_customer_accounts.sas:85 | Data/csv/oracle_dw/CUST_DEMOGRAPHICS.csv::FIRST_NAME=Linda |
| 15 | LAST_NAME | ORA_DW.CUST_DEMOGRAPHICS.LAST_NAME | carried from ORA_DW.CUST_DEMOGRAPHICS.LAST_NAME | — | no | INFERRED | Programs/Banking/load_customer_accounts.sas:85 | Data/csv/oracle_dw/CUST_DEMOGRAPHICS.csv::LAST_NAME=Lopez |
| 16 | SSN_HASH | ORA_DW.CUST_DEMOGRAPHICS.SSN_HASH | carried from ORA_DW.CUST_DEMOGRAPHICS.SSN_HASH | — | no | INFERRED | Programs/Banking/load_customer_accounts.sas:85 | Data/csv/oracle_dw/CUST_DEMOGRAPHICS.csv::SSN_HASH=a47401f094a96eef71465948a306129a |
| 17 | DATE_OF_BIRTH | ORA_DW.CUST_DEMOGRAPHICS.DATE_OF_BIRTH | carried from ORA_DW.CUST_DEMOGRAPHICS.DATE_OF_BIRTH | — | no | INFERRED | Programs/Banking/load_customer_accounts.sas:85 | Data/csv/oracle_dw/CUST_DEMOGRAPHICS.csv::DATE_OF_BIRTH=12AUG1958 |
| 18 | CUSTOMER_SEGMENT | ORA_DW.CUST_DEMOGRAPHICS.CUSTOMER_SEGMENT | carried from ORA_DW.CUST_DEMOGRAPHICS.CUSTOMER_SEGMENT | $CUSTSEG. | no | INFERRED | Programs/Banking/load_customer_accounts.sas:85 | Data/csv/oracle_dw/CUST_DEMOGRAPHICS.csv::CUSTOMER_SEGMENT=SMB |
| 19 | RISK_RATING | ORA_DW.CUST_DEMOGRAPHICS.RISK_RATING | carried from ORA_DW.CUST_DEMOGRAPHICS.RISK_RATING | RISKRATE. | no | INFERRED | Programs/Banking/load_customer_accounts.sas:85 | Data/csv/oracle_dw/CUST_DEMOGRAPHICS.csv::RISK_RATING=5 |
| 20 | REGION_CODE | ORA_DW.CUST_DEMOGRAPHICS.REGION_CODE | carried from ORA_DW.CUST_DEMOGRAPHICS.REGION_CODE | $REGION. | yes | INFERRED | Programs/Banking/load_customer_accounts.sas:85 | Data/csv/oracle_dw/CUST_DEMOGRAPHICS.csv::REGION_CODE=MW |
| 21 | PRIMARY_EMAIL | ORA_DW.CUST_DEMOGRAPHICS.PRIMARY_EMAIL | carried from ORA_DW.CUST_DEMOGRAPHICS.PRIMARY_EMAIL | — | no | INFERRED | Programs/Banking/load_customer_accounts.sas:85 | Data/csv/oracle_dw/CUST_DEMOGRAPHICS.csv::PRIMARY_EMAIL=linda.lopez1@example.com |
| 22 | PHONE_NUMBER | ORA_DW.CUST_DEMOGRAPHICS.PHONE_NUMBER | carried from ORA_DW.CUST_DEMOGRAPHICS.PHONE_NUMBER | — | no | INFERRED | Programs/Banking/load_customer_accounts.sas:85 | Data/csv/oracle_dw/CUST_DEMOGRAPHICS.csv::PHONE_NUMBER=555-943-3892 |
| 23 | ACCT_AGE_MONTHS | intck('month', OPEN_DATE, "&run_date"d) | num | — | no | FACT | Programs/Banking/load_customer_accounts.sas:100 | — |
| 24 | DAYS_INACTIVE | "&run_date"d - LAST_ACTIVITY_DATE | num | — | no | FACT | Programs/Banking/load_customer_accounts.sas:103 | — |
| 25 | UTILIZATION_PCT | (CURRENT_BALANCE / CREDIT_LIMIT) * 100 | num | — | no | FACT | Programs/Banking/load_customer_accounts.sas:107 | — |
| 26 | DORMANCY_FLAG | 'Y' / 'N' | char$1 | — | no | FACT | Programs/Banking/load_customer_accounts.sas:113 | — |
| 27 | HIGH_BALANCE_FLAG | 'Y' / 'N' | char$1 | — | no | FACT | Programs/Banking/load_customer_accounts.sas:119 | — |
| 28 | SNAPSHOT_DATE | "&run_date"d | num (SAS date) | — | no | FACT | Programs/Banking/load_customer_accounts.sas:150 | — |
| 29 | LOAD_TIMESTAMP | datetime() | num (SAS datetime) | — | no | FACT | Programs/Banking/load_customer_accounts.sas:151 | — |

### STG_BANK.ACCT_EXCEPTIONS

Created/appended by: Programs/Banking/load_customer_accounts.sas:168

| # | Column | Expression/source | SAS type | Format | Key | Evidence | Cite | CSV evidence |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | ACCOUNT_ID | ORA_DW.CUST_ACCOUNTS.ACCOUNT_ID | carried from ORA_DW.CUST_ACCOUNTS.ACCOUNT_ID | — | yes | INFERRED | Programs/Banking/load_customer_accounts.sas:85 | Data/csv/oracle_dw/CUST_ACCOUNTS.csv::ACCOUNT_ID=A00000001 |
| 2 | CUSTOMER_ID | ORA_DW.CUST_ACCOUNTS.CUSTOMER_ID | carried from ORA_DW.CUST_ACCOUNTS.CUSTOMER_ID | — | yes | INFERRED | Programs/Banking/load_customer_accounts.sas:85 | Data/csv/oracle_dw/CUST_ACCOUNTS.csv::CUSTOMER_ID=C0000001 |
| 3 | ACCOUNT_TYPE | ORA_DW.CUST_ACCOUNTS.ACCOUNT_TYPE | carried from ORA_DW.CUST_ACCOUNTS.ACCOUNT_TYPE | $ACCTTYPE. | no | INFERRED | Programs/Banking/load_customer_accounts.sas:85 | Data/csv/oracle_dw/CUST_ACCOUNTS.csv::ACCOUNT_TYPE=CC |
| 4 | ACCOUNT_STATUS | ORA_DW.CUST_ACCOUNTS.ACCOUNT_STATUS | carried from ORA_DW.CUST_ACCOUNTS.ACCOUNT_STATUS | $ACCTSTAT. | yes | INFERRED | Programs/Banking/load_customer_accounts.sas:85 | Data/csv/oracle_dw/CUST_ACCOUNTS.csv::ACCOUNT_STATUS=A |
| 5 | OPEN_DATE | ORA_DW.CUST_ACCOUNTS.OPEN_DATE | carried from ORA_DW.CUST_ACCOUNTS.OPEN_DATE | DATE9. | yes | INFERRED | Programs/Banking/load_customer_accounts.sas:85 | Data/csv/oracle_dw/CUST_ACCOUNTS.csv::OPEN_DATE=27NOV2011 |
| 6 | CLOSE_DATE | ORA_DW.CUST_ACCOUNTS.CLOSE_DATE | carried from ORA_DW.CUST_ACCOUNTS.CLOSE_DATE | DATE9. | no | INFERRED | Programs/Banking/load_customer_accounts.sas:85 | Data/csv/oracle_dw/CUST_ACCOUNTS.csv::CLOSE_DATE= |
| 7 | CURRENT_BALANCE | ORA_DW.CUST_ACCOUNTS.CURRENT_BALANCE | carried from ORA_DW.CUST_ACCOUNTS.CURRENT_BALANCE | DOLLAR18.2 | no | INFERRED | Programs/Banking/load_customer_accounts.sas:85 | Data/csv/oracle_dw/CUST_ACCOUNTS.csv::CURRENT_BALANCE=880.19 |
| 8 | AVAILABLE_BALANCE | ORA_DW.CUST_ACCOUNTS.AVAILABLE_BALANCE | carried from ORA_DW.CUST_ACCOUNTS.AVAILABLE_BALANCE | DOLLAR18.2 | no | INFERRED | Programs/Banking/load_customer_accounts.sas:85 | Data/csv/oracle_dw/CUST_ACCOUNTS.csv::AVAILABLE_BALANCE=619.81 |
| 9 | CREDIT_LIMIT | ORA_DW.CUST_ACCOUNTS.CREDIT_LIMIT | carried from ORA_DW.CUST_ACCOUNTS.CREDIT_LIMIT | DOLLAR18.2 | no | INFERRED | Programs/Banking/load_customer_accounts.sas:85 | Data/csv/oracle_dw/CUST_ACCOUNTS.csv::CREDIT_LIMIT=1500.00 |
| 10 | INTEREST_RATE | ORA_DW.CUST_ACCOUNTS.INTEREST_RATE | carried from ORA_DW.CUST_ACCOUNTS.INTEREST_RATE | — | no | INFERRED | Programs/Banking/load_customer_accounts.sas:85 | Data/csv/oracle_dw/CUST_ACCOUNTS.csv::INTEREST_RATE=0.2009 |
| 11 | BRANCH_ID | ORA_DW.CUST_ACCOUNTS.BRANCH_ID | carried from ORA_DW.CUST_ACCOUNTS.BRANCH_ID | — | no | INFERRED | Programs/Banking/load_customer_accounts.sas:85 | Data/csv/oracle_dw/CUST_ACCOUNTS.csv::BRANCH_ID=B015 |
| 12 | OFFICER_ID | ORA_DW.CUST_ACCOUNTS.OFFICER_ID | carried from ORA_DW.CUST_ACCOUNTS.OFFICER_ID | — | no | INFERRED | Programs/Banking/load_customer_accounts.sas:85 | Data/csv/oracle_dw/CUST_ACCOUNTS.csv::OFFICER_ID=O0088 |
| 13 | LAST_ACTIVITY_DATE | ORA_DW.CUST_ACCOUNTS.LAST_ACTIVITY_DATE | carried from ORA_DW.CUST_ACCOUNTS.LAST_ACTIVITY_DATE | DATE9. | no | INFERRED | Programs/Banking/load_customer_accounts.sas:85 | Data/csv/oracle_dw/CUST_ACCOUNTS.csv::LAST_ACTIVITY_DATE=03NOV2023 |
| 14 | FIRST_NAME | ORA_DW.CUST_DEMOGRAPHICS.FIRST_NAME | carried from ORA_DW.CUST_DEMOGRAPHICS.FIRST_NAME | — | no | INFERRED | Programs/Banking/load_customer_accounts.sas:85 | Data/csv/oracle_dw/CUST_DEMOGRAPHICS.csv::FIRST_NAME=Linda |
| 15 | LAST_NAME | ORA_DW.CUST_DEMOGRAPHICS.LAST_NAME | carried from ORA_DW.CUST_DEMOGRAPHICS.LAST_NAME | — | no | INFERRED | Programs/Banking/load_customer_accounts.sas:85 | Data/csv/oracle_dw/CUST_DEMOGRAPHICS.csv::LAST_NAME=Lopez |
| 16 | SSN_HASH | ORA_DW.CUST_DEMOGRAPHICS.SSN_HASH | carried from ORA_DW.CUST_DEMOGRAPHICS.SSN_HASH | — | no | INFERRED | Programs/Banking/load_customer_accounts.sas:85 | Data/csv/oracle_dw/CUST_DEMOGRAPHICS.csv::SSN_HASH=a47401f094a96eef71465948a306129a |
| 17 | DATE_OF_BIRTH | ORA_DW.CUST_DEMOGRAPHICS.DATE_OF_BIRTH | carried from ORA_DW.CUST_DEMOGRAPHICS.DATE_OF_BIRTH | — | no | INFERRED | Programs/Banking/load_customer_accounts.sas:85 | Data/csv/oracle_dw/CUST_DEMOGRAPHICS.csv::DATE_OF_BIRTH=12AUG1958 |
| 18 | CUSTOMER_SEGMENT | ORA_DW.CUST_DEMOGRAPHICS.CUSTOMER_SEGMENT | carried from ORA_DW.CUST_DEMOGRAPHICS.CUSTOMER_SEGMENT | $CUSTSEG. | no | INFERRED | Programs/Banking/load_customer_accounts.sas:85 | Data/csv/oracle_dw/CUST_DEMOGRAPHICS.csv::CUSTOMER_SEGMENT=SMB |
| 19 | RISK_RATING | ORA_DW.CUST_DEMOGRAPHICS.RISK_RATING | carried from ORA_DW.CUST_DEMOGRAPHICS.RISK_RATING | RISKRATE. | no | INFERRED | Programs/Banking/load_customer_accounts.sas:85 | Data/csv/oracle_dw/CUST_DEMOGRAPHICS.csv::RISK_RATING=5 |
| 20 | REGION_CODE | ORA_DW.CUST_DEMOGRAPHICS.REGION_CODE | carried from ORA_DW.CUST_DEMOGRAPHICS.REGION_CODE | $REGION. | yes | INFERRED | Programs/Banking/load_customer_accounts.sas:85 | Data/csv/oracle_dw/CUST_DEMOGRAPHICS.csv::REGION_CODE=MW |
| 21 | PRIMARY_EMAIL | ORA_DW.CUST_DEMOGRAPHICS.PRIMARY_EMAIL | carried from ORA_DW.CUST_DEMOGRAPHICS.PRIMARY_EMAIL | — | no | INFERRED | Programs/Banking/load_customer_accounts.sas:85 | Data/csv/oracle_dw/CUST_DEMOGRAPHICS.csv::PRIMARY_EMAIL=linda.lopez1@example.com |
| 22 | PHONE_NUMBER | ORA_DW.CUST_DEMOGRAPHICS.PHONE_NUMBER | carried from ORA_DW.CUST_DEMOGRAPHICS.PHONE_NUMBER | — | no | INFERRED | Programs/Banking/load_customer_accounts.sas:85 | Data/csv/oracle_dw/CUST_DEMOGRAPHICS.csv::PHONE_NUMBER=555-943-3892 |
| 23 | ACCT_AGE_MONTHS | intck('month', OPEN_DATE, "&run_date"d) | num | — | no | FACT | Programs/Banking/load_customer_accounts.sas:100 | — |
| 24 | DAYS_INACTIVE | "&run_date"d - LAST_ACTIVITY_DATE | num | — | no | FACT | Programs/Banking/load_customer_accounts.sas:103 | — |
| 25 | UTILIZATION_PCT | (CURRENT_BALANCE / CREDIT_LIMIT) * 100 | num | — | no | FACT | Programs/Banking/load_customer_accounts.sas:107 | — |
| 26 | DORMANCY_FLAG | 'Y' / 'N' | char$1 | — | no | FACT | Programs/Banking/load_customer_accounts.sas:113 | — |
| 27 | HIGH_BALANCE_FLAG | 'Y' / 'N' | char$1 | — | no | FACT | Programs/Banking/load_customer_accounts.sas:119 | — |
| 28 | SNAPSHOT_DATE | "&run_date"d | num (SAS date) | — | no | FACT | Programs/Banking/load_customer_accounts.sas:150 | — |
| 29 | LOAD_TIMESTAMP | datetime() | num (SAS datetime) | — | no | FACT | Programs/Banking/load_customer_accounts.sas:151 | — |

Note: WORK.ACCT_EXCEPTIONS is output at lines 129/138/146, then inserted with SELECT *; the compiled PDV determines column order.

### CURATED.DAILY_TRANSACTIONS

Created/appended by: Programs/Banking/daily_transaction_processing.sas:207

| # | Column | Expression/source | SAS type | Format | Key | Evidence | Cite | CSV evidence |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | TRANSACTION_ID | RAW_BANK.TXN_FEED_20240131.TRANSACTION_ID | carried from RAW_BANK.TXN_FEED_20240131.TRANSACTION_ID | — | yes | INFERRED | Programs/Banking/daily_transaction_processing.sas:107 | Data/csv/raw_bank/TXN_FEED_20240131.csv::TRANSACTION_ID=T000000001 |
| 2 | ACCOUNT_ID | RAW_BANK.TXN_FEED_20240131.ACCOUNT_ID | carried from RAW_BANK.TXN_FEED_20240131.ACCOUNT_ID | — | yes | INFERRED | Programs/Banking/daily_transaction_processing.sas:107 | Data/csv/raw_bank/TXN_FEED_20240131.csv::ACCOUNT_ID=A00000004 |
| 3 | TRANSACTION_DATE | RAW_BANK.TXN_FEED_20240131.TRANSACTION_DATE | carried from RAW_BANK.TXN_FEED_20240131.TRANSACTION_DATE | — | yes | INFERRED | Programs/Banking/daily_transaction_processing.sas:107 | Data/csv/raw_bank/TXN_FEED_20240131.csv::TRANSACTION_DATE=31JAN2024 |
| 4 | TRANSACTION_TYPE | RAW_BANK.TXN_FEED_20240131.TRANSACTION_TYPE | carried from RAW_BANK.TXN_FEED_20240131.TRANSACTION_TYPE | — | no | INFERRED | Programs/Banking/daily_transaction_processing.sas:107 | Data/csv/raw_bank/TXN_FEED_20240131.csv::TRANSACTION_TYPE=REF |
| 5 | TRANSACTION_AMOUNT | RAW_BANK.TXN_FEED_20240131.TRANSACTION_AMOUNT | carried from RAW_BANK.TXN_FEED_20240131.TRANSACTION_AMOUNT | — | no | INFERRED | Programs/Banking/daily_transaction_processing.sas:107 | Data/csv/raw_bank/TXN_FEED_20240131.csv::TRANSACTION_AMOUNT=1804.93 |
| 6 | CHANNEL | RAW_BANK.TXN_FEED_20240131.CHANNEL | carried from RAW_BANK.TXN_FEED_20240131.CHANNEL | — | no | INFERRED | Programs/Banking/daily_transaction_processing.sas:107 | Data/csv/raw_bank/TXN_FEED_20240131.csv::CHANNEL=WIRE |
| 7 | MERCHANT_CATEGORY | RAW_BANK.TXN_FEED_20240131.MERCHANT_CATEGORY | carried from RAW_BANK.TXN_FEED_20240131.MERCHANT_CATEGORY | — | no | INFERRED | Programs/Banking/daily_transaction_processing.sas:107 | Data/csv/raw_bank/TXN_FEED_20240131.csv::MERCHANT_CATEGORY=4900 |
| 8 | DESCRIPTION | RAW_BANK.TXN_FEED_20240131.DESCRIPTION | carried from RAW_BANK.TXN_FEED_20240131.DESCRIPTION | — | no | INFERRED | Programs/Banking/daily_transaction_processing.sas:107 | Data/csv/raw_bank/TXN_FEED_20240131.csv::DESCRIPTION=REF MOBILE REF714480 |
| 9 | POST_DATE | RAW_BANK.TXN_FEED_20240131.POST_DATE | carried from RAW_BANK.TXN_FEED_20240131.POST_DATE | — | no | INFERRED | Programs/Banking/daily_transaction_processing.sas:107 | Data/csv/raw_bank/TXN_FEED_20240131.csv::POST_DATE=31JAN2024 |
| 10 | CURRENCY_CODE | RAW_BANK.TXN_FEED_20240131.CURRENCY_CODE | carried from RAW_BANK.TXN_FEED_20240131.CURRENCY_CODE | — | no | INFERRED | Programs/Banking/daily_transaction_processing.sas:107 | Data/csv/raw_bank/TXN_FEED_20240131.csv::CURRENCY_CODE=USD |
| 11 | ACCOUNT_TYPE | STG_BANK.CUST_ACCOUNTS_DAILY.ACCOUNT_TYPE | carried from STG_BANK.CUST_ACCOUNTS_DAILY.ACCOUNT_TYPE | — | no | INFERRED | Programs/Banking/daily_transaction_processing.sas:107 | — |
| 12 | CUSTOMER_ID | STG_BANK.CUST_ACCOUNTS_DAILY.CUSTOMER_ID | carried from STG_BANK.CUST_ACCOUNTS_DAILY.CUSTOMER_ID | — | no | INFERRED | Programs/Banking/daily_transaction_processing.sas:107 | — |
| 13 | CUSTOMER_SEGMENT | STG_BANK.CUST_ACCOUNTS_DAILY.CUSTOMER_SEGMENT | carried from STG_BANK.CUST_ACCOUNTS_DAILY.CUSTOMER_SEGMENT | — | no | INFERRED | Programs/Banking/daily_transaction_processing.sas:107 | — |
| 14 | REGION_CODE | STG_BANK.CUST_ACCOUNTS_DAILY.REGION_CODE | carried from STG_BANK.CUST_ACCOUNTS_DAILY.REGION_CODE | — | no | INFERRED | Programs/Banking/daily_transaction_processing.sas:107 | — |
| 15 | BRANCH_ID | STG_BANK.CUST_ACCOUNTS_DAILY.BRANCH_ID | carried from STG_BANK.CUST_ACCOUNTS_DAILY.BRANCH_ID | — | no | INFERRED | Programs/Banking/daily_transaction_processing.sas:107 | — |
| 16 | PRE_TXN_BALANCE | a.CURRENT_BALANCE as PRE_TXN_BALANCE | num | DOLLAR18.2 | no | FACT | Programs/Banking/daily_transaction_processing.sas:114 | — |
| 17 | POST_TXN_BALANCE | case ... end as POST_TXN_BALANCE | num | DOLLAR18.2 | no | FACT | Programs/Banking/daily_transaction_processing.sas:123 | — |
| 18 | RISK_RATING | STG_BANK.CUST_ACCOUNTS_DAILY.RISK_RATING | carried from STG_BANK.CUST_ACCOUNTS_DAILY.RISK_RATING | — | no | INFERRED | Programs/Banking/daily_transaction_processing.sas:124 | — |
| 19 | RUNNING_BALANCE | RUNNING_BALANCE = PRE_TXN_BALANCE + signed TRANSACTION_AMOUNT | num | DOLLAR18.2 | no | FACT | Programs/Banking/daily_transaction_processing.sas:141 | — |

### CURATED.RUNNING_BALANCES

Created/appended by: Programs/Banking/daily_transaction_processing.sas:222

| # | Column | Expression/source | SAS type | Format | Key | Evidence | Cite | CSV evidence |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | ACCOUNT_ID | RAW_BANK.TXN_FEED_20240131.ACCOUNT_ID | carried from RAW_BANK.TXN_FEED_20240131.ACCOUNT_ID | — | yes | INFERRED | Programs/Banking/daily_transaction_processing.sas:224 | Data/csv/raw_bank/TXN_FEED_20240131.csv::ACCOUNT_ID=A00000004 |
| 2 | TRANSACTION_DATE | RAW_BANK.TXN_FEED_20240131.TRANSACTION_DATE | carried from RAW_BANK.TXN_FEED_20240131.TRANSACTION_DATE | — | yes | INFERRED | Programs/Banking/daily_transaction_processing.sas:224 | Data/csv/raw_bank/TXN_FEED_20240131.csv::TRANSACTION_DATE=31JAN2024 |
| 3 | TRANSACTION_ID | RAW_BANK.TXN_FEED_20240131.TRANSACTION_ID | carried from RAW_BANK.TXN_FEED_20240131.TRANSACTION_ID | — | yes | INFERRED | Programs/Banking/daily_transaction_processing.sas:224 | Data/csv/raw_bank/TXN_FEED_20240131.csv::TRANSACTION_ID=T000000001 |
| 4 | RUNNING_BALANCE | RUNNING_BALANCE | num | DOLLAR18.2 | no | FACT | Programs/Banking/daily_transaction_processing.sas:224 | — |

### CURATED.TXN_ANOMALIES

Created/appended by: Programs/Banking/daily_transaction_processing.sas:214

| # | Column | Expression/source | SAS type | Format | Key | Evidence | Cite | CSV evidence |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | TRANSACTION_ID | RAW_BANK.TXN_FEED_20240131.TRANSACTION_ID | carried from RAW_BANK.TXN_FEED_20240131.TRANSACTION_ID | — | yes | INFERRED | Programs/Banking/daily_transaction_processing.sas:107 | Data/csv/raw_bank/TXN_FEED_20240131.csv::TRANSACTION_ID=T000000001 |
| 2 | ACCOUNT_ID | RAW_BANK.TXN_FEED_20240131.ACCOUNT_ID | carried from RAW_BANK.TXN_FEED_20240131.ACCOUNT_ID | — | yes | INFERRED | Programs/Banking/daily_transaction_processing.sas:107 | Data/csv/raw_bank/TXN_FEED_20240131.csv::ACCOUNT_ID=A00000004 |
| 3 | TRANSACTION_DATE | RAW_BANK.TXN_FEED_20240131.TRANSACTION_DATE | carried from RAW_BANK.TXN_FEED_20240131.TRANSACTION_DATE | — | yes | INFERRED | Programs/Banking/daily_transaction_processing.sas:107 | Data/csv/raw_bank/TXN_FEED_20240131.csv::TRANSACTION_DATE=31JAN2024 |
| 4 | TRANSACTION_TYPE | RAW_BANK.TXN_FEED_20240131.TRANSACTION_TYPE | carried from RAW_BANK.TXN_FEED_20240131.TRANSACTION_TYPE | — | no | INFERRED | Programs/Banking/daily_transaction_processing.sas:107 | Data/csv/raw_bank/TXN_FEED_20240131.csv::TRANSACTION_TYPE=REF |
| 5 | TRANSACTION_AMOUNT | RAW_BANK.TXN_FEED_20240131.TRANSACTION_AMOUNT | carried from RAW_BANK.TXN_FEED_20240131.TRANSACTION_AMOUNT | — | no | INFERRED | Programs/Banking/daily_transaction_processing.sas:107 | Data/csv/raw_bank/TXN_FEED_20240131.csv::TRANSACTION_AMOUNT=1804.93 |
| 6 | CHANNEL | RAW_BANK.TXN_FEED_20240131.CHANNEL | carried from RAW_BANK.TXN_FEED_20240131.CHANNEL | — | no | INFERRED | Programs/Banking/daily_transaction_processing.sas:107 | Data/csv/raw_bank/TXN_FEED_20240131.csv::CHANNEL=WIRE |
| 7 | MERCHANT_CATEGORY | RAW_BANK.TXN_FEED_20240131.MERCHANT_CATEGORY | carried from RAW_BANK.TXN_FEED_20240131.MERCHANT_CATEGORY | — | no | INFERRED | Programs/Banking/daily_transaction_processing.sas:107 | Data/csv/raw_bank/TXN_FEED_20240131.csv::MERCHANT_CATEGORY=4900 |
| 8 | DESCRIPTION | RAW_BANK.TXN_FEED_20240131.DESCRIPTION | carried from RAW_BANK.TXN_FEED_20240131.DESCRIPTION | — | no | INFERRED | Programs/Banking/daily_transaction_processing.sas:107 | Data/csv/raw_bank/TXN_FEED_20240131.csv::DESCRIPTION=REF MOBILE REF714480 |
| 9 | POST_DATE | RAW_BANK.TXN_FEED_20240131.POST_DATE | carried from RAW_BANK.TXN_FEED_20240131.POST_DATE | — | no | INFERRED | Programs/Banking/daily_transaction_processing.sas:107 | Data/csv/raw_bank/TXN_FEED_20240131.csv::POST_DATE=31JAN2024 |
| 10 | CURRENCY_CODE | RAW_BANK.TXN_FEED_20240131.CURRENCY_CODE | carried from RAW_BANK.TXN_FEED_20240131.CURRENCY_CODE | — | no | INFERRED | Programs/Banking/daily_transaction_processing.sas:107 | Data/csv/raw_bank/TXN_FEED_20240131.csv::CURRENCY_CODE=USD |
| 11 | ACCOUNT_TYPE | STG_BANK.CUST_ACCOUNTS_DAILY.ACCOUNT_TYPE | carried from STG_BANK.CUST_ACCOUNTS_DAILY.ACCOUNT_TYPE | — | no | INFERRED | Programs/Banking/daily_transaction_processing.sas:107 | — |
| 12 | CUSTOMER_ID | STG_BANK.CUST_ACCOUNTS_DAILY.CUSTOMER_ID | carried from STG_BANK.CUST_ACCOUNTS_DAILY.CUSTOMER_ID | — | no | INFERRED | Programs/Banking/daily_transaction_processing.sas:107 | — |
| 13 | CUSTOMER_SEGMENT | STG_BANK.CUST_ACCOUNTS_DAILY.CUSTOMER_SEGMENT | carried from STG_BANK.CUST_ACCOUNTS_DAILY.CUSTOMER_SEGMENT | — | no | INFERRED | Programs/Banking/daily_transaction_processing.sas:107 | — |
| 14 | REGION_CODE | STG_BANK.CUST_ACCOUNTS_DAILY.REGION_CODE | carried from STG_BANK.CUST_ACCOUNTS_DAILY.REGION_CODE | — | no | INFERRED | Programs/Banking/daily_transaction_processing.sas:107 | — |
| 15 | BRANCH_ID | STG_BANK.CUST_ACCOUNTS_DAILY.BRANCH_ID | carried from STG_BANK.CUST_ACCOUNTS_DAILY.BRANCH_ID | — | no | INFERRED | Programs/Banking/daily_transaction_processing.sas:107 | — |
| 16 | PRE_TXN_BALANCE | a.CURRENT_BALANCE as PRE_TXN_BALANCE | num | DOLLAR18.2 | no | FACT | Programs/Banking/daily_transaction_processing.sas:114 | — |
| 17 | POST_TXN_BALANCE | case ... end as POST_TXN_BALANCE | num | DOLLAR18.2 | no | FACT | Programs/Banking/daily_transaction_processing.sas:123 | — |
| 18 | RISK_RATING | STG_BANK.CUST_ACCOUNTS_DAILY.RISK_RATING | carried from STG_BANK.CUST_ACCOUNTS_DAILY.RISK_RATING | — | no | INFERRED | Programs/Banking/daily_transaction_processing.sas:124 | — |
| 19 | RUNNING_BALANCE | RUNNING_BALANCE = PRE_TXN_BALANCE + signed TRANSACTION_AMOUNT | num | DOLLAR18.2 | no | FACT | Programs/Banking/daily_transaction_processing.sas:141 | — |
| 20 | AVG_TXN_AMT | mean(abs(TRANSACTION_AMOUNT)) as AVG_TXN_AMT | num (aggregate) | — | no | FACT | Programs/Banking/daily_transaction_processing.sas:163 | — |
| 21 | STD_TXN_AMT | std(abs(TRANSACTION_AMOUNT)) as STD_TXN_AMT | num (aggregate) | — | no | FACT | Programs/Banking/daily_transaction_processing.sas:164 | — |
| 22 | Z_SCORE | (abs(e.TRANSACTION_AMOUNT) - s.AVG_TXN_AMT) / s.STD_TXN_AMT | num | — | no | FACT | Programs/Banking/daily_transaction_processing.sas:182 | — |
| 23 | ANOMALY_TYPE | case ... end as ANOMALY_TYPE | char$20 | — | no | FACT | Programs/Banking/daily_transaction_processing.sas:191 | — |

### WORK.TXN_REJECTED

Created/appended by: Programs/Banking/daily_transaction_processing.sas:45

| # | Column | Expression/source | SAS type | Format | Key | Evidence | Cite | CSV evidence |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | TRANSACTION_ID | RAW_BANK.TXN_FEED_20240131.TRANSACTION_ID | carried from RAW_BANK.TXN_FEED_20240131.TRANSACTION_ID | — | no | INFERRED | Programs/Banking/daily_transaction_processing.sas:37 | Data/csv/raw_bank/TXN_FEED_20240131.csv::TRANSACTION_ID=T000000001 |
| 2 | ACCOUNT_ID | RAW_BANK.TXN_FEED_20240131.ACCOUNT_ID | carried from RAW_BANK.TXN_FEED_20240131.ACCOUNT_ID | — | no | INFERRED | Programs/Banking/daily_transaction_processing.sas:37 | Data/csv/raw_bank/TXN_FEED_20240131.csv::ACCOUNT_ID=A00000004 |
| 3 | TRANSACTION_DATE | RAW_BANK.TXN_FEED_20240131.TRANSACTION_DATE | carried from RAW_BANK.TXN_FEED_20240131.TRANSACTION_DATE | — | no | INFERRED | Programs/Banking/daily_transaction_processing.sas:37 | Data/csv/raw_bank/TXN_FEED_20240131.csv::TRANSACTION_DATE=31JAN2024 |
| 4 | TRANSACTION_TYPE | RAW_BANK.TXN_FEED_20240131.TRANSACTION_TYPE | carried from RAW_BANK.TXN_FEED_20240131.TRANSACTION_TYPE | — | no | INFERRED | Programs/Banking/daily_transaction_processing.sas:37 | Data/csv/raw_bank/TXN_FEED_20240131.csv::TRANSACTION_TYPE=REF |
| 5 | TRANSACTION_AMOUNT | RAW_BANK.TXN_FEED_20240131.TRANSACTION_AMOUNT | carried from RAW_BANK.TXN_FEED_20240131.TRANSACTION_AMOUNT | — | no | INFERRED | Programs/Banking/daily_transaction_processing.sas:37 | Data/csv/raw_bank/TXN_FEED_20240131.csv::TRANSACTION_AMOUNT=1804.93 |
| 6 | CHANNEL | RAW_BANK.TXN_FEED_20240131.CHANNEL | carried from RAW_BANK.TXN_FEED_20240131.CHANNEL | — | no | INFERRED | Programs/Banking/daily_transaction_processing.sas:37 | Data/csv/raw_bank/TXN_FEED_20240131.csv::CHANNEL=WIRE |
| 7 | MERCHANT_CATEGORY | RAW_BANK.TXN_FEED_20240131.MERCHANT_CATEGORY | carried from RAW_BANK.TXN_FEED_20240131.MERCHANT_CATEGORY | — | no | INFERRED | Programs/Banking/daily_transaction_processing.sas:37 | Data/csv/raw_bank/TXN_FEED_20240131.csv::MERCHANT_CATEGORY=4900 |
| 8 | DESCRIPTION | RAW_BANK.TXN_FEED_20240131.DESCRIPTION | carried from RAW_BANK.TXN_FEED_20240131.DESCRIPTION | — | no | INFERRED | Programs/Banking/daily_transaction_processing.sas:37 | Data/csv/raw_bank/TXN_FEED_20240131.csv::DESCRIPTION=REF MOBILE REF714480 |
| 9 | POST_DATE | RAW_BANK.TXN_FEED_20240131.POST_DATE | carried from RAW_BANK.TXN_FEED_20240131.POST_DATE | — | no | INFERRED | Programs/Banking/daily_transaction_processing.sas:37 | Data/csv/raw_bank/TXN_FEED_20240131.csv::POST_DATE=31JAN2024 |
| 10 | CURRENCY_CODE | RAW_BANK.TXN_FEED_20240131.CURRENCY_CODE | carried from RAW_BANK.TXN_FEED_20240131.CURRENCY_CODE | — | no | INFERRED | Programs/Banking/daily_transaction_processing.sas:37 | Data/csv/raw_bank/TXN_FEED_20240131.csv::CURRENCY_CODE=USD |
| 11 | REJECT_REASON | length REJECT_REASON $200 | char$200 | — | no | FACT | Programs/Banking/daily_transaction_processing.sas:50 | — |

Note: Reject dataset is created by the two-target DATA step and removed in cleanup; it is not appended to a permanent table.

### CURATED.RISK_SCORES

Created/appended by: Programs/Banking/credit_risk_scoring.sas:231

| # | Column | Expression/source | SAS type | Format | Key | Evidence | Cite | CSV evidence |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | ACCOUNT_ID | STG_BANK.CUST_ACCOUNTS_DAILY.ACCOUNT_ID | carried from STG_BANK.CUST_ACCOUNTS_DAILY.ACCOUNT_ID | — | yes | INFERRED | Programs/Banking/credit_risk_scoring.sas:34 | — |
| 2 | CUSTOMER_ID | STG_BANK.CUST_ACCOUNTS_DAILY.CUSTOMER_ID | carried from STG_BANK.CUST_ACCOUNTS_DAILY.CUSTOMER_ID | — | yes | INFERRED | Programs/Banking/credit_risk_scoring.sas:34 | — |
| 3 | ACCOUNT_TYPE | STG_BANK.CUST_ACCOUNTS_DAILY.ACCOUNT_TYPE | carried from STG_BANK.CUST_ACCOUNTS_DAILY.ACCOUNT_TYPE | — | no | INFERRED | Programs/Banking/credit_risk_scoring.sas:34 | — |
| 4 | CURRENT_BALANCE | STG_BANK.CUST_ACCOUNTS_DAILY.CURRENT_BALANCE | carried from STG_BANK.CUST_ACCOUNTS_DAILY.CURRENT_BALANCE | — | no | INFERRED | Programs/Banking/credit_risk_scoring.sas:34 | — |
| 5 | CREDIT_LIMIT | STG_BANK.CUST_ACCOUNTS_DAILY.CREDIT_LIMIT | carried from STG_BANK.CUST_ACCOUNTS_DAILY.CREDIT_LIMIT | — | no | INFERRED | Programs/Banking/credit_risk_scoring.sas:34 | — |
| 6 | ACCT_AGE_MONTHS | STG_BANK.CUST_ACCOUNTS_DAILY.ACCT_AGE_MONTHS | carried from STG_BANK.CUST_ACCOUNTS_DAILY.ACCT_AGE_MONTHS | — | no | INFERRED | Programs/Banking/credit_risk_scoring.sas:34 | — |
| 7 | DAYS_INACTIVE | STG_BANK.CUST_ACCOUNTS_DAILY.DAYS_INACTIVE | carried from STG_BANK.CUST_ACCOUNTS_DAILY.DAYS_INACTIVE | — | no | INFERRED | Programs/Banking/credit_risk_scoring.sas:34 | — |
| 8 | UTILIZATION_PCT | STG_BANK.CUST_ACCOUNTS_DAILY.UTILIZATION_PCT | carried from STG_BANK.CUST_ACCOUNTS_DAILY.UTILIZATION_PCT | — | no | INFERRED | Programs/Banking/credit_risk_scoring.sas:34 | — |
| 9 | CUSTOMER_SEGMENT | STG_BANK.CUST_ACCOUNTS_DAILY.CUSTOMER_SEGMENT | carried from STG_BANK.CUST_ACCOUNTS_DAILY.CUSTOMER_SEGMENT | — | no | INFERRED | Programs/Banking/credit_risk_scoring.sas:34 | — |
| 10 | REGION_CODE | STG_BANK.CUST_ACCOUNTS_DAILY.REGION_CODE | carried from STG_BANK.CUST_ACCOUNTS_DAILY.REGION_CODE | — | no | INFERRED | Programs/Banking/credit_risk_scoring.sas:34 | — |
| 11 | FICO_SCORE | ORA_DW.BUREAU_SCORES.FICO_SCORE | carried from ORA_DW.BUREAU_SCORES.FICO_SCORE | — | no | INFERRED | Programs/Banking/credit_risk_scoring.sas:34 | Data/csv/oracle_dw/BUREAU_SCORES.csv::FICO_SCORE=538 |
| 12 | VANTAGE_SCORE | ORA_DW.BUREAU_SCORES.VANTAGE_SCORE | carried from ORA_DW.BUREAU_SCORES.VANTAGE_SCORE | — | no | INFERRED | Programs/Banking/credit_risk_scoring.sas:34 | Data/csv/oracle_dw/BUREAU_SCORES.csv::VANTAGE_SCORE=518 |
| 13 | BUREAU_INQS_6MO | ORA_DW.BUREAU_SCORES.BUREAU_INQS_6MO | carried from ORA_DW.BUREAU_SCORES.BUREAU_INQS_6MO | — | no | INFERRED | Programs/Banking/credit_risk_scoring.sas:34 | Data/csv/oracle_dw/BUREAU_SCORES.csv::BUREAU_INQS_6MO=0 |
| 14 | BUREAU_TRADES_OPEN | ORA_DW.BUREAU_SCORES.BUREAU_TRADES_OPEN | carried from ORA_DW.BUREAU_SCORES.BUREAU_TRADES_OPEN | — | no | INFERRED | Programs/Banking/credit_risk_scoring.sas:34 | Data/csv/oracle_dw/BUREAU_SCORES.csv::BUREAU_TRADES_OPEN=23 |
| 15 | BUREAU_DEROGS | ORA_DW.BUREAU_SCORES.BUREAU_DEROGS | carried from ORA_DW.BUREAU_SCORES.BUREAU_DEROGS | — | no | INFERRED | Programs/Banking/credit_risk_scoring.sas:34 | Data/csv/oracle_dw/BUREAU_SCORES.csv::BUREAU_DEROGS=0 |
| 16 | BUREAU_UTIL_PCT | ORA_DW.BUREAU_SCORES.BUREAU_UTIL_PCT | carried from ORA_DW.BUREAU_SCORES.BUREAU_UTIL_PCT | — | no | INFERRED | Programs/Banking/credit_risk_scoring.sas:34 | Data/csv/oracle_dw/BUREAU_SCORES.csv::BUREAU_UTIL_PCT=14.46 |
| 17 | BUREAU_OLDEST_TRADE_MO | ORA_DW.BUREAU_SCORES.BUREAU_OLDEST_TRADE_MO | carried from ORA_DW.BUREAU_SCORES.BUREAU_OLDEST_TRADE_MO | — | no | INFERRED | Programs/Banking/credit_risk_scoring.sas:34 | Data/csv/oracle_dw/BUREAU_SCORES.csv::BUREAU_OLDEST_TRADE_MO=167 |
| 18 | PMT_ONTIME_12MO | ORA_DW.PAYMENT_HISTORY.PMT_ONTIME_12MO | carried from ORA_DW.PAYMENT_HISTORY.PMT_ONTIME_12MO | — | no | INFERRED | Programs/Banking/credit_risk_scoring.sas:34 | Data/csv/oracle_dw/PAYMENT_HISTORY.csv::PMT_ONTIME_12MO=7 |
| 19 | PMT_LATE_30_12MO | ORA_DW.PAYMENT_HISTORY.PMT_LATE_30_12MO | carried from ORA_DW.PAYMENT_HISTORY.PMT_LATE_30_12MO | — | no | INFERRED | Programs/Banking/credit_risk_scoring.sas:34 | Data/csv/oracle_dw/PAYMENT_HISTORY.csv::PMT_LATE_30_12MO=5 |
| 20 | PMT_LATE_60_12MO | ORA_DW.PAYMENT_HISTORY.PMT_LATE_60_12MO | carried from ORA_DW.PAYMENT_HISTORY.PMT_LATE_60_12MO | — | no | INFERRED | Programs/Banking/credit_risk_scoring.sas:34 | Data/csv/oracle_dw/PAYMENT_HISTORY.csv::PMT_LATE_60_12MO=3 |
| 21 | PMT_LATE_90_12MO | ORA_DW.PAYMENT_HISTORY.PMT_LATE_90_12MO | carried from ORA_DW.PAYMENT_HISTORY.PMT_LATE_90_12MO | — | no | INFERRED | Programs/Banking/credit_risk_scoring.sas:34 | Data/csv/oracle_dw/PAYMENT_HISTORY.csv::PMT_LATE_90_12MO=1 |
| 22 | MAX_DAYS_PAST_DUE_EVER | ORA_DW.PAYMENT_HISTORY.MAX_DAYS_PAST_DUE_EVER | carried from ORA_DW.PAYMENT_HISTORY.MAX_DAYS_PAST_DUE_EVER | — | no | INFERRED | Programs/Banking/credit_risk_scoring.sas:34 | Data/csv/oracle_dw/PAYMENT_HISTORY.csv::MAX_DAYS_PAST_DUE_EVER=91 |
| 23 | MONTHS_SINCE_LAST_DPD | ORA_DW.PAYMENT_HISTORY.MONTHS_SINCE_LAST_DPD | carried from ORA_DW.PAYMENT_HISTORY.MONTHS_SINCE_LAST_DPD | — | no | INFERRED | Programs/Banking/credit_risk_scoring.sas:34 | Data/csv/oracle_dw/PAYMENT_HISTORY.csv::MONTHS_SINCE_LAST_DPD=13 |
| 24 | AVG_PMT_RATIO_12MO | ORA_DW.PAYMENT_HISTORY.AVG_PMT_RATIO_12MO | carried from ORA_DW.PAYMENT_HISTORY.AVG_PMT_RATIO_12MO | — | no | INFERRED | Programs/Banking/credit_risk_scoring.sas:34 | Data/csv/oracle_dw/PAYMENT_HISTORY.csv::AVG_PMT_RATIO_12MO=0.6016 |
| 25 | COLLATERAL_VALUE | ORA_DW.COLLATERAL.COLLATERAL_VALUE | carried from ORA_DW.COLLATERAL.COLLATERAL_VALUE | — | no | INFERRED | Programs/Banking/credit_risk_scoring.sas:34 | Data/csv/oracle_dw/COLLATERAL.csv::COLLATERAL_VALUE=592503.16 |
| 26 | LAST_APPRAISAL_DATE | ORA_DW.COLLATERAL.LAST_APPRAISAL_DATE | carried from ORA_DW.COLLATERAL.LAST_APPRAISAL_DATE | — | no | INFERRED | Programs/Banking/credit_risk_scoring.sas:34 | Data/csv/oracle_dw/COLLATERAL.csv::LAST_APPRAISAL_DATE=26DEC2023 |
| 27 | LTV | case when c.COLLATERAL_VALUE > 0 then ... end as LTV | num | 8.4 | no | FACT | Programs/Banking/credit_risk_scoring.sas:71 | — |
| 28 | PD | 1 / (1 + exp(-LOG_ODDS)) | num | PERCENT8.4 | no | FACT | Programs/Banking/credit_risk_scoring.sas:122 | — |
| 29 | LGD | max(0, min(1, (LTV - 0.5) * 0.8)) | num | PERCENT8.4 | no | FACT | Programs/Banking/credit_risk_scoring.sas:163 | — |
| 30 | EAD | CURRENT_BALANCE + 0.50 * (CREDIT_LIMIT - CURRENT_BALANCE) | num | DOLLAR18.2 | no | FACT | Programs/Banking/credit_risk_scoring.sas:173 | — |
| 31 | EXPECTED_LOSS | PD * LGD * EAD | num | DOLLAR18.2 | no | FACT | Programs/Banking/credit_risk_scoring.sas:179 | — |
| 32 | NEW_RISK_RATING | 7-way PD threshold assignment | num | — | no | FACT | Programs/Banking/credit_risk_scoring.sas:183 | — |
| 33 | SCORE_DATE | "&score_date"d | num (SAS date) | DATE9. | no | FACT | Programs/Banking/credit_risk_scoring.sas:76 | — |
| 34 | MODEL_ID | "&model_id" | char$UNKNOWN | — | no | FACT | Programs/Banking/credit_risk_scoring.sas:192 | — |
| 35 | SCORE_TIMESTAMP | datetime() | num (SAS datetime) | DATETIME20. | no | FACT | Programs/Banking/credit_risk_scoring.sas:193 | — |

### CURATED.RISK_MIGRATION

Created/appended by: Programs/Banking/credit_risk_scoring.sas:238

| # | Column | Expression/source | SAS type | Format | Key | Evidence | Cite | CSV evidence |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | SCORE_DATE | "&score_date"d as SCORE_DATE | num (SAS date) | DATE9. | no | FACT | Programs/Banking/credit_risk_scoring.sas:205 | — |
| 2 | ACCOUNT_ID | STG_BANK.CUST_ACCOUNTS_DAILY.ACCOUNT_ID | carried from STG_BANK.CUST_ACCOUNTS_DAILY.ACCOUNT_ID | — | yes | INFERRED | Programs/Banking/credit_risk_scoring.sas:219 | — |
| 3 | PREV_RATING | STG_BANK.CUST_ACCOUNTS_DAILY.RISK_RATING | carried from STG_BANK.CUST_ACCOUNTS_DAILY.RISK_RATING | — | no | INFERRED | Programs/Banking/credit_risk_scoring.sas:207 | — |
| 4 | CURR_RATING | CURATED.RISK_SCORES.NEW_RISK_RATING | carried from CURATED.RISK_SCORES.NEW_RISK_RATING | — | no | INFERRED | Programs/Banking/credit_risk_scoring.sas:208 | — |
| 5 | MIGRATION_DIRECTION | case ... end as MIGRATION_DIRECTION | char$10 | — | no | FACT | Programs/Banking/credit_risk_scoring.sas:214 | — |
| 6 | PD | CURATED.RISK_SCORES.PD | carried from CURATED.RISK_SCORES.PD | — | no | INFERRED | Programs/Banking/credit_risk_scoring.sas:215 | — |
| 7 | EXPECTED_LOSS | CURATED.RISK_SCORES.EXPECTED_LOSS | carried from CURATED.RISK_SCORES.EXPECTED_LOSS | — | no | INFERRED | Programs/Banking/credit_risk_scoring.sas:216 | — |

### REPORTS.RISK_SUMMARY

Created/appended by: Programs/Banking/credit_risk_scoring.sas:249

| # | Column | Expression/source | SAS type | Format | Key | Evidence | Cite | CSV evidence |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | ACCOUNT_TYPE | CURATED.RISK_SCORES.ACCOUNT_TYPE | carried from CURATED.RISK_SCORES.ACCOUNT_TYPE | — | no | INFERRED | Programs/Banking/credit_risk_scoring.sas:247 | — |
| 2 | NEW_RISK_RATING | CURATED.RISK_SCORES.NEW_RISK_RATING | carried from CURATED.RISK_SCORES.NEW_RISK_RATING | — | no | INFERRED | Programs/Banking/credit_risk_scoring.sas:247 | — |
| 3 | N_ACCOUNTS | n=N_ACCOUNTS | num | — | no | FACT | Programs/Banking/credit_risk_scoring.sas:250 | — |
| 4 | AVG_PD | mean(PD)=AVG_PD | num (aggregate) | — | no | FACT | Programs/Banking/credit_risk_scoring.sas:251 | — |
| 5 | AVG_LGD | mean(LGD)=AVG_LGD | num (aggregate) | — | no | FACT | Programs/Banking/credit_risk_scoring.sas:252 | — |
| 6 | TOTAL_EAD | sum(EAD)=TOTAL_EAD | num (aggregate) | — | no | FACT | Programs/Banking/credit_risk_scoring.sas:253 | — |
| 7 | TOTAL_EL | sum(EXPECTED_LOSS)=TOTAL_EL | num (aggregate) | — | no | FACT | Programs/Banking/credit_risk_scoring.sas:254 | — |

### REPORTS.MONTHLY_RWA

Created/appended by: Programs/Banking/monthly_regulatory_reporting.sas:41

| # | Column | Expression/source | SAS type | Format | Key | Evidence | Cite | CSV evidence |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | REPORT_MONTH | "&report_month" as REPORT_MONTH | char$6 | — | no | FACT | Programs/Banking/monthly_regulatory_reporting.sas:43 | — |
| 2 | ACCOUNT_TYPE | STG_BANK.CUST_ACCOUNTS_DAILY.ACCOUNT_TYPE | carried from STG_BANK.CUST_ACCOUNTS_DAILY.ACCOUNT_TYPE | — | yes | INFERRED | Programs/Banking/monthly_regulatory_reporting.sas:44 | — |
| 3 | CUSTOMER_SEGMENT | STG_BANK.CUST_ACCOUNTS_DAILY.CUSTOMER_SEGMENT | carried from STG_BANK.CUST_ACCOUNTS_DAILY.CUSTOMER_SEGMENT | — | yes | INFERRED | Programs/Banking/monthly_regulatory_reporting.sas:45 | — |
| 4 | RISK_WEIGHT | case when ACCOUNT_TYPE ... end as RISK_WEIGHT | num | — | no | FACT | Programs/Banking/monthly_regulatory_reporting.sas:56 | — |
| 5 | N_ACCOUNTS | count(*) as N_ACCOUNTS | num | — | no | FACT | Programs/Banking/monthly_regulatory_reporting.sas:57 | — |
| 6 | TOTAL_EXPOSURE | sum(CURRENT_BALANCE) as TOTAL_EXPOSURE | num (aggregate) | DOLLAR20.2 | no | FACT | Programs/Banking/monthly_regulatory_reporting.sas:58 | — |
| 7 | RWA | sum(CURRENT_BALANCE * calculated RISK_WEIGHT) as RWA | num (aggregate) | DOLLAR20.2 | no | FACT | Programs/Banking/monthly_regulatory_reporting.sas:59 | — |

### REPORTS.DELINQUENCY_AGING

Created/appended by: Programs/Banking/monthly_regulatory_reporting.sas:73

| # | Column | Expression/source | SAS type | Format | Key | Evidence | Cite | CSV evidence |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | REPORT_MONTH | "&report_month" as REPORT_MONTH | char$6 | — | no | FACT | Programs/Banking/monthly_regulatory_reporting.sas:43 | — |
| 2 | ACCOUNT_TYPE | STG_BANK.CUST_ACCOUNTS_DAILY.ACCOUNT_TYPE | carried from STG_BANK.CUST_ACCOUNTS_DAILY.ACCOUNT_TYPE | — | yes | INFERRED | Programs/Banking/monthly_regulatory_reporting.sas:44 | — |
| 3 | REGION_CODE | STG_BANK.CUST_ACCOUNTS_DAILY.REGION_CODE | carried from STG_BANK.CUST_ACCOUNTS_DAILY.REGION_CODE | — | yes | INFERRED | Programs/Banking/monthly_regulatory_reporting.sas:77 | — |
| 4 | DELINQ_BUCKET | case when DAYS_PAST_DUE ... end as DELINQ_BUCKET | char$10 | — | no | FACT | Programs/Banking/monthly_regulatory_reporting.sas:87 | — |
| 5 | N_ACCOUNTS | count(*) as N_ACCOUNTS | num | — | no | FACT | Programs/Banking/monthly_regulatory_reporting.sas:88 | — |
| 6 | TOTAL_BALANCE | sum(CURRENT_BALANCE) as TOTAL_BALANCE | num (aggregate) | DOLLAR20.2 | no | FACT | Programs/Banking/monthly_regulatory_reporting.sas:89 | — |
| 7 | TOTAL_PAST_DUE | sum(PAST_DUE_AMOUNT) as TOTAL_PAST_DUE | num (aggregate) | DOLLAR20.2 | no | FACT | Programs/Banking/monthly_regulatory_reporting.sas:90 | — |

### REPORTS.LLP_COVERAGE

Created/appended by: Programs/Banking/monthly_regulatory_reporting.sas:115

| # | Column | Expression/source | SAS type | Format | Key | Evidence | Cite | CSV evidence |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | REPORT_MONTH | "&report_month" as REPORT_MONTH | char$6 | — | no | FACT | Programs/Banking/monthly_regulatory_reporting.sas:43 | — |
| 2 | ACCOUNT_TYPE | STG_BANK.CUST_ACCOUNTS_DAILY.ACCOUNT_TYPE | carried from STG_BANK.CUST_ACCOUNTS_DAILY.ACCOUNT_TYPE | — | yes | INFERRED | Programs/Banking/monthly_regulatory_reporting.sas:118 | — |
| 3 | N_LOANS | count(*) as N_LOANS | num | — | no | FACT | Programs/Banking/monthly_regulatory_reporting.sas:119 | — |
| 4 | GROSS_LOANS | sum(a.CURRENT_BALANCE) as GROSS_LOANS | num (aggregate) | DOLLAR20.2 | no | FACT | Programs/Banking/monthly_regulatory_reporting.sas:120 | — |
| 5 | TOTAL_ALLOWANCE | sum(l.ALLOWANCE_AMT) as TOTAL_ALLOWANCE | num (aggregate) | DOLLAR20.2 | no | FACT | Programs/Banking/monthly_regulatory_reporting.sas:121 | — |
| 6 | COVERAGE_PCT | sum(l.ALLOWANCE_AMT) / sum(a.CURRENT_BALANCE) * 100 | num | 8.2 | no | FACT | Programs/Banking/monthly_regulatory_reporting.sas:126 | — |
| 7 | NPL_BALANCE | sum(case when l.DAYS_PAST_DUE >= 90 then ... end) | num (aggregate) | DOLLAR20.2 | no | FACT | Programs/Banking/monthly_regulatory_reporting.sas:128 | — |
| 8 | NPL_COVERAGE_PCT | sum(l.ALLOWANCE_AMT) / calculated NPL_BALANCE * 100 | num | 8.2 | no | FACT | Programs/Banking/monthly_regulatory_reporting.sas:133 | — |

### REPORTS.CAPITAL_ADEQUACY

Created/appended by: Programs/Banking/monthly_regulatory_reporting.sas:170

| # | Column | Expression/source | SAS type | Format | Key | Evidence | Cite | CSV evidence |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | REPORT_MONTH | "&report_month" as REPORT_MONTH | char$6 | — | no | FACT | Programs/Banking/monthly_regulatory_reporting.sas:43 | — |
| 2 | TOTAL_RWA | sum(RWA) as TOTAL_RWA | num (aggregate) | DOLLAR20.2 | no | FACT | Programs/Banking/monthly_regulatory_reporting.sas:173 | — |
| 3 | CET1_CAPITAL | 50000000 as CET1_CAPITAL | num | DOLLAR20.2 | no | FACT | Programs/Banking/monthly_regulatory_reporting.sas:175 | — |
| 4 | TIER1_CAPITAL | 65000000 as TIER1_CAPITAL | num | DOLLAR20.2 | no | FACT | Programs/Banking/monthly_regulatory_reporting.sas:176 | — |
| 5 | TOTAL_CAPITAL | 80000000 as TOTAL_CAPITAL | num | DOLLAR20.2 | no | FACT | Programs/Banking/monthly_regulatory_reporting.sas:177 | — |
| 6 | CET1_RATIO | 50000000 / sum(RWA) * 100 | num | 8.2 | no | FACT | Programs/Banking/monthly_regulatory_reporting.sas:178 | — |
| 7 | TIER1_RATIO | 65000000 / sum(RWA) * 100 | num | 8.2 | no | FACT | Programs/Banking/monthly_regulatory_reporting.sas:179 | — |
| 8 | TOTAL_CAPITAL_RATIO | 80000000 / sum(RWA) * 100 | num | 8.2 | no | FACT | Programs/Banking/monthly_regulatory_reporting.sas:180 | — |
| 9 | CET1_STATUS | case ... then 'PASS' else 'FAIL' end | char$4 | — | no | FACT | Programs/Banking/monthly_regulatory_reporting.sas:183 | — |
| 10 | TIER1_STATUS | case ... then 'PASS' else 'FAIL' end | char$4 | — | no | FACT | Programs/Banking/monthly_regulatory_reporting.sas:185 | — |
| 11 | TOTAL_CAPITAL_STATUS | case ... then 'PASS' else 'FAIL' end | char$4 | — | no | FACT | Programs/Banking/monthly_regulatory_reporting.sas:187 | — |

### ARCHIVE.BATCH_HISTORY

Created/appended by: BatchJobs/run_daily_banking.sas:142

| # | Column | Expression/source | SAS type | Format | Key | Evidence | Cite | CSV evidence |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | BATCH_ID | "&batch_id" | char$60 | — | no | FACT | BatchJobs/run_daily_banking.sas:32 | — |
| 2 | STEP_NUM | &step_num | num | — | no | FACT | BatchJobs/run_daily_banking.sas:32 | — |
| 3 | STEP_NAME | "&step_name" | char$50 | — | no | FACT | BatchJobs/run_daily_banking.sas:32 | — |
| 4 | PROGRAM_PATH | "&program" | char$200 | — | no | FACT | BatchJobs/run_daily_banking.sas:32 | — |
| 5 | STATUS | ifc(&step_rc = 0, "PASS", "FAIL") | char$10 | — | no | FACT | BatchJobs/run_daily_banking.sas:33 | — |
| 6 | START_TIME | &step_start | num (SAS datetime) | DATETIME20. | no | FACT | BatchJobs/run_daily_banking.sas:34 | — |
| 7 | END_TIME | %sysfunc(datetime()) | num (SAS datetime) | DATETIME20. | no | FACT | BatchJobs/run_daily_banking.sas:34 | — |
| 8 | DURATION | %sysevalf(%sysfunc(datetime()) - &step_start) | num (SAS time) | TIME8. | no | FACT | BatchJobs/run_daily_banking.sas:33 | — |
| 9 | ERROR_MSG | ifc(&step_rc = 0, "", "SYSCC=&step_rc") | char$500 | — | no | FACT | BatchJobs/run_daily_banking.sas:33 | — |

## Per-program runtime evidence

### Programs/Banking/load_customer_accounts.sas

- Autoexec macro variables: CURR_DT, EMAIL_ONCALL
- Round calls: none
- Datetime/today/time calls: datetime() (line 23), datetime() (line 151), datetime() (line 204)
- PROC APPEND: none
- `%lock`: none
- Business-date WHERE: a.ACCOUNT_STATUS not in ('W', 'C') and a.OPEN_DATE <= "&run_date"d %if &regio... (line 62)
- Row-sequential logic: none

### Programs/Banking/daily_transaction_processing.sas

- Autoexec macro variables: CURR_DT
- Round calls: none
- Datetime/today/time calls: datetime() (line 24), datetime() (line 230)
- PROC APPEND: base=CURATED.DAILY_TRANSACTIONS data=WORK.TXN_WITH_BALANCE (line 207), base=CURATED.TXN_ANOMALIES data=WORK.TXN_ANOMALIES (line 214)
- `%lock`: %lock(CURATED.DAILY_TRANSACTIONS) (line 205), %lock(CURATED.DAILY_TRANSACTIONS, unlock) (line 211)
- Business-date WHERE: TRANSACTION_DATE >= intnx('day', "&txn_date"d, -90) (line 167)
- Row-sequential logic:
  - by: `by ACCOUNT_ID TRANSACTION_DATE TRANSACTION_ID;` (line 139)
  - retain: `retain RUNNING_BALANCE;` (line 140)
  - first.: `first.ACCOUNT_ID` (line 143)

### Programs/Banking/credit_risk_scoring.sas

- Autoexec macro variables: CURR_DT
- Round calls: none
- Datetime/today/time calls: datetime() (line 193)
- PROC APPEND: base=CURATED.RISK_SCORES data=WORK.SCORED (line 231), base=CURATED.RISK_MIGRATION data=WORK.RISK_MIGRATION (line 238)
- `%lock`: %lock(CURATED.RISK_SCORES) (line 229), %lock(CURATED.RISK_SCORES, unlock) (line 234), %lock(CURATED.RISK_MIGRATION) (line 236), %lock(CURATED.RISK_MIGRATION, unlock) (line 241)
- Business-date WHERE: CUSTOMER_ID = b.CUSTOMER_ID and SCORE_DATE <= "&score_date"d) left join ORA_D... (line 77), a.SNAPSHOT_DATE = "&score_date"d and (a.RISK_RATING ne s.NEW_RISK_RATING or a... (line 220)
- Row-sequential logic: none

### Programs/Banking/monthly_regulatory_reporting.sas

- Autoexec macro variables: PREV_YM, REPORT_PATH
- Round calls: none
- Datetime/today/time calls: none
- PROC APPEND: none
- `%lock`: none
- Business-date WHERE: a.SNAPSHOT_DATE = "&month_end"d (line 63), a.SNAPSHOT_DATE = "&month_end"d and a.ACCOUNT_TYPE in ('MTG','AUTO','PERS','C... (line 94), a.SNAPSHOT_DATE = "&month_end"d and a.ACCOUNT_TYPE in ('MTG','AUTO','PERS','C... (line 137)
- Row-sequential logic: none

### BatchJobs/run_daily_banking.sas

- Autoexec macro variables: ABORT_ON_ERR, CURR_DT, EMAIL_DL, EMAIL_ONCALL
- Round calls: none
- Datetime/today/time calls: datetime() (line 15), datetime() (line 16), datetime() (line 59), datetime() (line 89), datetime() (line 90), datetime() (line 149), datetime() (line 156)
- PROC APPEND: base=ARCHIVE.BATCH_HISTORY data=WORK.BATCH_CONTROL (line 142)
- `%lock`: none
- Business-date WHERE: none
- Row-sequential logic: none

## UNKNOWN / limitations

UNKNOWN is retained where the SAS source does not declare a fixed character length or where a macro parameter controls the resulting length. Source-table columns are marked INFERRED and include seeded CSV header/sample evidence when available.
