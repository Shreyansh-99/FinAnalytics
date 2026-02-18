import random

BASE_TRAFFIC=30

WEEKEND_MULTIPLIER=1.6

SALARY_DAY_MULTIPLIER=2.2

PAYMENT_METHODS = {
    "UPI":0.75,
    "CARD":0.8,
    "WALLET":0.9,
    "NETBANKING":0.8
    }

FALIURE_RATES= {
    "UPI":0.045,
    "CARD":0.02,
    "WALLET":0.07,
    "NETBANKING":0.04

}

CITIES = ["Delhi", "Mumbai", "Bangalore", "Hyderabad", "Pune"]
DEVICES = ["android", "ios", "web"]
