/*=====================================================================
  t003_txn_running_balance — derived from
  Programs/Banking/daily_transaction_processing.sas

  This bundle exercises two pieces of the daily transaction ETL that
  are pure Base SAS:

    Step 1 — feed validation (the multi-output DATA step that splits
             RAW_BANK.TXN_FEED into WORK.TXN_VALIDATED and
             WORK.TXN_REJECTED with required-field, amount-range,
             transaction-type and future-date checks), verbatim.

    Step 3 — the RETAIN / BY-group running-balance calculation that
             carries a cumulative balance forward within each account,
             verbatim.

  In the upstream program the validated feed is enriched in Step 2 via a
  join to STG_BANK.CUST_ACCOUNTS_DAILY (Oracle-sourced staging). Those
  libraries are not in the repository, so the feed (RAW_BANK.TXN_FEED)
  and the account pre-balances (STG_BANK.CUST_ACCOUNTS_DAILY) are
  supplied here as small inline data sets with the same column shape the
  steps read. The validation and running-balance logic is unchanged.
=====================================================================*/

%let txn_date = 15JAN2024;

/* ---- Inline feed (stands in for RAW_BANK.TXN_FEED_YYYYMMDD) ---- */
data WORK.TXN_FEED;
  length TRANSACTION_ID $12 ACCOUNT_ID $10 TRANSACTION_TYPE $3;
  informat TRANSACTION_DATE date9.;
  format TRANSACTION_DATE date9.;
  input TRANSACTION_ID $ ACCOUNT_ID $ TRANSACTION_TYPE $
        TRANSACTION_AMOUNT TRANSACTION_DATE;
  datalines;
T0000000001 A100001 DEP   500.00 10JAN2024
T0000000002 A100001 WDR   120.00 11JAN2024
T0000000003 A100001 FEE    15.00 12JAN2024
T0000000004 A100002 DEP  2000.00 10JAN2024
T0000000005 A100002 WDR  1800.00 13JAN2024
T0000000006 A100002 INT     6.25 14JAN2024
T0000000007 A100003 PMT   300.00 11JAN2024
T0000000008 A100003 CHG    40.00 12JAN2024
T0000000009 A100003 REF    25.00 14JAN2024
T0000000010 A100004 WDR   900.00 10JAN2024
T0000000011 A100004 DEP   100.00 13JAN2024
T0000000099 A100005 XYZ   100.00 11JAN2024
T0000000100         DEP    50.00 11JAN2024
T0000000101 A100006 DEP 99999999.00 11JAN2024
T0000000102 A100007 DEP   200.00 31DEC2099
;
run;

/* ---- Account pre-balances (stands in for STG_BANK.CUST_ACCOUNTS_DAILY) ---- */
data WORK.CUST_ACCOUNTS_DAILY;
  length ACCOUNT_ID $10;
  input ACCOUNT_ID $ CURRENT_BALANCE;
  datalines;
A100001 1000.00
A100002 5000.00
A100003  150.00
A100004  600.00
;
run;

  /* ----------------------------------------------------------
     Step 1: Validate Incoming Feed
     ---------------------------------------------------------- */
  data WORK.TXN_VALIDATED(label="Validated Transactions")
       WORK.TXN_REJECTED(label="Rejected Transactions");

    set WORK.TXN_FEED;

    length REJECT_REASON $200;

    /* Validation: Required fields */
    if missing(TRANSACTION_ID) then do;
      REJECT_REASON = 'Missing TRANSACTION_ID';
      output WORK.TXN_REJECTED;
      return;
    end;

    if missing(ACCOUNT_ID) then do;
      REJECT_REASON = 'Missing ACCOUNT_ID';
      output WORK.TXN_REJECTED;
      return;
    end;

    if missing(TRANSACTION_AMOUNT) then do;
      REJECT_REASON = 'Missing TRANSACTION_AMOUNT';
      output WORK.TXN_REJECTED;
      return;
    end;

    /* Validation: Amount range */
    if abs(TRANSACTION_AMOUNT) > 10000000 then do;
      REJECT_REASON = catx(' ', 'Amount exceeds threshold:',
        put(TRANSACTION_AMOUNT, dollar18.2));
      output WORK.TXN_REJECTED;
      return;
    end;

    /* Validation: Valid transaction type */
    if TRANSACTION_TYPE not in ('DEP','WDR','TRF','PMT','FEE','INT','ADJ','REV','CHG','REF')
    then do;
      REJECT_REASON = catx(' ', 'Invalid transaction type:', TRANSACTION_TYPE);
      output WORK.TXN_REJECTED;
      return;
    end;

    /* Validation: Future-dated check */
    if TRANSACTION_DATE > "&txn_date"d then do;
      REJECT_REASON = catx(' ', 'Future dated:',
        put(TRANSACTION_DATE, date9.));
      output WORK.TXN_REJECTED;
      return;
    end;

    output WORK.TXN_VALIDATED;
    drop REJECT_REASON;
  run;

/* Note: the upstream validation step ends with `drop REJECT_REASON;`,
   which (per Base SAS, where a DROP statement applies to every output
   data set of the step) removes REJECT_REASON from the rejected table
   as well, so it is not listed below. The four rows that failed
   validation are: invalid type, missing account id, amount over the
   threshold, and future dated. */
proc print data=WORK.TXN_REJECTED noobs;
  var TRANSACTION_ID ACCOUNT_ID TRANSACTION_TYPE TRANSACTION_AMOUNT
      TRANSACTION_DATE;
run;

  /* ----------------------------------------------------------
     Step 2 (enrichment): attach each account's pre-txn balance
     ---------------------------------------------------------- */
  proc sql;
    create table WORK.TXN_ENRICHED as
    select
      t.*,
      a.CURRENT_BALANCE as PRE_TXN_BALANCE
    from WORK.TXN_VALIDATED t
    left join WORK.CUST_ACCOUNTS_DAILY a
      on t.ACCOUNT_ID = a.ACCOUNT_ID
    order by t.ACCOUNT_ID, t.TRANSACTION_DATE, t.TRANSACTION_ID
    ;
  quit;

  /* ----------------------------------------------------------
     Step 3: Running Balance Calculation
     ---------------------------------------------------------- */
  data WORK.TXN_WITH_BALANCE;
    set WORK.TXN_ENRICHED;
    by ACCOUNT_ID TRANSACTION_DATE TRANSACTION_ID;

    retain RUNNING_BALANCE;

    if first.ACCOUNT_ID then
      RUNNING_BALANCE = PRE_TXN_BALANCE;

    if TRANSACTION_TYPE in ('DEP','INT','REF','REV') then
      RUNNING_BALANCE = RUNNING_BALANCE + TRANSACTION_AMOUNT;
    else if TRANSACTION_TYPE in ('WDR','PMT','FEE','CHG') then
      RUNNING_BALANCE = RUNNING_BALANCE - abs(TRANSACTION_AMOUNT);
    else if TRANSACTION_TYPE in ('TRF','ADJ') then
      RUNNING_BALANCE = RUNNING_BALANCE + TRANSACTION_AMOUNT;

    format RUNNING_BALANCE dollar18.2 PRE_TXN_BALANCE dollar18.2;
  run;

proc print data=WORK.TXN_WITH_BALANCE noobs;
  var ACCOUNT_ID TRANSACTION_DATE TRANSACTION_ID TRANSACTION_TYPE
      TRANSACTION_AMOUNT PRE_TXN_BALANCE RUNNING_BALANCE;
run;
