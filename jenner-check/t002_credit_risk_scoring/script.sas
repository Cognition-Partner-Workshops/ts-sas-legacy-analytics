/*=====================================================================
  t002_credit_risk_scoring — derived from
  Programs/Banking/credit_risk_scoring.sas

  The upstream program assembles a scoring feature table in Step 1 by
  joining STG_BANK.CUST_ACCOUNTS_DAILY with the Oracle data-warehouse
  tables ORA_DW.BUREAU_SCORES, ORA_DW.PAYMENT_HISTORY and
  ORA_DW.COLLATERAL. Those libraries are not part of the repository, so
  Step 1 is replaced here by a small inline WORK.SCORE_INPUT with the
  same column shape the scorecard reads (FICO_SCORE, UTILIZATION_PCT,
  PMT_LATE_90_12MO, ACCT_AGE_MONTHS, LTV, ACCOUNT_TYPE, balances).

  Step 2 (the validated CRM-2023-Q4-v2 scorecard: WOE binning, the
  log-odds / PD logistic calculation, LGD, EAD, expected loss and the
  1-7 risk-rating assignment) and Step 5 (the PROC MEANS risk summary)
  are reproduced verbatim from the repository program.
=====================================================================*/

/* ---- Step 1 substitute: inline scoring feature sample ----
   Same columns the upstream scorecard reads downstream. */
data WORK.SCORE_INPUT;
  length ACCOUNT_ID $10 CUSTOMER_ID $10 ACCOUNT_TYPE $4
         CUSTOMER_SEGMENT $4 REGION_CODE $2;
  input ACCOUNT_ID $ CUSTOMER_ID $ ACCOUNT_TYPE $ CURRENT_BALANCE
        CREDIT_LIMIT ACCT_AGE_MONTHS UTILIZATION_PCT FICO_SCORE
        PMT_LATE_90_12MO LTV CUSTOMER_SEGMENT $ REGION_CODE $;
  datalines;
