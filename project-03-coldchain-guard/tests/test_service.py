import json
import math
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from coldchain.repository import Repository
from coldchain.service import ColdChainService, InputError, WebhookNotifier, validate_event


def event(event_id="evt-1", temperature=9.1, location="cold-room-west"):
    return {"event_id": event_id, "sensor_id": "sensor-west-1", "location_id": location,
            "observed_at": "2026-10-22T08:10:00Z", "temperature_c": temperature}


class FailingNotifier:
    def deliver(self, payload):
        raise RuntimeError("ticket system unavailable")


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Repository(str(Path(self.temp.name) / "test.sqlite"))
        fixture = Path(__file__).parents[1] / "fixtures" / "inventory.json"
        self.repo.import_inventory(json.loads(fixture.read_text(encoding="utf-8")))
        self.service = ColdChainService(self.repo)

    def test_excursion_opens_case_for_each_affected_lot(self):
        result = self.service.ingest(event())
        self.assertEqual(result["case"]["severity"], "high")
        self.assertEqual(result["case"]["lot_ids"], ["LOT-ICE-2401", "LOT-ICE-2402"])
        self.assertEqual(result["notification"], "mock")

    def test_extreme_excursion_is_critical(self):
        result = self.service.ingest(event(temperature=12.0))
        self.assertEqual(result["case"]["severity"], "critical")

    def test_normal_reading_is_stored_without_case(self):
        result = self.service.ingest(event(temperature=4.0))
        self.assertIsNone(result["case"])
        self.assertEqual(self.repo.cases(), [])

    def test_duplicate_sensor_event_does_not_create_duplicate_case(self):
        first = self.service.ingest(event())
        second = self.service.ingest(event())
        self.assertTrue(second["duplicate"])
        self.assertEqual(first["case"]["id"], second["case"]["id"])
        self.assertEqual(len(self.repo.cases()), 1)
        self.assertEqual(len(self.repo.outbox()), 1)

    def test_unknown_location_creates_review_case_without_lot_claim(self):
        result = self.service.ingest(event(location="unknown-room"))
        self.assertEqual(result["case"]["severity"], "high")
        self.assertEqual(result["case"]["lot_ids"], [])
        self.assertIn("No inventory mapping", result["case"]["summary"])

    def test_webhook_failure_preserves_case_and_pending_outbox(self):
        service = ColdChainService(self.repo, FailingNotifier())
        result = service.ingest(event())
        self.assertEqual(result["notification"], "pending")
        self.assertEqual(len(self.repo.cases()), 1)
        self.assertEqual(self.repo.outbox()[0]["delivery_state"], "pending")
        self.assertIn("unavailable", self.repo.outbox()[0]["last_error"])

    def test_webhook_posts_idempotent_ticket_to_mock_receiver(self):
        received = []

        class Receiver(BaseHTTPRequestHandler):
            def do_POST(inner_self):
                body = json.loads(inner_self.rfile.read(int(inner_self.headers["Content-Length"])))
                received.append((body, inner_self.headers.get("Idempotency-Key")))
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
        notifier = WebhookNotifier(f"http://127.0.0.1:{server.server_port}/tickets")
        result = ColdChainService(self.repo, notifier).ingest(event())
        self.assertEqual(result["notification"], "delivered")
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0][0]["lot_ids"], ["LOT-ICE-2401", "LOT-ICE-2402"])
        self.assertEqual(received[0][0]["idempotency_key"], received[0][1])
        self.assertEqual(self.repo.outbox()[0]["delivery_state"], "delivered")

    def test_validation_rejects_missing_fields_and_bad_timestamp(self):
        with self.assertRaises(InputError):
            validate_event({"event_id": "x"})
        payload = event()
        payload["observed_at"] = "yesterday"
        with self.assertRaises(InputError):
            validate_event(payload)

    def test_validation_rejects_naive_timestamp_boolean_and_nonfinite_temperature(self):
        for timestamp, temperature in (("2026-10-22T08:00:00", 4),
                                       ("2026-10-22T08:00:00Z", True),
                                       ("2026-10-22T08:00:00Z", math.inf)):
            with self.subTest(timestamp=timestamp, temperature=temperature):
                payload = event(temperature=temperature)
                payload["observed_at"] = timestamp
                with self.assertRaises(InputError):
                    validate_event(payload)


if __name__ == "__main__":
    unittest.main()
