-- Three reports, three ways to count "active customers". Each tool keeps its own query, written by its own team.
-- Episode 6 runs each one against cloudnova.sql. One block per report, a "-- <report>: <what it counts>" line
-- and then its query. The reports agree on the word and disagree on the number.

-- sales dashboard: billed in the last 90 days
SELECT DISTINCT c.name FROM customer c JOIN invoice i ON i.customer_id = c.id
WHERE i.billed_on >= date('2026-10-31', '-90 days');

-- consulting team sheet: has an open engagement
SELECT DISTINCT c.name FROM customer c JOIN engagement e ON e.customer_id = c.id
WHERE e.status = 'open';

-- finance report: has a signed contract
SELECT DISTINCT c.name FROM customer c JOIN contract k ON k.customer_id = c.id;
