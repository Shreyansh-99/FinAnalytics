from datetime import datetime

from engines.failure_engine import FailureEngine
from engines.payment_engine import choose_payment_method
from engines.user_engine import User


class UserEngineStub:
    def get_user_risk(self, user):
        return 0.0

    def update_user_metrics(self, user, amount, success):
        user.total_transactions += 1
        user.successful_transactions += int(success)
        user.failed_transactions += int(not success)


def test_payment_method_is_supported():
    assert choose_payment_method(0.2) in {"UPI", "CARD", "WALLET", "NETBANKING"}


def test_outage_forces_provider_failure():
    engine = FailureEngine()
    engine.outage_provider = "UPI"
    user = User(1, datetime.now(), datetime.now(), 0.5)
    payment = type("Payment", (), {"payment_method": "UPI", "amount": 100})()
    status, reason = engine.process_payment(payment, user, UserEngineStub())
    assert status == "FAILED"
    assert reason == "BANK_DOWN"
