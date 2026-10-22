import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from coldchain.api import create_server


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
        data = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method,
                                     headers={"Content-Type": "application/json"})
        try:
            response = urllib.request.urlopen(req, timeout=2)
        except urllib.error.HTTPError as exc:
            response = exc
        return response.code, json.loads(response.read())

    def test_health_and_unknown_route(self):
        self.assertEqual(self.request("/health")[0], 200)
        code, body = self.request("/not-a-route")
        self.assertEqual(code, 404)
        self.assertEqual(body["error"], "not_found")

    def test_demo_loads_and_persists_case_and_notification(self):
        code, body = self.request("/api/demo", "POST", {})
        self.assertEqual(code, 200)
        self.assertEqual(body["imported_lots"], 3)
        self.assertEqual(len(body["results"]), 2)
        _, cases = self.request("/api/cases")
        _, outbox = self.request("/api/outbox")
        self.assertEqual(len(cases["cases"]), 1)
        self.assertEqual(outbox["notifications"][0]["delivery_state"], "mock")

    def test_invalid_json_and_bad_event_have_clear_400(self):
        req = urllib.request.Request(self.base + "/api/telemetry", data=b"{bad",
                                     headers={"Content-Type": "application/json"}, method="POST")
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req, timeout=2)
        self.assertEqual(ctx.exception.code, 400)
        code, body = self.request("/api/telemetry", "POST", {"event_id": "incomplete"})
        self.assertEqual(code, 400)
        self.assertEqual(body["error"], "invalid_request")


if __name__ == "__main__":
    unittest.main()
