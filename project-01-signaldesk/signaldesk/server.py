"""Tiny WSGI server and JSON API; no third-party packages required."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from http import HTTPStatus
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qs

from .engine import TriageEngine


ROOT = Path(__file__).resolve().parent.parent
HTML = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
DECISIONS: list[dict[str, Any]] = []


def _response(start_response: Callable, status: HTTPStatus, body: bytes, content_type: str) -> list[bytes]:
    start_response(f"{status.value} {status.phrase}", [("Content-Type", content_type), ("Content-Length", str(len(body))), ("Cache-Control", "no-store"), ("X-Content-Type-Options", "nosniff")])
    return [body]


def _json(start_response: Callable, status: HTTPStatus, payload: Any) -> list[bytes]:
    return _response(start_response, status, json.dumps(payload, ensure_ascii=False).encode(), "application/json; charset=utf-8")


def create_app(engine: TriageEngine | None = None) -> Callable:
    engine = engine or TriageEngine.from_data()

    def app(environ: dict[str, Any], start_response: Callable) -> list[bytes]:
        method, path = environ.get("REQUEST_METHOD", "GET"), environ.get("PATH_INFO", "/")
        if method == "GET" and path == "/":
            return _response(start_response, HTTPStatus.OK, HTML.encode(), "text/html; charset=utf-8")
        if method == "GET" and path == "/health":
            return _json(start_response, HTTPStatus.OK, {"status": "ok", "service": "signaldesk", "version": "1.0.0"})
        if method == "GET" and path == "/api/incidents":
            return _json(start_response, HTTPStatus.OK, {"incidents": engine.list_incidents()})
        if method == "GET" and path.startswith("/api/incidents/"):
            incident_id = path.rsplit("/", 1)[-1]
            triage = engine.triage(incident_id)
            if triage is None:
                return _json(start_response, HTTPStatus.NOT_FOUND, {"error": "incident_not_found", "message": f"No incident with id {incident_id}."})
            return _json(start_response, HTTPStatus.OK, triage)
        if method == "POST" and path.startswith("/api/incidents/") and path.endswith("/review"):
            incident_id = path.split("/")[-2]
            try:
                length = min(int(environ.get("CONTENT_LENGTH") or 0), 16_384)
                data = json.loads(environ["wsgi.input"].read(length) or b"{}")
            except (ValueError, json.JSONDecodeError):
                return _json(start_response, HTTPStatus.BAD_REQUEST, {"error": "invalid_json"})
            decision, note = data.get("decision"), data.get("note", "")
            if decision not in {"approved", "dismissed", "needs_more_info"}:
                return _json(start_response, HTTPStatus.BAD_REQUEST, {"error": "invalid_decision", "allowed": ["approved", "dismissed", "needs_more_info"]})
            if engine.triage(incident_id) is None:
                return _json(start_response, HTTPStatus.NOT_FOUND, {"error": "incident_not_found"})
            record = {"incident_id": incident_id, "decision": decision, "note": str(note)[:500], "recorded_at": datetime.now(timezone.utc).isoformat()}
            DECISIONS.append(record)
            return _json(start_response, HTTPStatus.CREATED, {"review": record, "message": "Decision recorded for this demo session."})
        if method == "GET" and path == "/api/reviews":
            return _json(start_response, HTTPStatus.OK, {"reviews": DECISIONS})
        return _json(start_response, HTTPStatus.NOT_FOUND, {"error": "not_found"})

    return app


def serve(host: str = "127.0.0.1", port: int = 8000) -> None:
    from wsgiref.simple_server import make_server

    app = create_app()
    print(f"SignalDesk is ready at http://{host}:{port} · Press Ctrl+C to stop")
    with make_server(host, port, app) as server:
        server.serve_forever()

