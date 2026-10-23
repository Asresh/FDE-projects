# Demo flow

## 1. Start the API

Run `make setup` and `make run` from the project folder. The app creates a local SQLite ledger at `./data/payoutproof.sqlite`.

## 2. Load the synthetic records

```sh
curl -X POST http://127.0.0.1:8090/api/demo
```

The processor adapter receives three settlement events. The bank CSV import contains a matched deposit, a deposit that is $5.00 short, and a bank-only line. One processor payout has no bank line.

## 3. Reconcile and inspect

```sh
curl -X POST http://127.0.0.1:8090/api/reconcile
curl http://127.0.0.1:8090/api/reconciliations
curl http://127.0.0.1:8090/api/outbox
```

Expected statuses are one `matched`, one `amount_mismatch`, one `processor_only`, and one `bank_only`. The three exceptions are saved as review notifications in the mock outbox.

## 4. Try operational edge cases

- Repeat a processor event: its event ID is deduplicated.
- Repeat a bank statement row: the same bank reference is handled idempotently.
- Change a deposit amount and re-import it: the next reconciliation reflects the new evidence.
- Send a negative amount, malformed decimal, missing column, duplicate payout reference, or unsupported currency: the import is rejected with an actionable 400 response.
- Set `FINANCE_ALERT_WEBHOOK_URL` to a local receiver: successful deliveries include an idempotency key. If the endpoint fails, the exception and outbox entry remain available for follow-up.

## Health and safety

`GET /health` checks that SQLite can answer a query. Reconciliation only reports differences. A finance operator must validate evidence and choose the accounting action in the real source systems.
