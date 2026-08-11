/*=====================================================================
  t007_customer_profitability — derived from
  Programs/Reports/customer_profitability.sas

  This bundle reproduces the customer P&L assembly:

    Step 1 — interest income per customer (PROC SQL: lending vs deposit
             income split with CASE, the `calculated` net-interest
             margin, count(distinct) and relationship balance), verbatim.
    Step 4 — the P&L assembly DATA step (MERGE of interest income, fee
             income and expected credit loss BY customer, with operating
             cost, total revenue, net profit, annualized ROA and the
             profitability tier), verbatim.
    Step 5 — the segment profitability PROC MEANS summary, verbatim.

  Upstream, Step 1 reads STG_BANK.CUST_ACCOUNTS_DAILY and Steps 2/3 read
  CURATED.DAILY_TRANSACTIONS and CURATED.RISK_SCORES. Those libraries are
  not in the repository, so the account base is supplied inline as
  WORK.CUST_ACCOUNTS_DAILY and the fee-income and ECL inputs as small
  inline tables with the columns the merge reads. The income, P&L and
  summary logic is unchanged.
=====================================================================*/

%let report_month = 202401;

/* ---- Account base (stands in for STG_BANK.CUST_ACCOUNTS_DAILY) ---- */
data WORK.CUST_ACCOUNTS_DAILY;
  length CUSTOMER_ID $10 ACCOUNT_ID $10 ACCOUNT_TYPE $4
         CUSTOMER_SEGMENT $4 REGION_CODE $2 BRANCH_ID $5;
  input CUSTOMER_ID $ ACCOUNT_ID $ ACCOUNT_TYPE $ CUSTOMER_SEGMENT $
        REGION_CODE $ BRANCH_ID $ CURRENT_BALANCE INTEREST_RATE;
  datalines;
C0001 A100001 MTG  PB   NE BR001 285000 0.0625
C0001 A100002 SAV  PB   NE BR001  45200 0.0150
C0002 A100003 CC   RET  SE BR014   4200 0.1990
C0002 A100004 CHK  RET  SE BR014   1500 0.0010
C0003 A100005 AUTO SMB  MW BR007  18500 0.0710
C0003 A100006 LOC  SMB  MW BR007  33000 0.0925
C0004 A100007 MTG  PREM SW BR021 410000 0.0590
C0005 A100008 HELC CORP NW BR009  98500 0.0680
;
run;

/* ---- Fee income (stands in for the Step 2 transaction rollup) ---- */
data WORK.FEE_INCOME;
  length CUSTOMER_ID $10;
  input CUSTOMER_ID $ FEE_INCOME INT_CREDITED TXN_VOLUME;
  datalines;
C0001  35.00 120.50 42
C0002  90.00  18.25 65
C0003  15.00  42.00 33
C0004  10.00 310.00 18
;
run;

/* ---- Expected credit loss (stands in for the Step 3 risk-score rollup) ---- */
data WORK.ECL;
  length CUSTOMER_ID $10;
  input CUSTOMER_ID $ TOTAL_ECL;
  datalines;
C0001  150.00
C0003  640.00
C0004 1100.00
C0005  220.00
;
run;

  /* ----------------------------------------------------------
     Step 1: Interest Income by Customer
     ---------------------------------------------------------- */
  proc sql;
    create table WORK.INTEREST_INCOME as
    select
      a.CUSTOMER_ID,
      /* Primary segment/region/branch (from largest account) */
      max(a.CUSTOMER_SEGMENT) as CUSTOMER_SEGMENT,
      max(a.REGION_CODE) as REGION_CODE,
      max(a.BRANCH_ID) as BRANCH_ID,
      /* Lending income */
      sum(case when a.ACCOUNT_TYPE in ('MTG','AUTO','PERS','CC','LOC','HELC')
        then a.CURRENT_BALANCE * a.INTEREST_RATE / 12 else 0 end)
        as LENDING_INCOME format=dollar18.2,
      /* Deposit cost */
      sum(case when a.ACCOUNT_TYPE in ('CHK','SAV','MMA','CD','IRA')
        then a.CURRENT_BALANCE * a.INTEREST_RATE / 12 else 0 end)
        as DEPOSIT_COST format=dollar18.2,
      /* Net interest margin */
      calculated LENDING_INCOME - calculated DEPOSIT_COST
        as NET_INTEREST_INCOME format=dollar18.2,
      count(distinct a.ACCOUNT_ID) as NUM_ACCOUNTS,
      sum(a.CURRENT_BALANCE) as TOTAL_RELATIONSHIP format=dollar18.2
    from WORK.CUST_ACCOUNTS_DAILY a
    group by a.CUSTOMER_ID
    ;
  quit;

  /* ----------------------------------------------------------
     Step 4: Customer P&L Assembly
     ---------------------------------------------------------- */
  data WORK.CUSTOMER_PNL(label="Customer Profitability &report_month");
    merge WORK.INTEREST_INCOME(in=a)
          WORK.FEE_INCOME(in=b)
          WORK.ECL(in=c);
    by CUSTOMER_ID;

    if a;

    /* Operating cost allocation (simplified: $15/account/month) */
    OPERATING_COST = NUM_ACCOUNTS * 15;
    format OPERATING_COST dollar18.2;

    /* Total Revenue */
    TOTAL_REVENUE = sum(NET_INTEREST_INCOME, FEE_INCOME, 0);
    format TOTAL_REVENUE dollar18.2;

    /* Net Profit */
    NET_PROFIT = TOTAL_REVENUE - OPERATING_COST - coalesce(TOTAL_ECL, 0);
    format NET_PROFIT dollar18.2;

    /* ROA (annualized) */
    if TOTAL_RELATIONSHIP > 0 then
      ROA = (NET_PROFIT * 12) / TOTAL_RELATIONSHIP;
    else
      ROA = .;
    format ROA percent8.4;

    /* Profitability tier */
    length PROFIT_TIER $20;
    if NET_PROFIT >= 500    then PROFIT_TIER = 'Highly Profitable';
    else if NET_PROFIT >= 100 then PROFIT_TIER = 'Profitable';
    else if NET_PROFIT >= 0   then PROFIT_TIER = 'Marginal';
    else PROFIT_TIER = 'Unprofitable';

    REPORT_MONTH = "&report_month";
  run;

proc print data=WORK.CUSTOMER_PNL noobs;
  var CUSTOMER_ID CUSTOMER_SEGMENT NUM_ACCOUNTS NET_INTEREST_INCOME
      FEE_INCOME TOTAL_REVENUE OPERATING_COST TOTAL_ECL NET_PROFIT
      PROFIT_TIER;
run;

  /* ----------------------------------------------------------
     Step 5: Segment Summary
     ---------------------------------------------------------- */
  proc means data=WORK.CUSTOMER_PNL noprint nway;
    class CUSTOMER_SEGMENT;
    var TOTAL_REVENUE OPERATING_COST TOTAL_ECL NET_PROFIT TOTAL_RELATIONSHIP;
    output out=WORK.SEGMENT_PROFITABILITY(drop=_TYPE_ _FREQ_)
      n=N_CUSTOMERS
      sum=
      mean(NET_PROFIT)=AVG_PROFIT_PER_CUSTOMER
    ;
  run;

proc print data=WORK.SEGMENT_PROFITABILITY noobs;
run;
