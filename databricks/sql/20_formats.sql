CREATE OR REPLACE TABLE sas_legacy.sas_ref.fmt_accttype (code STRING, label STRING);
INSERT INTO sas_legacy.sas_ref.fmt_accttype VALUES
  ('CHK', 'Checking'), ('SAV', 'Savings'), ('MMA', 'Money Market'),
  ('CD', 'Certificate of Deposit'), ('IRA', 'Individual Retirement'),
  ('LOC', 'Line of Credit'), ('MTG', 'Mortgage'), ('AUTO', 'Auto Loan'),
  ('PERS', 'Personal Loan'), ('CC', 'Credit Card'), ('HELC', 'Home Equity LOC'),
  ('_OTHER_', 'Unknown');

CREATE OR REPLACE TABLE sas_legacy.sas_ref.fmt_acctstat (code STRING, label STRING);
INSERT INTO sas_legacy.sas_ref.fmt_acctstat VALUES
  ('A', 'Active'), ('C', 'Closed'), ('D', 'Dormant'), ('F', 'Frozen'),
  ('R', 'Restricted'), ('S', 'Suspended'), ('P', 'Pending'), ('W', 'Written Off'),
  ('_OTHER_', 'Unknown');

CREATE OR REPLACE TABLE sas_legacy.sas_ref.fmt_riskrate (
  lo DOUBLE, hi DOUBLE, lo_inclusive BOOLEAN, hi_inclusive BOOLEAN, label STRING
);
INSERT INTO sas_legacy.sas_ref.fmt_riskrate VALUES
  (1, 1, true, true, 'Minimal Risk'), (2, 2, true, true, 'Low Risk'),
  (3, 3, true, true, 'Moderate Risk'), (4, 4, true, true, 'Elevated Risk'),
  (5, 5, true, true, 'High Risk'), (6, 6, true, true, 'Very High Risk'),
  (7, 7, true, true, 'Loss Expected'), (NULL, NULL, true, true, 'Not Rated');

CREATE OR REPLACE TABLE sas_legacy.sas_ref.fmt_txncat (code STRING, label STRING);
INSERT INTO sas_legacy.sas_ref.fmt_txncat VALUES
  ('DEP', 'Deposit'), ('WDR', 'Withdrawal'), ('TRF', 'Transfer'), ('PMT', 'Payment'),
  ('FEE', 'Fee'), ('INT', 'Interest'), ('ADJ', 'Adjustment'), ('REV', 'Reversal'),
  ('CHG', 'Charge'), ('REF', 'Refund'), ('_OTHER_', 'Other');

CREATE OR REPLACE TABLE sas_legacy.sas_ref.fmt_delqbkt (
  lo DOUBLE, hi DOUBLE, lo_inclusive BOOLEAN, hi_inclusive BOOLEAN, label STRING
);
INSERT INTO sas_legacy.sas_ref.fmt_delqbkt VALUES
  (0, 0, true, true, 'Current'), (1, 29, true, true, '1-29 Days'),
  (30, 59, true, true, '30-59 Days'), (60, 89, true, true, '60-89 Days'),
  (90, 119, true, true, '90-119 Days'), (120, 179, true, true, '120-179 Days'),
  (180, NULL, true, true, '180+ Days');

CREATE OR REPLACE TABLE sas_legacy.sas_ref.fmt_balrange (
  lo DOUBLE, hi DOUBLE, lo_inclusive BOOLEAN, hi_inclusive BOOLEAN, label STRING
);
INSERT INTO sas_legacy.sas_ref.fmt_balrange VALUES
  (NULL, 0, true, false, 'Negative'), (0, 0, true, true, 'Zero'),
  (0, 1000, false, false, '$0-$999'), (1000, 5000, true, false, '$1K-$4,999'),
  (5000, 25000, true, false, '$5K-$24,999'),
  (25000, 100000, true, false, '$25K-$99,999'),
  (100000, 500000, true, false, '$100K-$499,999'),
  (500000, NULL, true, true, '$500K+');

CREATE OR REPLACE TABLE sas_legacy.sas_ref.fmt_region (code STRING, label STRING);
INSERT INTO sas_legacy.sas_ref.fmt_region VALUES
  ('NE', 'Northeast'), ('SE', 'Southeast'), ('MW', 'Midwest'), ('SW', 'Southwest'),
  ('W', 'West'), ('NW', 'Northwest'), ('HQ', 'Headquarters'), ('_OTHER_', 'Unknown');

CREATE OR REPLACE TABLE sas_legacy.sas_ref.fmt_custseg (code STRING, label STRING);
INSERT INTO sas_legacy.sas_ref.fmt_custseg VALUES
  ('RET', 'Retail'), ('PREM', 'Premium'), ('PB', 'Private Banking'),
  ('SMB', 'Small Business'), ('COMM', 'Commercial'), ('CORP', 'Corporate'),
  ('_OTHER_', 'Unclassified');

CREATE OR REPLACE TABLE sas_legacy.sas_ref.fmt_lnpurp (code STRING, label STRING);
INSERT INTO sas_legacy.sas_ref.fmt_lnpurp VALUES
  ('PURCH', 'Purchase'), ('REFI', 'Refinance'), ('CASHOUT', 'Cash-Out Refinance'),
  ('CONST', 'Construction'), ('RENO', 'Renovation'), ('CONSOL', 'Debt Consolidation'),
  ('EDUC', 'Education'), ('MEDIC', 'Medical'), ('_OTHER_', 'Other');

CREATE OR REPLACE TABLE sas_legacy.sas_ref.fmt_registry (
  format_name STRING, table_name STRING, kind STRING, n_rows INT
);
INSERT INTO sas_legacy.sas_ref.fmt_registry VALUES
  ('$ACCTTYPE', 'sas_legacy.sas_ref.fmt_accttype', 'char', 12),
  ('$ACCTSTAT', 'sas_legacy.sas_ref.fmt_acctstat', 'char', 9),
  ('RISKRATE', 'sas_legacy.sas_ref.fmt_riskrate', 'numeric', 8),
  ('$TXNCAT', 'sas_legacy.sas_ref.fmt_txncat', 'char', 11),
  ('DELQBKT', 'sas_legacy.sas_ref.fmt_delqbkt', 'numeric', 7),
  ('BALRANGE', 'sas_legacy.sas_ref.fmt_balrange', 'numeric', 8),
  ('$REGION', 'sas_legacy.sas_ref.fmt_region', 'char', 8),
  ('$CUSTSEG', 'sas_legacy.sas_ref.fmt_custseg', 'char', 7),
  ('$LNPURP', 'sas_legacy.sas_ref.fmt_lnpurp', 'char', 9);
