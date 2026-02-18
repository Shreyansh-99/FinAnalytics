from db.connection import get_connection
from datetime import date, timedelta

conn = get_connection()
cur = conn.cursor()

# latest anomaly
cur.execute("""
SELECT date FROM marts.anomaly_alerts
ORDER BY created_at DESC
LIMIT 1;
""")

row = cur.fetchone()

if not row:
    print("No anomaly to explain")
    exit()

anomaly_date = row[0]
baseline_start = anomaly_date - timedelta(days=7)

# success rate per method (baseline)
cur.execute("""
SELECT payment_method,
       AVG(CASE WHEN final_status='SUCCESS' THEN 1 ELSE 0 END)
FROM warehouse.fact_payments
WHERE payment_time >= %s AND payment_time < %s
GROUP BY payment_method;
""", (baseline_start, anomaly_date))

baseline = dict(cur.fetchall())

# success rate today
cur.execute("""
SELECT payment_method,
       AVG(CASE WHEN final_status='SUCCESS' THEN 1 ELSE 0 END)
FROM warehouse.fact_payments
WHERE DATE(payment_time) = %s
GROUP BY payment_method;
""", (anomaly_date,))

today = dict(cur.fetchall())

# compare
for method in today:
    if method in baseline:
        drop = baseline[method] - today[method]

        if drop > 0.15:  # significant drop
            cur.execute("""
            INSERT INTO marts.anomaly_explanations
            (date, metric, reason, evidence)
            VALUES (%s,%s,%s,%s)
            """, (
                anomaly_date,
                "revenue",
                f"{method} success rate dropped",
                drop
            ))

            conn.commit()
            print("Root cause identified:", method)