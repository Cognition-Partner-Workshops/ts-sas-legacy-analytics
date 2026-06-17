/* autoexec for t004_account_snapshot
   Caps output rows, and loads the repository's banking format catalog
   (Formats/banking_formats.sas) into WORK so the snapshot DATA step's
   FORMAT statement resolves $ACCTTYPE / $ACCTSTAT / RISKRATE /
   $CUSTSEG / $REGION. These value sets are the repository's, verbatim;
   the catalog target is WORK instead of the permanent BANKING library. */
options obs=100;

proc format library=WORK;
  value $ACCTTYPE
    'CHK'  = 'Checking'        'SAV'  = 'Savings'
    'MMA'  = 'Money Market'    'CD'   = 'Certificate of Deposit'
    'IRA'  = 'Individual Retirement' 'LOC' = 'Line of Credit'
    'MTG'  = 'Mortgage'        'AUTO' = 'Auto Loan'
    'PERS' = 'Personal Loan'   'CC'   = 'Credit Card'
    'HELC' = 'Home Equity LOC' OTHER  = 'Unknown';
  value $ACCTSTAT
    'A'  = 'Active'   'C'  = 'Closed'   'D'  = 'Dormant'
    'F'  = 'Frozen'   'R'  = 'Restricted' 'S' = 'Suspended'
    'P'  = 'Pending'  'W'  = 'Written Off' OTHER = 'Unknown';
  value RISKRATE
    1 = 'Minimal Risk'  2 = 'Low Risk'       3 = 'Moderate Risk'
    4 = 'Elevated Risk' 5 = 'High Risk'      6 = 'Very High Risk'
    7 = 'Loss Expected' OTHER = 'Not Rated';
  value $CUSTSEG
    'RET' = 'Retail'        'PREM' = 'Premium'
    'PB'  = 'Private Banking' 'SMB' = 'Small Business'
    'COMM'= 'Commercial'    'CORP' = 'Corporate'  OTHER = 'Unclassified';
  value $REGION
    'NE' = 'Northeast' 'SE' = 'Southeast' 'MW' = 'Midwest'
    'SW' = 'Southwest' 'W'  = 'West'      'NW' = 'Northwest'
    'HQ' = 'Headquarters' OTHER = 'Unknown';
run;
