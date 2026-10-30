from datetime import datetime, timedelta, timezone
from db.connection import get_connection

DEFAULT_START = datetime(2025, 12, 1, 0, 0, 0)

def get_start_time():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT MAX(event_time) FROM raw.payment_events;")
            row = cur.fetchone()
    finally:
        conn.close()

    if row and row[0]:
        resume_time = row[0] + timedelta(minutes=1)
        current_time = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        if resume_time.tzinfo is None:
            resume_time = resume_time.replace(tzinfo=timezone.utc)
        # Do not spend days replaying stale history when starting live services.
        if resume_time < current_time - timedelta(hours=24):
            return current_time
        return resume_time

    return DEFAULT_START
