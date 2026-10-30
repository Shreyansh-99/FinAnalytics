-- Compatibility migration for the original FinAnalytics database.
-- Safe to run after 001_schema.sql against an existing database.
CREATE TABLE IF NOT EXISTS marts.realtime_metrics (
    bucket_start TIMESTAMP NOT NULL,
    provider TEXT NOT NULL,
    total_transactions BIGINT NOT NULL,
    successful_transactions BIGINT NOT NULL,
    failed_transactions BIGINT NOT NULL,
    failure_rate NUMERIC(8,5) NOT NULL,
    total_revenue NUMERIC(18,2) NOT NULL,
    PRIMARY KEY (bucket_start, provider)
);

ALTER TABLE marts.anomaly_alerts ADD COLUMN IF NOT EXISTS alert_id BIGSERIAL;
ALTER TABLE marts.anomaly_alerts ADD COLUMN IF NOT EXISTS date DATE;
ALTER TABLE marts.anomaly_alerts ADD COLUMN IF NOT EXISTS detected_at TIMESTAMP DEFAULT now();
ALTER TABLE marts.anomaly_alerts ADD COLUMN IF NOT EXISTS window_start TIMESTAMP;
ALTER TABLE marts.anomaly_alerts ADD COLUMN IF NOT EXISTS window_end TIMESTAMP;
ALTER TABLE marts.anomaly_alerts ADD COLUMN IF NOT EXISTS provider TEXT DEFAULT 'UNKNOWN';
ALTER TABLE marts.anomaly_alerts ADD COLUMN IF NOT EXISTS severity TEXT DEFAULT 'MEDIUM';
ALTER TABLE marts.anomaly_alerts ADD COLUMN IF NOT EXISTS alert_level TEXT DEFAULT 'MEDIUM';
ALTER TABLE marts.anomaly_alerts ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'OPEN';
ALTER TABLE marts.anomaly_alerts ADD COLUMN IF NOT EXISTS evidence JSONB DEFAULT '{}'::jsonb;
ALTER TABLE marts.anomaly_alerts ADD COLUMN IF NOT EXISTS fingerprint TEXT;
ALTER TABLE marts.anomaly_alerts ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT now();

UPDATE marts.anomaly_alerts
SET date = COALESCE(date, created_at::date, CURRENT_DATE),
    detected_at = COALESCE(detected_at, created_at, now()),
    window_start = COALESCE(window_start, created_at, now()),
    window_end = COALESCE(window_end, created_at + interval '1 day', now()),
    provider = COALESCE(provider, 'UNKNOWN'),
    severity = COALESCE(severity, alert_level, 'MEDIUM'),
    alert_level = COALESCE(alert_level, severity, 'MEDIUM'),
    status = COALESCE(status, 'OPEN'),
    evidence = COALESCE(evidence, '{}'::jsonb),
    created_at = COALESCE(created_at, detected_at, now());

UPDATE marts.anomaly_alerts
SET fingerprint = md5(concat_ws('|', ctid::text, date::text, provider, metric, metric_value::text));

CREATE UNIQUE INDEX IF NOT EXISTS uq_anomaly_alert_fingerprint
    ON marts.anomaly_alerts (fingerprint);
