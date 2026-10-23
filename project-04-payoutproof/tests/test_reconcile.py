import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from payoutproof.ingestion import InputError, parse_bank_csv, validate_processor_event
from payoutproof.ledger import Ledger
from payoutproof.reconcile import Reconciler, WebhookNotifier


FIXTURES = Path(__file__).parents[1] / "fixtures"


class FailingNotifier:
    def deliver(self, alert):
        raise RuntimeError("finance endpoint offline")


class ReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.ledger = Ledger(str(Path(self.temp.name) / "finance.sqlite"))
        self.events = json.loads((FIXTURES / "processor_events.json").read_text(encoding="utf-8"))
        for item in self.events:
            self.ledger.save_processor_event(validate_processor_event(item))
        self.bank_csv = (FIXTURES / "bank_statement.csv").read_text(encoding="utf-8")
        self.ledger.import_bank_rows(parse_bank_csv(self.bank_csv))

    def test_reconcile_reports_matched_mismatch_processor_only_and_bank_only(self):
        results = Reconciler(self.ledger).run()
        by_id = {item["payout_ref"]: item for item in results}
        self.assertEqual(by_id["po-001"]["state"], "matched")
        self.assertEqual(by_id["po-002"]["state"], "amount_mismatch")
        self.assertEqual(by_id["po-002"]["delta_cents"], -500)
        self.assertEqual(by_id["po-003"]["state"], "processor_only")
        self.assertEqual(by_id["po-bank-only"]["state"], "bank_only")
        self.assertEqual(len(self.ledger.alerts()), 3)

    def test_repeated_processor_event_and_bank_import_are_idempotent(self):
        duplicate = validate_processor_event(self.events[0])
        self.assertFalse(self.ledger.save_processor_event(duplicate))
        result = self.ledger.import_bank_rows(parse_bank_csv(self.bank_csv))
        self.assertEqual(result["duplicates"], 3)
        self.assertEqual(result["inserted"], 0)

    def test_bank_update_changes_next_reconciliation(self):
        correction = "payout_ref,bank_ref,amount,currency,booked_at\npo-002,bank-702,245.00,USD,2026-10-23"
        self.assertEqual(self.ledger.import_bank_rows(parse_bank_csv(correction))["updated"], 1)
        by_id = {item["payout_ref"]: item for item in Reconciler(self.ledger).run()}
        self.assertEqual(by_id["po-002"]["state"], "matched")

    def test_currency_mismatch_is_explicit(self):
        currency_csv = "payout_ref,bank_ref,amount,currency,booked_at\npo-001,bank-701,98.50,CAD,2026-10-23"
        self.ledger.import_bank_rows(parse_bank_csv(currency_csv))
        by_id = {item["payout_ref"]: item for item in Reconciler(self.ledger).run()}
        self.assertEqual(by_id["po-001"]["state"], "currency_mismatch")

    def test_invalid_processor_amount_and_event_type_are_rejected(self):
        item = json.loads(json.dumps(self.events[0]))
        item["data"]["amount_cents"] = True
        with self.assertRaises(InputError):
            validate_processor_event(item)
        item = json.loads(json.dumps(self.events[0]))
        item["type"] = "payout.created"
        with self.assertRaises(InputError):
            validate_processor_event(item)

    def test_bad_money_duplicate_rows_and_missing_columns_are_rejected(self):
        for content in (
            "payout_ref,bank_ref,amount,currency,booked_at\np1,b1,1.001,USD,2026-10-23",
            "payout_ref,bank_ref,amount,currency,booked_at\np1,b1,1.00,USD,2026-10-23\np1,b2,2.00,USD,2026-10-23",
            "payout_ref,amount\np1,1.00",
        ):
            with self.subTest(content=content), self.assertRaises(InputError):
                parse_bank_csv(content)

    def test_bank_ref_conflict_rolls_back_import(self):
        content = "payout_ref,bank_ref,amount,currency,booked_at\npo-new,bank-701,10.00,USD,2026-10-23"
        with self.assertRaises(ValueError):
            self.ledger.import_bank_rows(parse_bank_csv(content))
        _, bank = self.ledger.source_records()
        self.assertNotIn("po-new", bank)

    def test_webhook_failure_keeps_alert_pending(self):
        Reconciler(self.ledger, FailingNotifier()).run()
        pending = self.ledger.pending_alerts()
        self.assertEqual(len(pending), 3)
        self.assertIn("offline", pending[0]["last_error"])

    def test_resolved_pending_alert_can_be_reopened_if_mismatch_returns(self):
        Reconciler(self.ledger, FailingNotifier()).run()
        corrected = "payout_ref,bank_ref,amount,currency,booked_at\npo-002,bank-702,245.00,USD,2026-10-23"
        self.ledger.import_bank_rows(parse_bank_csv(corrected))
        Reconciler(self.ledger, FailingNotifier()).run()
        resolved = [row for row in self.ledger.alerts() if row["payout_ref"] == "po-002"]
        self.assertEqual(resolved[0]["delivery_state"], "resolved")
        original = "payout_ref,bank_ref,amount,currency,booked_at\npo-002,bank-702,240.00,USD,2026-10-23"
        self.ledger.import_bank_rows(parse_bank_csv(original))
        Reconciler(self.ledger, FailingNotifier()).run()
        reopened = [row for row in self.ledger.alerts() if row["payout_ref"] == "po-002"]
        self.assertEqual(reopened[0]["delivery_state"], "pending")

    def test_webhook_posts_alert_with_idempotency_key(self):
        received = []

        class Receiver(BaseHTTPRequestHandler):
            def do_POST(inner_self):
                payload = json.loads(inner_self.rfile.read(int(inner_self.headers["Content-Length"])))
                received.append((payload, inner_self.headers.get("Idempotency-Key")))
                inner_self.send_response(202)
                inner_self.end_headers()

            def log_message(inner_self, fmt, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Receiver)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join, 2)
        self.addCleanup(server.shutdown)
        reconciler = Reconciler(self.ledger, WebhookNotifier(
            f"http://127.0.0.1:{server.server_port}/finance-alerts"))
        reconciler.run()
        self.assertEqual(len(received), 3)
        self.assertTrue(all(payload["idempotency_key"] == key for payload, key in received))
        self.assertTrue(all(row["delivery_state"] == "delivered" for row in self.ledger.alerts()))


if __name__ == "__main__":
    unittest.main()
