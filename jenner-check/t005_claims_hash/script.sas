/*=====================================================================
  t005_claims_hash — derived from
  Programs/Insurance/claims_processing.sas

  Step 1 of the claims pipeline validates each incoming claim against
  the policy master using a SAS hash object: it loads active policies
  into an in-memory hash keyed on POLICY_ID, then for each claim does a
  hash .find() and checks the loss date against the policy period and
  the claimed amount against the sum insured, routing failures to a
  separate invalid table.

  This bundle reproduces that hash-object validation DATA step verbatim.
  The upstream loads the hash from RAW_INS.POLICIES (insurance landing
  zone) and reads the daily feed from RAW_INS.CLAIMS_FEED_YYYYMMDD;
  neither library is in the repository, so both are supplied inline here
  with the columns the step reads (POLICY_ID, POLICY_TYPE, dates,
  SUM_INSURED, DEDUCTIBLE, STATUS for policies; CLAIM_ID, POLICY_ID,
  CLAIMANT_ID, LOSS_DATE, CLAIMED_AMOUNT for the feed). The hash logic
  is unchanged.
=====================================================================*/

/* ---- Policy master (stands in for RAW_INS.POLICIES) ---- */
data WORK.POLICIES;
  length POLICY_ID $10 POLICY_TYPE $10 STATUS $8;
  informat EFFECTIVE_DATE EXPIRATION_DATE date9.;
  format EFFECTIVE_DATE EXPIRATION_DATE date9.;
  input POLICY_ID $ POLICY_TYPE $ EFFECTIVE_DATE EXPIRATION_DATE
        SUM_INSURED DEDUCTIBLE STATUS $;
  datalines;
POL000001 AUTO  01JAN2023 31DEC2023  50000  500 ACTIVE
POL000002 HOME  01JUN2023 31MAY2024 350000 1000 ACTIVE
POL000003 TL    15MAR2022 14MAR2025 250000    0 ACTIVE
POL000004 HLTH  01JAN2023 31DEC2023  20000  250 LAPSED
POL000005 AUTO  01APR2023 31MAR2024  40000  500 ACTIVE
POL000006 UMBR  01JAN2023 31DEC2023 100000    0 ACTIVE
;
run;

/* ---- Daily claims feed (stands in for RAW_INS.CLAIMS_FEED_YYYYMMDD) ---- */
data WORK.CLAIMS_FEED;
  length CLAIM_ID $12 POLICY_ID $10 CLAIMANT_ID $10;
  informat LOSS_DATE date9.;
  format LOSS_DATE date9.;
  input CLAIM_ID $ POLICY_ID $ CLAIMANT_ID $ LOSS_DATE CLAIMED_AMOUNT;
  datalines;
CLM000000001 POL000001 CLT0001 15JUN2023   8200.00
CLM000000002 POL000002 CLT0002 03AUG2023  42000.00
CLM000000003 POL000003 CLT0003 20FEB2024  15000.00
CLM000000004 POL000004 CLT0004 10MAR2023   3000.00
CLM000000005 POL000005 CLT0005 12FEB2022   2500.00
CLM000000006 POL000006 CLT0006 01JUL2023 150000.00
CLM000000007 POL999999 CLT0007 05MAY2023   1200.00
;
run;

  /* ----------------------------------------------------------
     Step 1: Ingest and Validate
     ---------------------------------------------------------- */
  data WORK.CLAIMS_VALID(label="Validated Claims")
       WORK.CLAIMS_INVALID(label="Invalid Claims");

    set WORK.CLAIMS_FEED;

    length VALIDATION_ERROR $200;

    /* Check policy exists and is active */
    if _N_ = 1 then do;
      declare hash h_pol(dataset: "WORK.POLICIES(where=(STATUS='ACTIVE'))");
      h_pol.definekey('POLICY_ID');
      h_pol.definedata('POLICY_TYPE', 'EFFECTIVE_DATE', 'EXPIRATION_DATE',
                       'SUM_INSURED', 'DEDUCTIBLE');
      h_pol.definedone();
    end;

    length POLICY_TYPE $10 SUM_INSURED DEDUCTIBLE 8;
    format EFFECTIVE_DATE EXPIRATION_DATE date9.;

    rc = h_pol.find();

    if rc ne 0 then do;
      VALIDATION_ERROR = catx(' ', 'Policy not found or inactive:', POLICY_ID);
      output WORK.CLAIMS_INVALID;
      return;
    end;

    /* Check loss date within policy period */
    if LOSS_DATE < EFFECTIVE_DATE or LOSS_DATE > EXPIRATION_DATE then do;
      VALIDATION_ERROR = catx(' ', 'Loss date', put(LOSS_DATE, date9.),
        'outside policy period',
        put(EFFECTIVE_DATE, date9.), '-', put(EXPIRATION_DATE, date9.));
      output WORK.CLAIMS_INVALID;
      return;
    end;

    /* Check claimed amount vs sum insured */
    if CLAIMED_AMOUNT > SUM_INSURED then do;
      VALIDATION_ERROR = catx(' ', 'Claimed amount',
        put(CLAIMED_AMOUNT, dollar18.2), 'exceeds sum insured',
        put(SUM_INSURED, dollar18.2));
      output WORK.CLAIMS_INVALID;
      return;
    end;

    output WORK.CLAIMS_VALID;
    drop VALIDATION_ERROR rc;
  run;

proc print data=WORK.CLAIMS_VALID noobs;
  var CLAIM_ID POLICY_ID POLICY_TYPE LOSS_DATE CLAIMED_AMOUNT SUM_INSURED;
run;

/* The validation step ends with `drop VALIDATION_ERROR rc;` (verbatim
   from the repository). Base SAS applies a DROP to every output data
   set, so VALIDATION_ERROR is not carried into the invalid table; the
   four rows that failed validation are the lapsed policy, the
   out-of-period loss date, the over-limit claim, and the unknown
   policy id. */
proc print data=WORK.CLAIMS_INVALID noobs;
  var CLAIM_ID POLICY_ID LOSS_DATE CLAIMED_AMOUNT;
run;
