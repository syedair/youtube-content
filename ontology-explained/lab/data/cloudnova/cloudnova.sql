-- CloudNova seed data (plain SQL; loaded into in-memory SQLite by common.io.load_cloudnova)
CREATE TABLE person (id TEXT PRIMARY KEY, name TEXT, role TEXT, hipaa_training TEXT);
CREATE TABLE customer (id TEXT PRIMARY KEY, name TEXT, industry TEXT);
CREATE TABLE product (id TEXT PRIMARY KEY, name TEXT);
CREATE TABLE engagement (id TEXT PRIMARY KEY, name TEXT, customer_id TEXT, product_id TEXT, lead_id TEXT, reviewer_id TEXT, status TEXT);

INSERT INTO person VALUES ('emma', 'Emma Clarke', 'Consultant', 'due');
INSERT INTO person VALUES ('daniel', 'Daniel Brooks', 'Chief Architect', 'trained');

INSERT INTO customer VALUES ('acme-health', 'Acme Health', 'healthcare');
INSERT INTO customer VALUES ('globex-bank', 'Globex Bank', 'finance');
INSERT INTO customer VALUES ('initech', 'Initech', 'retail');

INSERT INTO product VALUES ('cirrus-ai', 'Cirrus AI');
INSERT INTO product VALUES ('cirrus-sql', 'Cirrus SQL');
INSERT INTO product VALUES ('cirrus-graph', 'Cirrus Graph');

INSERT INTO engagement VALUES ('claims-ai', 'Claims AI', 'acme-health', 'cirrus-ai', 'emma', 'daniel', 'open');
INSERT INTO engagement VALUES ('lakehouse', 'Lakehouse', 'globex-bank', 'cirrus-sql', 'daniel', NULL, 'open');
INSERT INTO engagement VALUES ('patient-360', 'Patient 360', 'acme-health', 'cirrus-graph', 'daniel', NULL, 'open');
-- An engagement nobody leads yet (competency question CQ2).
INSERT INTO engagement VALUES ('fraud-watch', 'Fraud Watch', 'initech', 'cirrus-sql', NULL, NULL, 'open');

-- Billing and contracts (episode 6): three reports count "active customers" three ways.
-- Lakehouse is billed at milestones (the last one in July); nothing is signed with Initech yet.
CREATE TABLE invoice (id TEXT PRIMARY KEY, customer_id TEXT, billed_on TEXT);
CREATE TABLE contract (id TEXT PRIMARY KEY, customer_id TEXT, signed_on TEXT);

INSERT INTO invoice VALUES ('inv-1041', 'globex-bank', '2026-07-15');
INSERT INTO invoice VALUES ('inv-1057', 'acme-health', '2026-10-01');

INSERT INTO contract VALUES ('msa-acme-health', 'acme-health', '2025-03-14');
INSERT INTO contract VALUES ('msa-globex-bank', 'globex-bank', '2024-11-05');

-- Patients and lab results (competency question CQ3). A valid LOINC code looks like 4548-4 (HbA1c).
CREATE TABLE patient (id TEXT PRIMARY KEY, name TEXT);
CREATE TABLE lab_result (id TEXT PRIMARY KEY, name TEXT, patient_id TEXT, loinc TEXT);

INSERT INTO patient VALUES ('p7', 'Patient P7');

INSERT INTO lab_result VALUES ('lab-1', 'HbA1c', 'p7', '4548-4');
INSERT INTO lab_result VALUES ('lab-2', 'Fasting glucose', 'p7', NULL);
INSERT INTO lab_result VALUES ('lab-3', 'Lipid panel', 'p7', 'LIPID-LOCAL');
