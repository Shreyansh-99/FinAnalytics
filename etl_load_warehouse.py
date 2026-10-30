from db.connection import connection_cursor


def load_warehouse():
    with connection_cursor() as (_, cur):
        cur.execute("""
            INSERT INTO warehouse.fact_payments
                (payment_id, order_id, user_id, payment_time, amount,
                 payment_method, provider, final_status, failure_reason, is_retry)
            WITH ranked_events AS (
                SELECT payment_id, order_id, user_id, event_time, amount,
                       payment_method, provider, status, failure_reason, is_retry,
                       ROW_NUMBER() OVER (
                           PARTITION BY payment_id
                           ORDER BY event_time DESC, event_id DESC
                       ) AS row_number
                FROM raw.payment_events
            )
            SELECT payment_id, order_id, user_id, event_time, amount,
                   payment_method, provider, status, failure_reason, is_retry
            FROM ranked_events
            WHERE row_number = 1
            ON CONFLICT (payment_id) DO UPDATE SET
                final_status=EXCLUDED.final_status,
                failure_reason=EXCLUDED.failure_reason,
                provider=EXCLUDED.provider;
        """)
        cur.execute("""
            INSERT INTO warehouse.dim_users
            SELECT user_id, MIN(payment_time), MAX(payment_time), COUNT(*),
                   COUNT(*) FILTER (WHERE final_status='SUCCESS'),
                   COUNT(*) FILTER (WHERE final_status='FAILED'),
                   COALESCE(SUM(amount) FILTER (WHERE final_status='SUCCESS'), 0)
            FROM warehouse.fact_payments
            GROUP BY user_id
            ON CONFLICT (user_id) DO UPDATE SET
                last_seen=EXCLUDED.last_seen, total_payments=EXCLUDED.total_payments,
                successful_payments=EXCLUDED.successful_payments,
                failed_payments=EXCLUDED.failed_payments, total_amount=EXCLUDED.total_amount;
        """)
        cur.execute("""
            INSERT INTO warehouse.dim_date
            SELECT DISTINCT payment_time::date, EXTRACT(DAY FROM payment_time)::int,
                   EXTRACT(MONTH FROM payment_time)::int, EXTRACT(YEAR FROM payment_time)::int,
                   EXTRACT(DOW FROM payment_time)::int,
                   EXTRACT(DOW FROM payment_time)::int IN (0, 6)
            FROM warehouse.fact_payments
            ON CONFLICT (date) DO NOTHING;
        """)


if __name__ == "__main__":
    load_warehouse()
    print("Warehouse projections updated")
