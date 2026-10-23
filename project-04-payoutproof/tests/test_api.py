import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from payoutproof.api import create_server


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.server = create_server(port=0, database_path=str(Path(self.temp.name) / "api.sqlite"))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop_server)
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def stop_server(self):
        self.server.shutdown()
        self.thread.join(timeout=2)
        self.server.server_close()

    def request(self, path, method="GET", payload=None):
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(self.base + path, data=body, method=method,
                                         headers={"Content-Type": "application/json"})
        try:
            response = urllib.request.urlopen(request, timeout=2)
        except urllib.error.HTTPError as exc:
            response = exc
        return response.code, json.loads(response.read())

    def test_health_and_missing_route(self):
        self.assertEqual(self.request("/health")[0], 200)
        code, body = self.request("/missing")
        self.assertEqual(code, 404)
        self.assertEqual(body["error"], "not_found")

    def test_demo_loads_reconciles_and_creates_review_alerts(self):
        code, body = self.request("/api/demo", "POST", {})
        self.assertEqual(code, 200)
        self.assertEqual(body["processor_events_added"], 3)
        self.assertEqual(body["count"], 4)
        self.assertEqual(sum(row["state"] == "matched" for row in body["reconciliations"]), 1)
        _, alerts = self.request("/api/outbox")
        self.assertEqual(len(alerts["alerts"]), 3)

    def test_invalid_bank_payload_returns_clear_400(self):
        code, body = self.request("/api/bank/import", "POST", {"csv": "bad"})
        self.assertEqual(code, 400)
        self.assertEqual(body["error"], "invalid_request")

    def test_invalid_json_body_returns_400(self):
        request = urllib.request.Request(self.base + "/api/processor/events", data=b"{bad",
                                         headers={"Content-Type": "application/json"}, method="POST")
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(request, timeout=2)
        self.assertEqual(ctx.exception.code, 400)


if __name__ == "__main__":
    unittest.main()
