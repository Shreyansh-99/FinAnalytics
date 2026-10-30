-- Add fields required by the current warehouse projection while preserving old rows.
ALTER TABLE warehouse.fact_payments
    ADD COLUMN IF NOT EXISTS provider VARCHAR;

ALTER TABLE warehouse.fact_payments
    ADD COLUMN IF NOT EXISTS failure_reason VARCHAR;

ALTER TABLE warehouse.fact_payments
    ADD COLUMN IF NOT EXISTS is_retry BOOLEAN NOT NULL DEFAULT FALSE;

UPDATE warehouse.fact_payments
SET provider = COALESCE(provider, payment_method)
WHERE provider IS NULL;
