# Demo flow

## 1. Start the service

In the project directory, run `make setup`, then `make run`. The service uses a local SQLite file at `./data/coldchain.sqlite` and logs JSON records to standard output.

## 2. Load the synthetic customer data

```sh
curl -X POST http://127.0.0.1:8080/api/demo
```

The demo imports three inventory lots and submits two sensor gateway events. The west cold-room excursion should open a case associated with `LOT-ICE-2401` and `LOT-ICE-2402`; the normal east-room reading should not open one.

## 3. Inspect cases and notifications

```sh
curl http://127.0.0.1:8080/api/cases
curl http://127.0.0.1:8080/api/outbox
curl http://127.0.0.1:8080/health
```

In demo mode, the ticket notification is saved in the local outbox with `delivery_state` set to `mock`. The outbox payload includes a stable idempotency key so a real ticketing adapter can avoid duplicate tickets.

## 4. Exercise edge cases

Send the same event again to see duplicate suppression. Then try a missing field, an invalid timestamp, a boolean temperature, an unknown location, or a temperature far outside range. Invalid payloads receive HTTP 400; an unknown location opens a high-severity review case without inventing affected lots. A configured webhook failure leaves the case intact and its outbox record pending with a short error.

## Acceptance checks

- Event IDs are unique per sensor and repeated events do not create duplicate cases.
- A normal reading is stored but does not create a case.
- Out-of-range readings create evidence-linked cases for affected lots.
- Missing inventory mapping is surfaced as an exception instead of silently dropped.
- A downstream webhook failure does not lose the reading, case, or notification intent.
- Health check verifies the database can be queried.
