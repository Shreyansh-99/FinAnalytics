from db.connection import get_connection
import statistics

conn = get_connection()
cur = conn.cursor()

# fetch last 30 days metrics
cur.execute("""
SELECT date, total_revenue
FROM marts.daily_metrics
ORDER BY date DESC
LIMIT 30;
""")

rows = cur.fetchall()

if len(rows) < 10:
    print("Not enough data yet")
    exit()

# separate today and history
today_date, today_value = rows[0]
history = [r[1] for r in rows[1:]]

mean = statistics.mean(history)
std = statistics.stdev(history)

lower_bound = mean - 2 * std

if today_value < lower_bound:

    deviation = today_value - mean

    cur.execute("""
    INSERT INTO marts.anomaly_alerts
    (date, metric, metric_value, expected_value, deviation, alert_level)
    VALUES (%s,%s,%s,%s,%s,%s)
    """, (
        today_date,
        "revenue",
        today_value,
        mean,
        deviation,
        "HIGH"
    ))

    conn.commit()
    print("⚠ Revenue anomaly detected!")
else:
    print("No anomaly")