import random
from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    user_id: int
    created_at: datetime
    last_active: datetime

     # hidden economic trait
    spending_power: float

    # behavioural counters
    total_transactions: int = 0
    successful_transactions: int = 0
    failed_transactions: int = 0
    total_amount: float = 0.0


class UserEngine:

    def __init__(self):
        self.users = {}
        self.next_id = 1

    # ---------- user creation ----------
    def _create_new_user(self, now: datetime) -> User:
        user = User(
            user_id=self.next_id,
            created_at=now,
            last_active=now,
            spending_power=self._assign_spending_power()
        )
        self.users[self.next_id] = user
        self.next_id += 1
        return user

    # ---------- who is active right now ----------
    def get_active_users(self, now: datetime, traffic_count: int):

        active_users = []

        for _ in range(traffic_count):

            # 25% chance platform gets a brand new signup
            if len(self.users) == 0 or random.random() < 0.25:
                user = self._create_new_user(now)

            else:
                # returning user bias toward recently active users
                recent_users = [
                    u for u in self.users.values()
                    if (now - u.last_active).total_seconds() < 3600 * 24
                ]

                if recent_users and random.random() < 0.7:
                    user = random.choice(recent_users)
                else:
                    user = random.choice(list(self.users.values()))

            user.last_active = now
            active_users.append(user)

        return active_users

    # ---------- update behaviour after payment result ----------
    def update_user_metrics(self, user: User, amount: float, success: bool):
        user.total_transactions += 1
        user.total_amount += amount

        if success:
            user.successful_transactions += 1
        else:
            user.failed_transactions += 1

    # ---------- derived behavioural features ----------
    def get_user_confidence(self, user: User) -> float:
        """
        Confidence grows when payments succeed.
        0 → unsure user
        1 → highly confident user
        """
        if user.total_transactions == 0:
            return 0.2

        success_rate = user.successful_transactions / user.total_transactions
        return min(1.0, 0.3 + success_rate * 0.7)
    
    def _assign_spending_power(self) -> float:
        r = random.random()

    # population distribution (realistic inequality)
        if r < 0.60:          # majority low income
            return random.uniform(0.2, 0.5)

        elif r < 0.90:        # middle class
            return random.uniform(0.5, 0.9)

        else:                 # affluent
            return random.uniform(0.9, 1.5)



    def get_user_risk(self, user: User) -> float:
        """
        Higher failure ratio = risky behaviour
        """
        if user.total_transactions == 0:
            return 0.1

        return min(1.0, user.failed_transactions / user.total_transactions)