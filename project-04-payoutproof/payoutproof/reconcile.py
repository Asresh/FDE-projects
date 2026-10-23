"""Deterministic settlement matcher and webhook alert delivery."""

import json
import urllib.error
import urllib.request
from datetime import datetime, timezone


class WebhookNotifier:
    def __init__(self, url=None, timeout=3):
        self.url = url
        self.timeout = timeout

    def deliver(self, alert):
        if not self.url:
            return "mock"
        body = json.dumps(alert, sort_keys=True).encode("utf-8")
        request = urllib.request.Request(
            self.url, data=body, method="POST",
            headers={"Content-Type": "application/json",
                     "Idempotency-Key": alert["idempotency_key"]})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                if response.status >= 300:
                    raise RuntimeError(f"finance webhook returned HTTP {response.status}")
        except (urllib.error.URLError, TimeoutError) as exc:
            raise RuntimeError(f"finance webhook delivery failed: {exc}") from exc
        return "delivered"


class Reconciler:
    def __init__(self, ledger, notifier=None):
        self.ledger = ledger
        self.notifier = notifier or WebhookNotifier()

    def run(self):
        processor, bank = self.ledger.source_records()
        output = []
        for payout_ref in sorted(set(processor) | set(bank)):
            p = processor.get(payout_ref)
            b = bank.get(payout_ref)
            p_cents = p["amount_cents"] if p else None
            b_cents = b["amount_cents"] if b else None
            p_currency = p["currency"] if p else None
            b_currency = b["currency"] if b else None
            delta = b_cents - p_cents if p and b else None
            if not p:
                state = "bank_only"
                detail = f"Bank deposit {b['bank_ref']} has no matching processor payout."
            elif not b:
                state = "processor_only"
                detail = "Processor payout is not present in the imported bank statement."
            elif p_currency != b_currency:
                state = "currency_mismatch"
                detail = f"Currency differs: processor {p_currency}, bank {b_currency}."
            elif p_cents != b_cents:
                state = "amount_mismatch"
                detail = (f"Bank amount differs by {delta:+d} cents "
                          f"(bank minus processor) for payout {payout_ref}.")
            else:
                state = "matched"
                detail = "Payout ID, amount, and currency match across both sources."
            output.append({"payout_ref": payout_ref, "state": state,
                           "processor_cents": p_cents, "bank_cents": b_cents,
                           "processor_currency": p_currency, "bank_currency": b_currency,
                           "delta_cents": delta, "detail": detail})

        self.ledger.save_reconciliations(output, datetime.now(timezone.utc).isoformat())
        for queued in self.ledger.pending_alerts():
            try:
                alert = json.loads(queued["payload"])
                alert["idempotency_key"] = queued["alert_key"]
                state = self.notifier.deliver(alert)
                self.ledger.mark_alert(queued["alert_key"], state)
            except Exception as exc:  # keep the alert durable when its receiver is offline
                self.ledger.mark_alert(queued["alert_key"], "pending", str(exc)[:500])
        return output
