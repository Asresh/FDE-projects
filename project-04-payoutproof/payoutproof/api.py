"""HTTP entry point for processor event, bank statement, and reconciliation APIs."""

import json
import logging
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .ingestion import InputError, parse_bank_csv, validate_processor_event
from .ledger import Ledger
from .reconcile import Reconciler, WebhookNotifier

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "fixtures"


class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({"timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
                           "level": record.levelname, "event": record.getMessage()})


def make_handler(ledger, reconciler):
    class Handler(BaseHTTPRequestHandler):
        server_version = "PayoutProof/1.0"

        def log_message(self, fmt, *args):
            logging.getLogger("payoutproof.http").info(
                json.dumps({"client": self.client_address[0], "message": fmt % args}))

        def send_json(self, status, body):
            data = json.dumps(body, sort_keys=True).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def read_json(self):
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError as exc:
                raise InputError("invalid Content-Length") from exc
            if length <= 0 or length > 65536:
                raise InputError("request body must be between 1 and 65536 bytes")
            try:
                return json.loads(self.rfile.read(length))
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                raise InputError("request body must contain valid JSON") from exc

        def do_GET(self):
            path = urlparse(self.path).path
            if path == "/health":
                try:
                    ledger.health()
                    self.send_json(200, {"status": "ok", "database": "ok"})
                except Exception:
                    self.send_json(503, {"status": "degraded", "database": "unavailable"})
            elif path == "/api/reconciliations":
                self.send_json(200, {"reconciliations": ledger.reconciliations()})
            elif path == "/api/outbox":
                self.send_json(200, {"alerts": ledger.alerts()})
            else:
                self.send_json(404, {"error": "not_found", "message": "route not found"})

        def do_POST(self):
            path = urlparse(self.path).path
            try:
                if path == "/api/processor/events":
                    event = validate_processor_event(self.read_json())
                    inserted = ledger.save_processor_event(event)
                    self.send_json(201 if inserted else 200,
                                   {"accepted": inserted, "duplicate": not inserted,
                                    "payout_id": event["payout_id"]})
                elif path == "/api/bank/import":
                    body = self.read_json()
                    rows = parse_bank_csv(body.get("csv") if isinstance(body, dict) else None)
                    result = ledger.import_bank_rows(rows)
                    self.send_json(200, result)
                elif path == "/api/reconcile":
                    results = reconciler.run()
                    self.send_json(200, {"count": len(results), "reconciliations": results})
                elif path == "/api/demo":
                    with (FIXTURES / "processor_events.json").open(encoding="utf-8") as file:
                        events = json.load(file)
                    accepted = sum(ledger.save_processor_event(validate_processor_event(item))
                                   for item in events)
                    with (FIXTURES / "bank_statement.csv").open(encoding="utf-8") as file:
                        bank_rows = parse_bank_csv(file.read())
                    bank_result = ledger.import_bank_rows(bank_rows)
                    results = reconciler.run()
                    self.send_json(200, {"processor_events_added": accepted,
                                         "bank_import": bank_result, "count": len(results),
                                         "reconciliations": results})
                else:
                    self.send_json(404, {"error": "not_found", "message": "route not found"})
            except (InputError, ValueError) as exc:
                self.send_json(400, {"error": "invalid_request", "message": str(exc)})
            except Exception:
                logging.getLogger("payoutproof.api").exception("request_failed")
                self.send_json(500, {"error": "internal_error",
                                     "message": "request could not be completed"})

    return Handler


def create_server(host="127.0.0.1", port=8090, database_path="./data/payoutproof.sqlite",
                  webhook_url=None):
    ledger = Ledger(database_path)
    reconciler = Reconciler(ledger, WebhookNotifier(webhook_url))
    return ThreadingHTTPServer((host, port), make_handler(ledger, reconciler))


def serve():
    logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler()])
    logging.getLogger().handlers[0].setFormatter(JsonFormatter())
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8090"))
    database_path = os.environ.get("DATABASE_PATH", "./data/payoutproof.sqlite")
    webhook_url = os.environ.get("FINANCE_ALERT_WEBHOOK_URL") or None
    server = create_server(host, port, database_path, webhook_url)
    logging.getLogger("payoutproof").info(json.dumps(
        {"event": "server_started", "host": host, "port": port}))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
