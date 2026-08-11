/*=====================================================================
  t004_account_snapshot — derived from
  Programs/Banking/load_customer_accounts.sas

  The upstream Step 1 extracts the account base by joining
  ORA_DW.CUST_ACCOUNTS with ORA_DW.CUST_DEMOGRAPHICS (Oracle DW). Those
  libraries are not in the repository, so the extract is replaced here by
  a small inline WORK.ACCT_RAW with the columns Step 2 reads.

  Step 2 — the snapshot DATA step — is reproduced verbatim: it applies
  the repository's banking formats, derives account age, days inactive,
  utilization, dormancy and high-balance flags, and splits out data
  quality exceptions (negative deposit balance, utilization > 95%,
  missing risk rating) to a second output table. Step 4's PROC MEANS
  summary is included as well. (The format catalog is loaded in
  autoexec.sas from the repository's banking_formats.sas value sets.)
=====================================================================*/

%let run_date = 15JAN2024;

/* ---- Step 1 substitute: inline account base (ORA_DW join result) ---- */
data WORK.ACCT_RAW;
  length ACCOUNT_ID $10 CUSTOMER_ID $10 ACCOUNT_TYPE $4 ACCOUNT_STATUS $1
         CUSTOMER_SEGMENT $4 REGION_CODE $2;
  informat OPEN_DATE LAST_ACTIVITY_DATE date9.;
  format OPEN_DATE LAST_ACTIVITY_DATE date9.;
  input ACCOUNT_ID $ CUSTOMER_ID $ ACCOUNT_TYPE $ ACCOUNT_STATUS $
        OPEN_DATE CURRENT_BALANCE CREDIT_LIMIT LAST_ACTIVITY_DATE
        RISK_RATING CUSTOMER_SEGMENT $ REGION_CODE $;
  datalines;
A100001 C0001 CHK  A 15MAR2010   1532.40       0 02JAN2024 2 RET  NE
A100002 C0002 SAV  A 01JUN2018  45200.00       0 28DEC2023 1 PREM SE
A100003 C0003 CC   A 20SEP2021   7890.55    8000 05JAN2024 4 RET  MW
A100004 C0004 MTG  A 10JAN2005 285000.00       0 30DEC2023 3 PB   SW
A100005 C0005 AUTO A 12FEB2016  12750.00       0 11JAN2021 5 SMB  W
A100006 C0006 HELC A 03MAR2014  98500.00  100000 09JAN2024 6 CORP NW
A100007 C0007 CHK  A 18JUL2019   -250.00       0 02JAN2024 2 RET  SW
A100008 C0008 LOC  A 22MAY2020  33000.00   34000 04JAN2024 . COMM HQ
;
run;

  /* ----------------------------------------------------------
     Step 2: Apply Business Rules and Derive Metrics
     ---------------------------------------------------------- */
  data WORK.CUST_ACCOUNTS_DAILY(label="Daily Customer Account Snapshot")
       WORK.ACCT_EXCEPTIONS(label="Account Data Quality Exceptions");

    set WORK.ACCT_RAW;

    format ACCOUNT_TYPE $ACCTTYPE.
           ACCOUNT_STATUS $ACCTSTAT.
           RISK_RATING RISKRATE.
           CUSTOMER_SEGMENT $CUSTSEG.
           REGION_CODE $REGION.
           CURRENT_BALANCE CREDIT_LIMIT
             dollar18.2
           OPEN_DATE LAST_ACTIVITY_DATE date9.
    ;

    length EXCEPTION_CODE $10 EXCEPTION_DESC $200;

    /* Derived: Account age in months */
    ACCT_AGE_MONTHS = intck('month', OPEN_DATE, "&run_date"d);

    /* Derived: Days since last activity */
    DAYS_INACTIVE = "&run_date"d - LAST_ACTIVITY_DATE;

    /* Derived: Utilization ratio for revolving accounts */
    if ACCOUNT_TYPE in ('CC', 'LOC', 'HELC') and CREDIT_LIMIT > 0 then
      UTILIZATION_PCT = (CURRENT_BALANCE / CREDIT_LIMIT) * 100;
    else
      UTILIZATION_PCT = .;

    /* Derived: Dormancy flag */
    if DAYS_INACTIVE > 365 and ACCOUNT_STATUS = 'A' then
      DORMANCY_FLAG = 'Y';
    else
      DORMANCY_FLAG = 'N';

    /* Derived: High-balance flag */
    if CURRENT_BALANCE >= 250000 then
      HIGH_BALANCE_FLAG = 'Y';
    else
      HIGH_BALANCE_FLAG = 'N';

    /* Business Rule: Negative balance on deposit accounts */
    if ACCOUNT_TYPE in ('CHK', 'SAV', 'MMA', 'CD') and CURRENT_BALANCE < 0 then do;
      EXCEPTION_CODE = 'NEG_BAL';
      EXCEPTION_DESC = catx(' ', 'Negative balance',
        put(CURRENT_BALANCE, dollar18.2),
        'on deposit account', ACCOUNT_ID);
      output WORK.ACCT_EXCEPTIONS;
    end;

    /* Business Rule: Credit utilization > 95% */
    if UTILIZATION_PCT > 95 then do;
      EXCEPTION_CODE = 'HIGH_UTIL';
      EXCEPTION_DESC = catx(' ', 'Utilization at',
        put(UTILIZATION_PCT, 5.1), '%',
        'for account', ACCOUNT_ID);
      output WORK.ACCT_EXCEPTIONS;
    end;

    /* Business Rule: Missing risk rating */
    if RISK_RATING = . then do;
      EXCEPTION_CODE = 'NO_RISK';
      EXCEPTION_DESC = catx(' ', 'Missing risk rating for customer',
        CUSTOMER_ID);
      output WORK.ACCT_EXCEPTIONS;
    end;

    /* Snapshot metadata */
    SNAPSHOT_DATE = "&run_date"d;
    format SNAPSHOT_DATE date9.;

    output WORK.CUST_ACCOUNTS_DAILY;

    drop EXCEPTION_CODE EXCEPTION_DESC;
  run;

