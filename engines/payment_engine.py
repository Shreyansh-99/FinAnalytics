import random
from dataclasses import dataclass
from datetime import datetime
from config import CITIES, DEVICES


@dataclass
class PaymentAttempt:
    payment_id: str
    order_id: str
    user_id: int
    amount: float
    payment_method: str
    city: str
    device: str
    timestamp: datetime


def choose_amount(user, confidence: float) -> float:

    power = user.spending_power
    maturity = min(user.total_transactions / 15, 1.0)  # stabilizes after ~15 tx

    # probability of purchase types
    routine_p = 0.6 - (power * 0.25) + (0.2 * (1 - confidence))
    lifestyle_p = 0.3 + (power * 0.2)
    big_p = 0.1 + (power * 0.25) + (confidence * 0.2)

    # mature users behave more consistently
    noise = (1 - maturity) * random.uniform(-0.15, 0.15)

    routine_p += noise
    lifestyle_p -= noise/2
    big_p -= noise/2

    # normalize
    total = routine_p + lifestyle_p + big_p
    routine_p, lifestyle_p, big_p = (
        routine_p/total, lifestyle_p/total, big_p/total
    )

    tier = random.choices(
        ["routine", "lifestyle", "big"],
        [routine_p, lifestyle_p, big_p]
    )[0]

    if tier == "routine":
        base = random.uniform(40, 400)

    elif tier == "lifestyle":
        base = random.uniform(400, 2500)

    else:  # big purchase
        base = random.uniform(2500, 12000)

    # economic scaling
    amount = base * (0.7 + power * 0.9)

    return round(amount, 2)


# ---------- method selection ----------
def choose_payment_method(risk: float) -> str:

    if risk > 0.6:
        weights = {"UPI":0.6, "WALLET":0.25, "CARD":0.1, "NETBANKING":0.05}

    elif risk > 0.3:
        weights = {"UPI":0.45, "CARD":0.3, "WALLET":0.15, "NETBANKING":0.1}

    else:
        weights = {"CARD":0.45, "UPI":0.3, "NETBANKING":0.15, "WALLET":0.1}

    methods = list(weights.keys())
    probs = list(weights.values())
    return random.choices(methods, probs)[0]


# ---------- create payment ----------
def create_payment_attempt(user, now, user_engine):

    confidence = user_engine.get_user_confidence(user)
    risk = user_engine.get_user_risk(user)

    payment_id = f"pay_{random.randint(10**8,10**9-1)}"
    order_id = f"ord_{random.randint(10**8,10**9-1)}"

    return PaymentAttempt(
        payment_id=payment_id,
        order_id=order_id,
        user_id=user.user_id,
        amount=choose_amount(user, confidence),
        payment_method=choose_payment_method(risk),
        city=random.choice(CITIES),
        device=random.choice(DEVICES),
        timestamp=now
    )