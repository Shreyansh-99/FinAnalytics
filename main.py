import time
import atexit
from datetime import datetime, timedelta

SIMULATION_TIME = datetime(2025, 12, 1, 0, 0, 0)

from engines.traffic_model import get_traffic_count
from engines.user_engine import UserEngine
from engines.payment_engine import create_payment_attempt
from engines.failure_engine import FailureEngine
from db.writer import EventWriter


# ---------------------------
# Initialize system components
# ---------------------------

user_engine = UserEngine()
failure_engine = FailureEngine()
writer = EventWriter()

# ensure buffered events are written on exit
atexit.register(writer.flush)

print("FinAnalytics Simulator Started...\n")


# ---------------------------
# Main event loop (runs forever)
# ---------------------------

while True:

  #  now = datetime.now()
    now = SIMULATION_TIME

    # 1) Possibly trigger or recover outage
    failure_engine.maybe_trigger_outage(now)

    # 2) Determine traffic this minute
    traffic = get_traffic_count(now)

    # 3) Select active users
    active_users = user_engine.get_active_users(now, traffic)

    # 4) Process each user's payment attempt
    for user in active_users:

        # Create payment attempt
        payment = create_payment_attempt(user, now, user_engine)

        # Process payment outcome
        status, reason = failure_engine.process_payment(payment, user, user_engine)

        event = {
            "time": now,
            "payment_id": payment.payment_id,
            "order_id": payment.order_id,
            "user": user.user_id,
            "amount": payment.amount,
            "method": payment.payment_method,
            "status": status,
            "reason": reason,
            "retry": False
        }

        writer.log_event(event)

        # ---------------------------
        # Retry logic
        # ---------------------------
        if status == "FAILED" and failure_engine.should_retry(user):

            retry_payment = create_payment_attempt(user, now, user_engine)
            status2, reason2 = failure_engine.process_payment(retry_payment, user, user_engine)

            retry_event = {
                "time": now,
                "payment_id": retry_payment.payment_id,
                "order_id": retry_payment.order_id,
                "user": user.user_id,
                "amount": retry_payment.amount,
                "method": retry_payment.payment_method,
                "status": status2,
                "reason": reason2,
                "retry": True
            }

            writer.log_event(retry_event)

    # ---------------------------
    # Wait until next minute
    # ---------------------------
    SIMULATION_TIME += timedelta(minutes=1)
    time.sleep(0.1)