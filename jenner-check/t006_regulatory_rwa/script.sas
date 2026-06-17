/*=====================================================================
  t006_regulatory_rwa — derived from
  Programs/Banking/monthly_regulatory_reporting.sas

  This bundle exercises the Basel III standardized-approach
  Risk-Weighted Assets (RWA) aggregation (Step 1) and the delinquency
  aging buckets (Step 2) from the monthly regulatory report, both
  PROC SQL with CASE expressions and the `calculated` keyword.

  Upstream these select from STG_BANK.CUST_ACCOUNTS_DAILY left joined to
  ORA_DW.LOAN_DETAILS, filtered to the snapshot date. Those libraries
  are not in the repository, so the join result is supplied here as a
  single inline WORK.CUST_ACCOUNTS_DAILY carrying the columns the two
  queries read (ACCOUNT_TYPE, CUSTOMER_SEGMENT, REGION_CODE, LTV,
  CURRENT_BALANCE, DAYS_PAST_DUE, PAST_DUE_AMOUNT). The SNAPSHOT_DATE
  filter is dropped since the inline table is already the target month;
  the risk-weight CASE logic, the bucket CASE logic, the aggregations
  and the bucket ordering are unchanged from the repository.
=====================================================================*/

%let report_month = 202401;

/* ---- Join result of STG_BANK.CUST_ACCOUNTS_DAILY x ORA_DW.LOAN_DETAILS ---- */
data WORK.CUST_ACCOUNTS_DAILY;
  length ACCOUNT_TYPE $4 CUSTOMER_SEGMENT $4 REGION_CODE $2;
  input ACCOUNT_TYPE $ CUSTOMER_SEGMENT $ REGION_CODE $
        LTV CURRENT_BALANCE DAYS_PAST_DUE PAST_DUE_AMOUNT;
  datalines;
MTG  PB   NE 0.62 285000   0      0
MTG  SMB  SW 0.91 410000  45   8200
MTG  RET  MW 0.78 150000   0      0
HELC CORP NW 0.88  98500  72   5400
AUTO RET  SE 0.74  18500   0      0
AUTO COMM HQ 0.55  12750 120   3100
PERS PREM W  .       9300  30   1200
CC   RET  MW .       4200   0      0
CC   RET  SW .      11800 180   4800
LOC  SMB  MW .      33000  15    900
CHK  RET  NE .       1532   0      0
SAV  PREM SE .      45200   0      0
CD   PB   NE .     120000   0      0
;
run;

  /* ----------------------------------------------------------
     Step 1: Risk-Weighted Assets by Category
     Basel III standardized approach risk weights
     ---------------------------------------------------------- */
  proc sql;
    create table WORK.MONTHLY_RWA as
    select
      "&report_month" as REPORT_MONTH length=6,
      ACCOUNT_TYPE,
      CUSTOMER_SEGMENT,
      case
        when ACCOUNT_TYPE in ('CHK','SAV','MMA')     then 0.00
        when ACCOUNT_TYPE = 'CD'                     then 0.00
        when ACCOUNT_TYPE = 'MTG' and LTV <= 0.80    then 0.35
        when ACCOUNT_TYPE = 'MTG' and LTV >  0.80    then 0.50
        when ACCOUNT_TYPE = 'HELC'                   then 0.50
        when ACCOUNT_TYPE in ('AUTO','PERS')         then 0.75
        when ACCOUNT_TYPE = 'CC'                     then 0.75
        when ACCOUNT_TYPE = 'LOC'                    then 1.00
        else 1.00
      end as RISK_WEIGHT,
      count(*) as N_ACCOUNTS,
      sum(CURRENT_BALANCE)                    as TOTAL_EXPOSURE format=dollar20.2,
      sum(CURRENT_BALANCE * calculated RISK_WEIGHT) as RWA      format=dollar20.2
    from WORK.CUST_ACCOUNTS_DAILY
    group by 1, 2, 3, 4
    order by ACCOUNT_TYPE, CUSTOMER_SEGMENT
    ;
  quit;

proc print data=WORK.MONTHLY_RWA noobs;
run;

  /* ----------------------------------------------------------
     Step 2: Delinquency Aging — 30/60/90/120/180+ Buckets
     ---------------------------------------------------------- */
  proc sql;
    create table WORK.DELINQUENCY_AGING as
    select
      "&report_month" as REPORT_MONTH length=6,
      ACCOUNT_TYPE,
      REGION_CODE,
      case
        when DAYS_PAST_DUE = 0          then 'Current'
        when DAYS_PAST_DUE between 1 and 29  then '1-29'
        when DAYS_PAST_DUE between 30 and 59 then '30-59'
        when DAYS_PAST_DUE between 60 and 89 then '60-89'
        when DAYS_PAST_DUE between 90 and 119 then '90-119'
        when DAYS_PAST_DUE between 120 and 179 then '120-179'
        when DAYS_PAST_DUE >= 180       then '180+'
        else 'Unknown'
      end as DELINQ_BUCKET length=10,
      count(*)               as N_ACCOUNTS,
      sum(CURRENT_BALANCE)   as TOTAL_BALANCE format=dollar20.2,
      sum(PAST_DUE_AMOUNT)   as TOTAL_PAST_DUE format=dollar20.2
    from WORK.CUST_ACCOUNTS_DAILY
    where ACCOUNT_TYPE in ('MTG','AUTO','PERS','CC','LOC','HELC')
    group by 1, 2, 3, 4
    order by ACCOUNT_TYPE, REGION_CODE,
      case
        when calculated DELINQ_BUCKET = 'Current'  then 0
        when calculated DELINQ_BUCKET = '1-29'     then 1
        when calculated DELINQ_BUCKET = '30-59'    then 2
        when calculated DELINQ_BUCKET = '60-89'    then 3
        when calculated DELINQ_BUCKET = '90-119'   then 4
        when calculated DELINQ_BUCKET = '120-179'  then 5
        when calculated DELINQ_BUCKET = '180+'     then 6
        else 7
      end
    ;
  quit;

proc print data=WORK.DELINQUENCY_AGING noobs;
run;
