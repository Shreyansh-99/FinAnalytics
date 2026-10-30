-- Deterministic, set-based historical seed. Run once after 001_schema.sql.
-- FINANALYTICS_SEED_EVENTS can be replaced by the deployment job when using psql.
INSERT INTO raw.payment_events (
    event_key, event_time, payment_id, order_id, user_id, merchant_id, amount, currency,
    payment_method, provider, status, failure_reason, city, device, is_retry, latency_ms
)
SELECT
    'hist_evt_' || g,
    now() - interval '90 days' + (((g - 1) % 129600) * interval '1 minute'),
    'hist_pay_' || g,
    'hist_ord_' || ((g - 1) / 2 + 1),
    100000 + ((g * 7919) % 250000),
    5000 + ((g * 17) % 1000),
    round((40 + ((g * 104729) % 1196000) / 100.0)::numeric, 2),
    'INR',
    CASE (g % 4) WHEN 0 THEN 'UPI' WHEN 1 THEN 'CARD' WHEN 2 THEN 'WALLET' ELSE 'NETBANKING' END,
    CASE (g % 4) WHEN 0 THEN 'UPI' WHEN 1 THEN 'CARD' WHEN 2 THEN 'WALLET' ELSE 'NETBANKING' END,
    CASE
        WHEN g % 997 < 42 OR (g % 1440 BETWEEN 500 AND 535 AND g % 4 = 0)
            THEN 'FAILED' ELSE 'SUCCESS'
    END,
    CASE WHEN g % 997 < 42 THEN
        CASE (g % 3) WHEN 0 THEN 'NETWORK_ERROR' WHEN 1 THEN 'INSUFFICIENT_FUNDS' ELSE 'AUTH_FAILED' END
    ELSE NULL END,
    CASE (g % 5) WHEN 0 THEN 'Delhi' WHEN 1 THEN 'Mumbai' WHEN 2 THEN 'Bangalore' WHEN 3 THEN 'Hyderabad' ELSE 'Pune' END,
    CASE (g % 3) WHEN 0 THEN 'android' WHEN 1 THEN 'ios' ELSE 'web' END,
    (g % 19 = 0),
    80 + ((g * 31) % 1400)
FROM generate_series(1, 2400000) AS series(g)
ON CONFLICT (payment_id) DO NOTHING;
