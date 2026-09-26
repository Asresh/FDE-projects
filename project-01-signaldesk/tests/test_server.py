import io
import json
import unittest

from signaldesk.server import DECISIONS, create_app


def request(app, method, path, body=None):
    raw = json.dumps(body).encode() if body is not None else b""
    env = {"REQUEST_METHOD": method, "PATH_INFO": path, "CONTENT_LENGTH": str(len(raw)), "wsgi.input": io.BytesIO(raw)}
    seen = {}
    payload = b"".join(app(env, lambda status, headers: seen.update(status=status, headers=dict(headers))))
    return int(seen["status"].split()[0]), seen["headers"], json.loads(payload) if "json" in seen["headers"].get("Content-Type", "") else payload.decode()


class ApiTests(unittest.TestCase):
    def setUp(self):
        DECISIONS.clear()
        self.app = create_app()

    def test_health_returns_ok(self):
        status, _, body = request(self.app, "GET", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "ok")

    def test_list_incidents_is_json(self):
        status, headers, body = request(self.app, "GET", "/api/incidents")
        self.assertEqual(status, 200)
        self.assertTrue(headers["Content-Type"].startswith("application/json"))
        self.assertEqual(len(body["incidents"]), 3)

    def test_incident_detail_includes_source_linked_evidence(self):
        status, _, body = request(self.app, "GET", "/api/incidents/INC-1042")
        self.assertEqual(status, 200)
        self.assertTrue(all(item.get("source") for item in body["evidence"]))

    def test_unknown_incident_is_404(self):
        status, _, body = request(self.app, "GET", "/api/incidents/INC-9999")
        self.assertEqual(status, 404)
        self.assertEqual(body["error"], "incident_not_found")

    def test_review_accepts_allowed_decision_and_records_it(self):
        status, _, body = request(self.app, "POST", "/api/incidents/INC-1042/review", {"decision": "approved", "note": "Checked dashboard"})
        self.assertEqual(status, 201)
        self.assertEqual(body["review"]["note"], "Checked dashboard")
        self.assertEqual(DECISIONS[0]["decision"], "approved")

    def test_review_rejects_unknown_decision(self):
        status, _, body = request(self.app, "POST", "/api/incidents/INC-1042/review", {"decision": "execute_fix"})
        self.assertEqual(status, 400)
        self.assertEqual(body["error"], "invalid_decision")

    def test_review_is_not_available_for_unknown_incident(self):
        status, _, body = request(self.app, "POST", "/api/incidents/INC-9999/review", {"decision": "approved"})
        self.assertEqual(status, 404)
        self.assertEqual(body["error"], "incident_not_found")


if __name__ == "__main__":
    unittest.main()
