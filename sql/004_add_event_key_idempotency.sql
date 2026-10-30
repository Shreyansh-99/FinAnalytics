-- Existing payment_id values may repeat for retries/status events.
-- Add a separate unique ingestion key without deleting historical events.
ALTER TABLE raw.payment_events
    ADD COLUMN IF NOT EXISTS event_key TEXT;

UPDATE raw.payment_events
SET event_key = 'legacy_' || event_id::text
WHERE event_key IS NULL;

ALTER TABLE raw.payment_events
    ALTER COLUMN event_key SET NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_payment_events_event_key
    ON raw.payment_events (event_key);