A100001 C0001 MTG  285000 300000 142  95.0 778 0 0.62 PB   NE
A100002 C0002 AUTO  18500  25000  36  74.0 705 1 0.74 RET  SE
A100003 C0003 CC     4200   8000  28  52.5 662 0  .   RET  MW
A100004 C0004 MTG  410000 420000  18  97.6 612 2 1.05 SMB  SW
A100005 C0005 PERS   9300   9300  60   .   730 0  .   PREM W
A100006 C0006 HELC  98500 120000  84  82.1 690 1 0.88 CORP NW
A100007 C0007 CC    11800  12000  14  98.3 588 3  .   RET  SW
A100008 C0008 AUTO  12750  20000 110  63.7 762 0 0.55 COMM HQ
A100009 C0009 MTG  150000 250000 200  60.0 805 0 0.40 PB   NE
A100010 C0010 LOC   33000  50000  44  66.0 648 1  .   SMB  MW
;
run;

  /* ----------------------------------------------------------
     Step 2: Apply Scorecard Model
     Coefficients from validated Model CRM-2023-Q4-v2
     ---------------------------------------------------------- */
  data WORK.SCORED;
    set WORK.SCORE_INPUT;

    /* Logistic regression: log-odds calculation */
    INTERCEPT = -3.2145;

    /* FICO score contribution (normalized) */
    if not missing(FICO_SCORE) then do;
      if FICO_SCORE >= 760      then WOE_FICO = -1.204;
      else if FICO_SCORE >= 720 then WOE_FICO = -0.812;
      else if FICO_SCORE >= 680 then WOE_FICO = -0.356;
      else if FICO_SCORE >= 640 then WOE_FICO =  0.198;
      else if FICO_SCORE >= 600 then WOE_FICO =  0.654;
      else WOE_FICO = 1.102;
    end;
    else WOE_FICO = 0.198;  /* Population average for missing */

    /* Utilization contribution */
    if not missing(UTILIZATION_PCT) then do;
      if UTILIZATION_PCT <= 10      then WOE_UTIL = -0.956;
      else if UTILIZATION_PCT <= 30 then WOE_UTIL = -0.521;
      else if UTILIZATION_PCT <= 50 then WOE_UTIL = -0.102;
      else if UTILIZATION_PCT <= 70 then WOE_UTIL =  0.334;
      else if UTILIZATION_PCT <= 90 then WOE_UTIL =  0.789;
      else WOE_UTIL = 1.245;
    end;
    else WOE_UTIL = 0;

    /* Payment history contribution */
    if not missing(PMT_LATE_90_12MO) then do;
      if PMT_LATE_90_12MO = 0      then WOE_DPD = -0.678;
      else if PMT_LATE_90_12MO = 1  then WOE_DPD =  0.445;
      else WOE_DPD = 1.567;
    end;
    else WOE_DPD = 0;

    /* Account age contribution */
    if not missing(ACCT_AGE_MONTHS) then do;
      if ACCT_AGE_MONTHS >= 120     then WOE_AGE = -0.534;
      else if ACCT_AGE_MONTHS >= 60 then WOE_AGE = -0.289;
      else if ACCT_AGE_MONTHS >= 24 then WOE_AGE =  0.045;
      else WOE_AGE = 0.456;
    end;
    else WOE_AGE = 0;

    /* LTV contribution (secured only) */
    if ACCOUNT_TYPE in ('MTG','AUTO','HELC') then do;
      if not missing(LTV) then do;
        if LTV <= 0.60      then WOE_LTV = -0.712;
        else if LTV <= 0.80 then WOE_LTV = -0.234;
        else if LTV <= 1.00 then WOE_LTV =  0.356;
        else WOE_LTV = 0.889;
      end;
      else WOE_LTV = 0;
    end;
    else WOE_LTV = 0;

    /* Calculate log-odds and PD */
    LOG_ODDS = INTERCEPT
      + 0.412 * WOE_FICO
      + 0.198 * WOE_UTIL
      + 0.289 * WOE_DPD
      + 0.067 * WOE_AGE
      + 0.134 * WOE_LTV;

    PD = 1 / (1 + exp(-LOG_ODDS));
    format PD percent8.4;

    /* LGD estimation */
    if ACCOUNT_TYPE in ('MTG','AUTO','HELC') then do;
      if not missing(LTV) then
        LGD = max(0, min(1, (LTV - 0.5) * 0.8));
      else
        LGD = 0.40;
    end;
    else if ACCOUNT_TYPE = 'CC' then LGD = 0.75;
    else LGD = 0.50;
    format LGD percent8.4;

    /* EAD estimation */
    if ACCOUNT_TYPE in ('CC','LOC','HELC') then
      EAD = CURRENT_BALANCE + 0.50 * (CREDIT_LIMIT - CURRENT_BALANCE);
    else
      EAD = CURRENT_BALANCE;
    format EAD dollar18.2;

    /* Expected Loss */
    EXPECTED_LOSS = PD * LGD * EAD;
    format EXPECTED_LOSS dollar18.2;

    /* Risk Rating Assignment */
    if PD < 0.005      then NEW_RISK_RATING = 1;
    else if PD < 0.01  then NEW_RISK_RATING = 2;
    else if PD < 0.03  then NEW_RISK_RATING = 3;
    else if PD < 0.07  then NEW_RISK_RATING = 4;
    else if PD < 0.15  then NEW_RISK_RATING = 5;
    else if PD < 0.30  then NEW_RISK_RATING = 6;
    else NEW_RISK_RATING = 7;

    drop INTERCEPT WOE_FICO WOE_UTIL WOE_DPD WOE_AGE WOE_LTV LOG_ODDS;
  run;

proc print data=WORK.SCORED noobs;
  var ACCOUNT_ID ACCOUNT_TYPE FICO_SCORE PD LGD EAD EXPECTED_LOSS NEW_RISK_RATING;
run;

  /* ----------------------------------------------------------
     Step 5: Risk Summary Report
     ---------------------------------------------------------- */
  proc means data=WORK.SCORED noprint nway;
    class ACCOUNT_TYPE NEW_RISK_RATING;
    var PD LGD EAD EXPECTED_LOSS;
    output out=WORK.RISK_SUMMARY(drop=_TYPE_ _FREQ_)
      n=N_ACCOUNTS
      mean(PD)=AVG_PD
      mean(LGD)=AVG_LGD
      sum(EAD)=TOTAL_EAD
      sum(EXPECTED_LOSS)=TOTAL_EL
    ;
  run;

proc print data=WORK.RISK_SUMMARY noobs;
run;
