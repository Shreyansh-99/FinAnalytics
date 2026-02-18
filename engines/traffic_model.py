from datetime import datetime
import random
from config import BASE_TRAFFIC, WEEKEND_MULTIPLIER, SALARY_DAY_MULTIPLIER

def get_traffic_count(now: datetime) -> int:

    traffic = BASE_TRAFFIC

    # hour effect
    if 0 <= now.hour <= 6:
        traffic *= 0.3
    elif 18 <= now.hour <= 23:
        traffic *= 1.8

    # weekend
    if now.weekday() >= 5:
        traffic *= WEEKEND_MULTIPLIER

    # salary days
    if now.day in [1, 30]:
        traffic *= SALARY_DAY_MULTIPLIER

    return max(1, int(random.gauss(traffic, traffic * 0.15)))