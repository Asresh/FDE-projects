"""Small standard-library HTTP API with JSON logs and health endpoint."""

import json
import logging
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .repository import Repository
from .service import ColdChainService, InputError, WebhookNotifier

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "fixtures"


class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({"timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
                           "level": record.levelname, "event": record.getMessage()})


def make_handler(service, repository):
    class Handler(BaseHTTPRequestHandler):
        server_version = "ColdChainGuard/1.0"

        def log_message(self, fmt, *args):
            logging.getLogger("coldchain.http").info(
                json.dumps({"client": self.client_address[0], "message": fmt % args}))

        def send_json(self, code, payload):
            data = json.dumps(payload, sort_keys=True).encode()
            self.send_response(code)
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
                    repository.health()
                    self.send_json(200, {"status": "ok", "database": "ok"})
                except Exception:
                    self.send_json(503, {"status": "degraded", "database": "unavailable"})
            elif path == "/api/cases":
                self.send_json(200, {"cases": service.repository.cases()})
            elif path == "/api/outbox":
                self.send_json(200, {"notifications": service.repository.outbox()})
            else:
                self.send_json(404, {"error": "not_found", "message": "route not found"})

        def do_POST(self):
            path = urlparse(self.path).path
            try:
                if path == "/api/telemetry":
                    result = service.ingest(self.read_json())
                    self.send_json(200 if result["duplicate"] else 201, result)
                elif path == "/api/demo":
                    with (FIXTURES / "inventory.json").open(encoding="utf-8") as file:
                        inventory = json.load(file)
                    repository.import_inventory(inventory)
                    with (FIXTURES / "readings.json").open(encoding="utf-8") as file:
                        events = json.load(file)
                    results = [service.ingest(event) for event in events]
                    self.send_json(200, {"imported_lots": len(inventory), "results": results})
                else:
                    self.send_json(404, {"error": "not_found", "message": "route not found"})
            except InputError as exc:
                self.send_json(400, {"error": "invalid_request", "message": str(exc)})
            except Exception as exc:
                logging.getLogger("coldchain.api").exception("request_failed")
                self.send_json(500, {"error": "internal_error", "message": "request could not be completed"})

        def do_OPTIONS(self):
            self.send_json(405, {"error": "method_not_allowed"})

    return Handler


def create_server(host="127.0.0.1", port=8080, database_path="./data/coldchain.sqlite",
                  webhook_url=None):
    repository = Repository(database_path)
    service = ColdChainService(repository, WebhookNotifier(webhook_url))
    return ThreadingHTTPServer((host, port), make_handler(service, repository))


def serve():
    logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler()])
    logging.getLogger().handlers[0].setFormatter(JsonFormatter())
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8080"))
    database_path = os.environ.get("DATABASE_PATH", "./data/coldchain.sqlite")
    webhook_url = os.environ.get("TICKETING_WEBHOOK_URL") or None
    server = create_server(host, port, database_path, webhook_url)
    logging.getLogger("coldchain").info(json.dumps({"event": "server_started", "host": host, "port": port}))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
