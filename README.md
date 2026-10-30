# FinAnalytics

FinAnalytics is a production-style payment analytics platform built with Python, PostgreSQL, and Streamlit. It simulates payment traffic, persists an auditable event stream, builds warehouse projections, detects provider reliability issues, and exposes the results through an operations dashboard.

## Why this project matters

This project demonstrates practical backend and data-engineering skills in one workflow:

- Event-driven payment simulation with retries, latency, provider failures, and bank outages.
- PostgreSQL data modeling across raw, warehouse, and mart layers.
- Batch ingestion with idempotency and reconnect handling.
- Deterministic historical data generation for repeatable analysis.
- Provider-level metrics and threshold-based anomaly detection.
- A Docker Compose environment with separate simulator, processing, database, and dashboard services.
- Automated tests for core payment and failure behavior.

## Architecture

```text
Traffic simulator
       |
       v
raw.payment_events  -->  warehouse.fact_payments  -->  marts.realtime_metrics
       |                         |                              |
       +-------------------------+------------------------------+
                                 v
                         marts.anomaly_alerts
                                 |
                                 v
                         Streamlit dashboard
```

The raw event table remains the source of truth. Warehouse and mart tables are rebuildable projections, which keeps ingestion concerns separate from reporting and makes downstream transformations easier to change safely.

## Technical highlights

### Reliable ingestion

`db/writer.py` buffers events and writes them in batches. Database conflicts are handled with an idempotency key so a retried batch does not create duplicate events. The writer also reconnects after transient database failures and drains its queue during shutdown.

### Analytical data model

The SQL layer creates:

- `raw.payment_events` for the append-oriented event history.
- `warehouse.fact_payments`, `warehouse.dim_users`, and `warehouse.dim_date` for analytical queries.
- `marts.realtime_metrics`, `marts.daily_metrics`, and `marts.anomaly_alerts` for dashboard and operational use cases.

### Anomaly detection

The analytics job compares each provider's recent failure rate with its seven-day baseline. Alerts include the provider, metric, time bucket, evidence, and severity. A unique alert fingerprint prevents the same incident from being emitted repeatedly.

### Reproducible local environment

Docker Compose starts PostgreSQL, the simulator, the processing worker, and the dashboard as separate services. The historical seed is deterministic, which makes local demos and debugging repeatable.

## Repository structure

| Path | Purpose |
| --- | --- |
| `main.py` | Generates simulated payment events |
| `engines/` | Traffic, user, payment, and failure behavior |
| `db/` | PostgreSQL connection, batching, and resume logic |
| `sql/` | Schemas, historical seed, and upgrade migrations |
| `etl_load_warehouse.py` | Projects raw events into warehouse tables |
| `analytics.py` | Refreshes metrics and creates anomaly alerts |
| `run_pipeline.py` | Runs the processing jobs on a schedule |
| `dashboard.py` | Streamlit operations dashboard |
| `tests/` | Tests for core business rules |

## Run locally

### Prerequisites

- Docker Desktop with Docker Compose
- Python 3.11+ for running individual processes or tests

### Start the full stack

```bash
cp .env.example .env
docker compose up --build
```

Open the dashboard at [http://localhost:8501](http://localhost:8501).

The first PostgreSQL startup applies the schema and historical seed scripts. The seed creates 2.4 million deterministic historical events, so allow extra time and disk space on the first run.

### Run components individually

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

python main.py --minutes 60 --rate-limit 250 --seed 42
python run_pipeline.py --once
streamlit run dashboard.py
```

Run the test suite with:

```bash
pytest
```

## Configuration

Copy `.env.example` to `.env` and adjust the database URL, connection pool limits, simulator rate, batch size, and anomaly-detection thresholds. `.env` is ignored by Git so local credentials are not committed.

## Engineering trade-offs

This is a portfolio-scale system rather than a payment processor. The design intentionally favors clarity and reproducibility. A production deployment would add a durable message broker, exponential backoff with jitter, dead-letter handling, authentication and authorization, stronger alert calibration, observability, and secrets management through the deployment platform.

## License

No license has been selected yet. Add one before distributing or accepting external contributions.
