import argparse
import atexit
import random
import time
import uuid
from datetime import timedelta, timezone

from db.bootstrap import get_start_time
from db.writer import EventWriter
from engines.failure_engine import FailureEngine
from engines.payment_engine import create_payment_attempt
from engines.traffic_model import get_traffic_count
from engines.user_engine import UserEngine


def run_simulation(minutes=None, rate_limit=250, seed=None):
    if seed is not None:
        random.seed(seed)
    simulation_time = get_start_time()
    if simulation_time.tzinfo is None:
        simulation_time = simulation_time.replace(tzinfo=timezone.utc)
    user_engine = UserEngine()
    failure_engine = FailureEngine()
    writer = EventWriter()
    atexit.register(writer.stop)
    deadline = None if minutes is None else simulation_time + timedelta(minutes=minutes)
    interval = 1 / rate_limit if rate_limit > 0 else 0
    try:
        while deadline is None or simulation_time < deadline:
            failure_engine.maybe_trigger_outage(simulation_time)
            for user in user_engine.get_active_users(simulation_time, get_traffic_count(simulation_time)):
                payment = create_payment_attempt(user, simulation_time, user_engine)
                status, reason = failure_engine.process_payment(payment, user, user_engine)
                writer.log_event({
                    "event_key": f"evt_{uuid.uuid4().hex}",
                    "time": simulation_time, "payment_id": payment.payment_id,
                    "order_id": payment.order_id, "user": user.user_id,
                    "amount": payment.amount, "method": payment.payment_method,
                    "provider": payment.payment_method, "status": status, "reason": reason,
                    "city": payment.city, "device": payment.device, "retry": False,
                    "latency_ms": random.randint(80, 1600),
                })
                if status == "FAILED" and failure_engine.should_retry(user):
                    retry = create_payment_attempt(user, simulation_time, user_engine)
                    retry_status, retry_reason = failure_engine.process_payment(retry, user, user_engine)
                    writer.log_event({
                        "event_key": f"evt_{uuid.uuid4().hex}",
                        "time": simulation_time, "payment_id": retry.payment_id,
                        "order_id": payment.order_id, "user": user.user_id,
                        "amount": retry.amount, "method": retry.payment_method,
                        "provider": retry.payment_method, "status": retry_status,
                        "reason": retry_reason, "city": retry.city, "device": retry.device,
                        "retry": True, "latency_ms": random.randint(100, 2200),
                    })
                if interval:
                    time.sleep(interval)
            simulation_time += timedelta(minutes=1)
    finally:
        writer.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the FinAnalytics payment event simulator")
    parser.add_argument("--minutes", type=int, default=60, help="simulation minutes; use 0 for continuous")
    parser.add_argument("--rate-limit", type=float, default=250, help="maximum events per second")
    parser.add_argument("--seed", type=int, help="reproducible random seed")
    args = parser.parse_args()
    run_simulation(None if args.minutes == 0 else args.minutes, args.rate_limit, args.seed)
