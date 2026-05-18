/*=====================================================================
  run_daily_insurance.sas — Daily Insurance Batch Orchestrator
  Purpose: Master control program for the daily insurance ETL batch.
  Schedule: Daily 07:00 via Control-M INS_MASTER
  Last Modified: 2024-01-15
=====================================================================*/

%include "/opt/sas/config/Lev1/SASApp/autoexec.sas";

%macro run_daily_insurance(run_date=&CURR_DT, restart_from=);

  %local batch_id start_tm;
  %let start_tm = %sysfunc(datetime());
  %let batch_id = INS_%sysfunc(putn("&run_date"d, yymmddn8.))_%sysfunc(putn(%sysfunc(datetime()), B8601DT.));

  %put NOTE: ========================================================;
  %put NOTE: DAILY INSURANCE BATCH STARTED;
  %put NOTE: Batch ID: &batch_id;
  %put NOTE: Run Date: &run_date;
  %put NOTE: ========================================================;

  %run_step(1, Claims Processing,
    /opt/sas/custom/programs/Insurance/claims_processing.sas)

  %run_step(2, Policy Valuation,
    /opt/sas/custom/programs/Insurance/policy_valuation.sas)

  %put NOTE: ========================================================;
  %put NOTE: DAILY INSURANCE BATCH COMPLETED;
  %put NOTE: Batch ID: &batch_id;
  %put NOTE: Duration: %sysfunc(putn(%sysevalf(%sysfunc(datetime())-&start_tm), time8.));
  %put NOTE: ========================================================;

%mend run_daily_insurance;

%run_daily_insurance(run_date=&CURR_DT);