proc print data=WORK.CUST_ACCOUNTS_DAILY noobs;
  var ACCOUNT_ID ACCOUNT_TYPE ACCOUNT_STATUS RISK_RATING REGION_CODE
      ACCT_AGE_MONTHS DAYS_INACTIVE UTILIZATION_PCT DORMANCY_FLAG
      HIGH_BALANCE_FLAG;
run;

/* The snapshot step ends with `drop EXCEPTION_CODE EXCEPTION_DESC;`,
   which (Base SAS DROP applies to every output data set) removes those
   columns from the exceptions table too, so only the keys are listed.
   Five exception rows are flagged: CC/HELC/LOC for utilization > 95%,
   the negative-balance checking account, and the missing-risk account. */
proc print data=WORK.ACCT_EXCEPTIONS noobs;
  var ACCOUNT_ID ACCOUNT_TYPE CURRENT_BALANCE UTILIZATION_PCT RISK_RATING;
run;

  /* ----------------------------------------------------------
     Step 4: Summary Statistics
     ---------------------------------------------------------- */
  proc means data=WORK.CUST_ACCOUNTS_DAILY noprint nway;
    class ACCOUNT_TYPE REGION_CODE;
    var CURRENT_BALANCE UTILIZATION_PCT ACCT_AGE_MONTHS;
    output out=WORK.ACCT_SUMMARY(drop=_TYPE_ _FREQ_)
      n=N_ACCOUNTS
      sum(CURRENT_BALANCE)=TOTAL_BALANCE
      mean(CURRENT_BALANCE)=AVG_BALANCE
      mean(UTILIZATION_PCT)=AVG_UTILIZATION
      mean(ACCT_AGE_MONTHS)=AVG_AGE_MONTHS
    ;
  run;

proc print data=WORK.ACCT_SUMMARY noobs;
run;
