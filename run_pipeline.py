import argparse
import time

from analytics import refresh_metrics
from etl_load_warehouse import load_warehouse


def main():
    parser = argparse.ArgumentParser(description="Refresh FinAnalytics metrics and anomaly alerts")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval", type=int, default=60)
    args = parser.parse_args()
    while True:
        load_warehouse()
        metric_count = refresh_metrics()
        print(f"Pipeline refresh complete; providers checked: {metric_count}", flush=True)
        if args.once:
            return
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
