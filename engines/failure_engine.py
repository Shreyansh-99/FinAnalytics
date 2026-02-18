import random
from datetime import datetime, timedelta

class FailureEngine:

    def __init__(self):
        self.active_outage_until = None
        self.outage_provider = None

    # --------------------------
    # Random outage trigger
    # --------------------------
    def maybe_trigger_outage(self, now: datetime):

        # small chance each minute
        if self.active_outage_until is None and random.random() < 0.002:
            duration = random.randint(5, 20)  # minutes
            self.active_outage_until = now + timedelta(minutes=duration)
            self.outage_provider = random.choice(["UPI", "CARD", "NETBANKING"])
            print(f"[OUTAGE] {self.outage_provider} down for {duration} min")

        # outage ended
        if self.active_outage_until and now >= self.active_outage_until:
            print(f"[RECOVERY] {self.outage_provider} restored")
            self.active_outage_until = None
            self.outage_provider = None

    # --------------------------
    # Decide payment result
    # --------------------------
    def process_payment(self, payment, user, user_engine):

        base_failure = 0.03  # normal gateway failure

        # risky users fail more
        risk = user_engine.get_user_risk(user)
        failure_prob = base_failure + (risk * 0.25)

        # outage override
        if self.outage_provider == payment.payment_method:
            failure_prob += 0.6

        success = random.random() > failure_prob

        status = "SUCCESS" if success else "FAILED"
        reason = None

        if not success:
            if self.outage_provider == payment.payment_method:
                reason = "BANK_DOWN"
            else:
                reason = random.choice([
                    "INSUFFICIENT_FUNDS",
                    "NETWORK_ERROR",
                    "AUTH_FAILED"
                ])

        # update behavioural stats
        user_engine.update_user_metrics(user, payment.amount, success)

        return status, reason

    # --------------------------
    # Retry logic
    # --------------------------
    def should_retry(self, user):
        """
        Users retry more if confident
        """
        confidence = min(
            1.0,
            user.successful_transactions / max(1, user.total_transactions)
        )

        return random.random() < (0.25 + confidence * 0.5)