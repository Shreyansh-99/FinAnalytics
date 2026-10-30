import hashlib
import json
import os
from datetime import datetime, timedelta, timezone

import pandas as pd

from db.connection import connection_cursor


def refresh_metrics(lookback_hours: int = 168) -> int:
    """Refresh realtime rollups and emit deduplicated provider failure alerts."""
    with connection_cursor() as (_, cur):
        cur.execute("""
            INSERT INTO marts.realtime_metrics
            SELECT date_trunc('minute', event_time), provider,
                   COUNT(*), COUNT(*) FILTER (WHERE status='SUCCESS'),
                   COUNT(*) FILTER (WHERE status='FAILED'),
                   COUNT(*) FILTER (WHERE status='FAILED')::numeric / NULLIF(COUNT(*), 0),
                   COALESCE(SUM(amount) FILTER (WHERE status='SUCCESS'), 0)
            FROM raw.payment_events
            WHERE event_time >= now() - (%s * interval '1 hour')
            GROUP BY 1, 2
            ON CONFLICT (bucket_start, provider) DO UPDATE SET
                total_transactions=EXCLUDED.total_transactions,
                successful_transactions=EXCLUDED.successful_transactions,
                failed_transactions=EXCLUDED.failed_transactions,
                failure_rate=EXCLUDED.failure_rate,
                total_revenue=EXCLUDED.total_revenue;
        """, (lookback_hours,))

        cur.execute("""
            SELECT provider, COUNT(*)::float AS total,
                   AVG((status='FAILED')::int)::float AS failure_rate
            FROM raw.payment_events
            WHERE event_time >= now() - interval '15 minutes'
            GROUP BY provider
            HAVING COUNT(*) >= %s
        """, (int(os.getenv("ANOMALY_MIN_EVENTS", "100")),))
        current = cur.fetchall()

        for provider, total, failure_rate in current:
            cur.execute("""
                SELECT AVG(failure_rate)::float
                FROM marts.realtime_metrics
                WHERE provider=%s AND bucket_start >= now() - interval '7 days'
                  AND bucket_start < now() - interval '15 minutes'
            """, (provider,))
            expected = cur.fetchone()[0]
            if expected is None or failure_rate <= expected + 0.05:
                continue
            severity = "CRITICAL" if failure_rate >= expected + 0.20 else "HIGH"
            window_end = datetime.now(timezone.utc)
            window_start = window_end - timedelta(minutes=15)
            fingerprint = hashlib.sha256(
                f"{provider}:failure_rate:{window_start:%Y%m%d%H%M}".encode()
            ).hexdigest()
            cur.execute("""
                INSERT INTO marts.anomaly_alerts
                    (date, window_start, window_end, provider, metric, metric_value,
                     expected_value, deviation, severity, alert_level, evidence, fingerprint)
                VALUES (%s,%s,%s,%s,'failure_rate',%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (fingerprint) DO NOTHING
            """, (window_end.date(), window_start, window_end, provider, failure_rate, expected,
                  failure_rate - expected, severity, severity,
                  json.dumps({"events": total, "window_minutes": 15}), fingerprint))
    return len(current)


def load_dashboard_data(hours: int = 24):
    with connection_cursor() as (_, cur):
        cur.execute("""
            SELECT bucket_start, provider, total_transactions,
                   successful_transactions, failed_transactions,
                   failure_rate, total_revenue
            FROM marts.realtime_metrics
            WHERE bucket_start >= now() - (%s * interval '1 hour')
            ORDER BY bucket_start
        """, (hours,))
        rows = cur.fetchall()
        columns = ["bucket_start", "provider", "total_transactions", "successful_transactions",
                   "failed_transactions", "failure_rate", "total_revenue"]
        metrics = pd.DataFrame(rows, columns=columns)
        cur.execute("""
            SELECT detected_at, provider, metric, metric_value, expected_value, severity, status
            FROM marts.anomaly_alerts ORDER BY detected_at DESC LIMIT 50
        """)
        alerts = pd.DataFrame(cur.fetchall(), columns=["detected_at", "provider", "metric",
                            "metric_value", "expected_value", "severity", "status"])
    return metrics, alerts
