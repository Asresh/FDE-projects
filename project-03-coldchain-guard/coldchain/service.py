"""Validation, temperature policy, case creation, and ticket delivery."""

import json
import urllib.error
import urllib.request
from datetime import datetime
from uuid import uuid5, NAMESPACE_URL


class InputError(ValueError):
    pass


def validate_event(event):
    required = ("event_id", "sensor_id", "location_id", "observed_at", "temperature_c")
    if not isinstance(event, dict):
        raise InputError("request body must be a JSON object")
    missing = [key for key in required if key not in event]
    if missing:
        raise InputError("missing required fields: " + ", ".join(missing))
    for key in required[:3]:
        if not isinstance(event[key], str) or not event[key].strip() or len(event[key]) > 128:
            raise InputError(f"{key} must be a non-empty string of at most 128 characters")
    try:
        observed = datetime.fromisoformat(event["observed_at"].replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise InputError("observed_at must be an ISO-8601 timestamp") from exc
    if observed.tzinfo is None:
        raise InputError("observed_at must include a timezone")
    value = event["temperature_c"]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InputError("temperature_c must be a finite number")
    if value != value or value in (float("inf"), float("-inf")) or not -100 <= value <= 100:
        raise InputError("temperature_c must be a finite number between -100 and 100")
    return {**event, "observed_at": observed.isoformat(), "temperature_c": float(value)}


class WebhookNotifier:
    def __init__(self, url=None, timeout=2):
        self.url = url
        self.timeout = timeout

    def deliver(self, payload):
        if not self.url:
            return "mock"
        req = urllib.request.Request(self.url, data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json",
                                              "Idempotency-Key": payload["idempotency_key"]},
                                     method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                if response.status >= 300:
                    raise RuntimeError(f"webhook returned HTTP {response.status}")
        except (urllib.error.URLError, TimeoutError) as exc:
            raise RuntimeError(f"webhook delivery failed: {exc}") from exc
        return "delivered"


class ColdChainService:
    def __init__(self, repository, notifier=None):
        self.repository = repository
        self.notifier = notifier or WebhookNotifier()

    def ingest(self, raw_event):
        event = validate_event(raw_event)
        reading_id, inserted = self.repository.save_reading(event)
        reading, existing_case = self.repository.reading_result(reading_id)
        if not inserted:
            return {"duplicate": True, "reading_id": reading_id,
                    "case": self._case_view(existing_case), "notification": "unchanged"}

        lots = self.repository.lots_at(event["location_id"])
        out_of_range = [lot for lot in lots
                        if not lot["min_c"] <= event["temperature_c"] <= lot["max_c"]]
        if not lots:
            severity = "high"
            summary = f"No inventory mapping exists for {event['location_id']}; quality review required."
            affected = []
        elif out_of_range:
            severity = "critical" if any(
                event["temperature_c"] > lot["max_c"] + 3 or
                event["temperature_c"] < lot["min_c"] - 3 for lot in out_of_range) else "high"
            affected = [lot["lot_id"] for lot in out_of_range]
            summary = (f"{event['temperature_c']:.1f}°C outside the allowed range for "
                       f"{len(affected)} lot(s) at {event['location_id']}; quality review required.")
        else:
            return {"duplicate": False, "reading_id": reading_id, "case": None,
                    "notification": "not_required"}

        case_id = str(uuid5(NAMESPACE_URL, f"coldchain:{event['sensor_id']}:{event['event_id']}"))
        case = self.repository.create_case(case_id, reading_id, severity, summary,
                                           affected, event["observed_at"])
        payload = {"case_id": case["id"], "severity": case["severity"],
                   "summary": case["summary"], "lot_ids": affected,
                   "idempotency_key": case["id"]}
        try:
            state = self.notifier.deliver(payload)
            self.repository.mark_delivery(case["id"], state)
        except Exception as exc:  # preserve the case and outbox when downstream is unavailable
            self.repository.mark_delivery(case["id"], "pending", str(exc)[:500])
            state = "pending"
        return {"duplicate": False, "reading_id": reading_id,
                "case": self._case_view(case), "notification": state}

    @staticmethod
    def _case_view(case):
        if not case:
            return None
        return {**case, "lot_ids": json.loads(case["lot_ids"])}
