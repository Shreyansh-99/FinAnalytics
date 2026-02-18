from db.connection import get_connection

conn = get_connection()
cur = conn.cursor()

cur.execute("""
    SELECT DISTINCT ON (payment_id)
        payment_id,
        order_id,
        user_id,
        event_time,
        amount,
        payment_method,
        status
    FROM raw.payment_events
    ORDER BY payment_id, event_time DESC
""")

final_payments = cur.fetchall()

print("Payments extracted:", len(final_payments))


cur.executemany("""
    INSERT INTO warehouse.fact_payments (
        payment_id, order_id, user_id,
        payment_time, amount, payment_method, final_status
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s)
    ON CONFLICT (payment_id) DO NOTHING
""", final_payments)

conn.commit()
print("Fact table updated")

cur.execute("""
    INSERT INTO warehouse.dim_users
    SELECT
        user_id,
        MIN(payment_time),
        MAX(payment_time),
        COUNT(*),
        COUNT(*) FILTER (WHERE final_status='SUCCESS'),
        COUNT(*) FILTER (WHERE final_status='FAILED'),
        SUM(amount) FILTER (WHERE final_status='SUCCESS')
    FROM warehouse.fact_payments
    GROUP BY user_id
    ON CONFLICT (user_id)
    DO UPDATE SET
        last_seen = EXCLUDED.last_seen,
        total_payments = EXCLUDED.total_payments,
        successful_payments = EXCLUDED.successful_payments,
        failed_payments = EXCLUDED.failed_payments,
        total_amount = EXCLUDED.total_amount;
""")

conn.commit()
print("User dimension updated")

cur.execute("""
    INSERT INTO warehouse.dim_date
    SELECT DISTINCT
        DATE(payment_time) as date,
        EXTRACT(DAY FROM payment_time),
        EXTRACT(MONTH FROM payment_time),
        EXTRACT(YEAR FROM payment_time),
        EXTRACT(DOW FROM payment_time),
        CASE WHEN EXTRACT(DOW FROM payment_time) IN (0,6) THEN TRUE ELSE FALSE END
    FROM warehouse.fact_payments
    ON CONFLICT (date) DO NOTHING
""")

conn.commit()
print("Date dimension updated")