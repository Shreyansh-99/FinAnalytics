from db.connection import get_connection

conn = get_connection()
cur = conn.cursor()

cur.execute("""
INSERT INTO marts.daily_metrics
SELECT
    DATE(payment_time) as date,
    COUNT(*) as total_transactions,
    COUNT(*) FILTER (WHERE final_status='SUCCESS'),
    COUNT(*) FILTER (WHERE final_status='FAILED'),
    SUM(amount) FILTER (WHERE final_status='SUCCESS'),
    COUNT(DISTINCT user_id)
FROM warehouse.fact_payments
GROUP BY DATE(payment_time)
ON CONFLICT (date) DO UPDATE SET
    total_transactions = EXCLUDED.total_transactions,
    successful_transactions = EXCLUDED.successful_transactions,
    failed_transactions = EXCLUDED.failed_transactions,
    total_revenue = EXCLUDED.total_revenue,
    unique_users = EXCLUDED.unique_users;
""")

conn.commit()
print("Daily metrics updated")