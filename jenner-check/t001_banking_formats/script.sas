/*=====================================================================
  t001_banking_formats — derived from Formats/banking_formats.sas

  The PROC FORMAT below is the repository's banking format catalog,
  verbatim. The only change from the upstream file is the catalog
  target: the original writes to a permanent catalog at
      libname BANKING "/data/sas/formats/banking";
  which is rewritten here to the WORK library so the bundle is
  self-contained. A short consumer DATA step and PROC PRINT apply the
  account-type, status, risk-rating and region formats to a small
  sample so the formatted values are visible in the listing.
=====================================================================*/

proc format library=WORK;

  /* Account Type Codes */
  value $ACCTTYPE
    'CHK'  = 'Checking'
    'SAV'  = 'Savings'
    'MMA'  = 'Money Market'
    'CD'   = 'Certificate of Deposit'
    'IRA'  = 'Individual Retirement'
    'LOC'  = 'Line of Credit'
    'MTG'  = 'Mortgage'
    'AUTO' = 'Auto Loan'
    'PERS' = 'Personal Loan'
    'CC'   = 'Credit Card'
    'HELC' = 'Home Equity LOC'
    OTHER  = 'Unknown'
  ;

  /* Account Status */
  value $ACCTSTAT
    'A'  = 'Active'
    'C'  = 'Closed'
    'D'  = 'Dormant'
    'F'  = 'Frozen'
    'R'  = 'Restricted'
    'S'  = 'Suspended'
    'P'  = 'Pending'
    'W'  = 'Written Off'
    OTHER = 'Unknown'
  ;

  /* Risk Rating */
  value RISKRATE
    1    = 'Minimal Risk'
    2    = 'Low Risk'
    3    = 'Moderate Risk'
    4    = 'Elevated Risk'
    5    = 'High Risk'
    6    = 'Very High Risk'
    7    = 'Loss Expected'
    OTHER = 'Not Rated'
  ;

  /* Transaction Category */
  value $TXNCAT
    'DEP'  = 'Deposit'
    'WDR'  = 'Withdrawal'
    'TRF'  = 'Transfer'
    'PMT'  = 'Payment'
    'FEE'  = 'Fee'
    'INT'  = 'Interest'
    'ADJ'  = 'Adjustment'
    'REV'  = 'Reversal'
    'CHG'  = 'Charge'
    'REF'  = 'Refund'
    OTHER  = 'Other'
  ;

  /* Delinquency Buckets */
  value DELQBKT
    0        = 'Current'
    1-29     = '1-29 Days'
    30-59    = '30-59 Days'
    60-89    = '60-89 Days'
    90-119   = '90-119 Days'
    120-179  = '120-179 Days'
    180-HIGH = '180+ Days'
  ;

  /* Balance Ranges for Reporting */
  value BALRANGE
    LOW-<0        = 'Negative'
    0             = 'Zero'
    0<-<1000      = '$0-$999'
    1000-<5000    = '$1K-$4,999'
    5000-<25000   = '$5K-$24,999'
    25000-<100000 = '$25K-$99,999'
    100000-<500000= '$100K-$499,999'
    500000-HIGH   = '$500K+'
  ;

  /* Branch Region */
  value $REGION
    'NE' = 'Northeast'
    'SE' = 'Southeast'
    'MW' = 'Midwest'
    'SW' = 'Southwest'
    'W'  = 'West'
    'NW' = 'Northwest'
    'HQ' = 'Headquarters'
    OTHER = 'Unknown'
  ;

  /* Customer Segment */
  value $CUSTSEG
    'RET'  = 'Retail'
    'PREM' = 'Premium'
    'PB'   = 'Private Banking'
    'SMB'  = 'Small Business'
    'COMM' = 'Commercial'
    'CORP' = 'Corporate'
    OTHER  = 'Unclassified'
  ;

  /* Loan Purpose */
  value $LNPURP
    'PURCH' = 'Purchase'
    'REFI'  = 'Refinance'
    'CASHOUT'= 'Cash-Out Refinance'
    'CONST' = 'Construction'
    'RENO'  = 'Renovation'
    'CONSOL'= 'Debt Consolidation'
    'EDUC'  = 'Education'
    'MEDIC' = 'Medical'
    OTHER   = 'Other'
  ;

run;

%put NOTE: Banking formats loaded to WORK;

/* ---- Consumer step: apply the catalog to a small sample ---- */
data accounts;
  length account_id $8 account_type $4 account_status $1
         region_code $2 customer_segment $4;
  input account_id $ account_type $ account_status $ region_code $
        customer_segment $ risk_rating current_balance delq_days;
  datalines;
A100001 CHK  A NE RET  2     1532.40   0
A100002 SAV  A SE PREM 1    45200.00   0
A100003 CC   A MW RET  4     3890.55  45
A100004 MTG  A SW PB   3   285000.00   0
A100005 AUTO D W  SMB  5    12750.00 120
A100006 HELC A NW CORP 6    98500.00  72
A100007 PERS F SW RET  7     6400.00 200
A100008 LOC  A HQ COMM 3   -250.00     0
;
run;

proc print data=accounts noobs label;
  var account_id account_type account_status risk_rating
      region_code customer_segment current_balance delq_days;
  format account_type $ACCTTYPE.
         account_status $ACCTSTAT.
         risk_rating RISKRATE.
         region_code $REGION.
         customer_segment $CUSTSEG.
         current_balance BALRANGE.
         delq_days DELQBKT.;
  label account_id      = 'Account'
        account_type    = 'Account Type'
        account_status  = 'Status'
        risk_rating     = 'Risk Rating'
        region_code     = 'Region'
        customer_segment= 'Segment'
        current_balance = 'Balance Band'
        delq_days       = 'Delinquency';
run;
