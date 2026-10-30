CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS warehouse;
CREATE SCHEMA IF NOT EXISTS marts;

CREATE TABLE IF NOT EXISTS raw.payment_events (
    event_id BIGSERIAL PRIMARY KEY,
    event_key TEXT NOT NULL UNIQUE,
    event_time TIMESTAMPTZ NOT NULL,
    payment_id TEXT NOT NULL,
    order_id TEXT NOT NULL,
    user_id BIGINT NOT NULL,
    merchant_id BIGINT,
    amount NUMERIC(12,2) NOT NULL CHECK (amount > 0),
    currency CHAR(3) NOT NULL DEFAULT 'INR',
    payment_method TEXT NOT NULL,
    provider TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('SUCCESS', 'FAILED')),
    failure_reason TEXT,
    city TEXT NOT NULL,
    device TEXT NOT NULL,
    is_retry BOOLEAN NOT NULL DEFAULT FALSE,
    latency_ms INTEGER,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_raw_events_time ON raw.payment_events (event_time DESC);
CREATE INDEX IF NOT EXISTS ix_raw_events_provider_time ON raw.payment_events (provider, event_time DESC);
CREATE INDEX IF NOT EXISTS ix_raw_events_status_time ON raw.payment_events (status, event_time DESC);

CREATE TABLE IF NOT EXISTS warehouse.fact_payments (
    payment_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    user_id BIGINT NOT NULL,
    payment_time TIMESTAMPTZ NOT NULL,
    amount NUMERIC(12,2) NOT NULL,
    payment_method TEXT NOT NULL,
    provider TEXT NOT NULL,
    final_status TEXT NOT NULL,
    failure_reason TEXT,
    is_retry BOOLEAN NOT NULL DEFAULT FALSE,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS warehouse.dim_users (
    user_id BIGINT PRIMARY KEY,
    first_seen TIMESTAMPTZ NOT NULL,
    last_seen TIMESTAMPTZ NOT NULL,
    total_payments BIGINT NOT NULL,
    successful_payments BIGINT NOT NULL,
    failed_payments BIGINT NOT NULL,
    total_amount NUMERIC(18,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS warehouse.dim_date (
    date DATE PRIMARY KEY,
    day_of_month INTEGER NOT NULL,
    month INTEGER NOT NULL,
    year INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    is_weekend BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS marts.daily_metrics (
    date DATE PRIMARY KEY,
    total_transactions BIGINT NOT NULL,
    successful_transactions BIGINT NOT NULL,
    failed_transactions BIGINT NOT NULL,
    total_revenue NUMERIC(18,2) NOT NULL,
    unique_users BIGINT NOT NULL,
    failure_rate NUMERIC(8,5) NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS marts.realtime_metrics (
    bucket_start TIMESTAMPTZ NOT NULL,
    provider TEXT NOT NULL,
    total_transactions BIGINT NOT NULL,
    successful_transactions BIGINT NOT NULL,
    failed_transactions BIGINT NOT NULL,
    failure_rate NUMERIC(8,5) NOT NULL,
    total_revenue NUMERIC(18,2) NOT NULL,
    PRIMARY KEY (bucket_start, provider)
);

CREATE TABLE IF NOT EXISTS marts.anomaly_alerts (
    alert_id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    window_start TIMESTAMPTZ NOT NULL,
    window_end TIMESTAMPTZ NOT NULL,
    provider TEXT NOT NULL,
    metric TEXT NOT NULL,
    metric_value NUMERIC(12,5) NOT NULL,
    expected_value NUMERIC(12,5) NOT NULL,
    deviation NUMERIC(12,5) NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    alert_level TEXT NOT NULL DEFAULT 'MEDIUM',
    status TEXT NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'ACKNOWLEDGED', 'RESOLVED')),
    evidence JSONB NOT NULL DEFAULT '{}'::jsonb,
    fingerprint TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_alerts_recent ON marts.anomaly_alerts (detected_at DESC);
CREATE INDEX IF NOT EXISTS ix_realtime_metrics_recent ON marts.realtime_metrics (bucket_start DESC);
