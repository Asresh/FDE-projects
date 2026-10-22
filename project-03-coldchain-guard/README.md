# ColdChain Guard

ColdChain Guard helps a food or pharmacy distribution team catch a cold-room temperature excursion, determine which inventory lots may be affected, and create a reviewable response case. It turns sensor readings and inventory records into one workflow with a visible evidence trail.

## Architecture

1. **Sensor gateway adapter** accepts JSON readings like an edge MQTT gateway export.
2. **Policy and case service** validates the reading, checks product limits, correlates it with inventory lots, and records an excursion case in SQLite.
3. **Notification outbox** records a webhook-shaped ticket notification with an idempotency key. Demo mode delivers it to a local mock receiver; deployments can configure an outbound webhook.

The system never declares product safe or unsafe for sale. It flags readings for an authorized quality operator and preserves the sensor evidence and lot links. See [`docs/architecture.svg`](docs/architecture.svg) and [`docs/demo_flow.md`](docs/demo_flow.md).

## Setup

Requires Python 3.9+ and Make. There are no third-party dependencies.

```bash
make setup
make run
```

The service listens on `http://127.0.0.1:8080`. Load sample lots and readings:

```bash
curl -X POST http://127.0.0.1:8080/api/demo
curl http://127.0.0.1:8080/api/cases
curl http://127.0.0.1:8080/api/outbox
curl http://127.0.0.1:8080/health
```

Submit an individual reading:

```bash
curl -X POST http://127.0.0.1:8080/api/telemetry \
  -H 'Content-Type: application/json' \
  -d '{"event_id":"evt-1001","sensor_id":"sensor-west-1","location_id":"cold-room-west","observed_at":"2026-10-22T08:10:00Z","temperature_c":9.1}'
```

The demo uses synthetic fixtures. Set `DATABASE_PATH` to choose the SQLite file, `PORT` to change the listen port, and optionally `TICKETING_WEBHOOK_URL` to deliver notifications to an HTTP webhook. Without that URL notifications stay in the local outbox for review.

## Checks

```bash
make test
make check
```

`make check` runs the unit and integration tests and Python bytecode compilation. No external service is needed.

## Deployment

Build and run the included container locally:

```bash
docker build -t coldchain-guard .
docker run --rm -p 8080:8080 -v coldchain-data:/data \
  -e DATABASE_PATH=/data/coldchain.sqlite coldchain-guard
```

`GET /health` reports process health and SQLite connectivity. Logs are one JSON object per line with timestamp, level, event, and request context. The image runs as a non-root user.

## Limitations

- Demo sensor events stand in for an MQTT broker; production deployments need customer-specific device identity, broker authentication, network policy, and replay protection.
- The included inventory import is a synthetic SQLite-backed ERP boundary, not a connector to a customer's ERP.
- Webhook delivery is best-effort; the durable outbox remains the source of truth if a remote endpoint is unavailable. Retries and dead-letter operations require an operator or production queue integration.
- Temperature policy is a simple example. Product, jurisdiction, excursion duration, calibration, and disposition rules must be approved by a qualified quality owner.
- This prototype is not a food-safety or pharmaceutical compliance system and is not validated for production use.

## Project files

- [`docs/job_market_research.md`](docs/job_market_research.md): current postings, compensation, and design implications.
- [`docs/demo_flow.md`](docs/demo_flow.md): operator walkthrough and API examples.
- [`docs/architecture.svg`](docs/architecture.svg): component and integration view.
- `coldchain/`: service, policy, SQLite repository, and webhook adapter.
- `tests/`: unit, API integration, idempotency, validation, and failure-path tests.

**Author: Asresh**
