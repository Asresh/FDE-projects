"""Explainable incident triage using small, transparent retrieval rules."""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
TOKEN_RE = re.compile(r"[a-z0-9]+")
STOP_WORDS = {"a", "an", "and", "are", "for", "from", "in", "is", "of", "on", "or", "the", "to", "with"}


def tokens(value: str) -> set[str]:
    return {word for word in TOKEN_RE.findall(value.lower()) if word not in STOP_WORDS}


def read_csv(name: str) -> list[dict[str, str]]:
    with (DATA_DIR / name).open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def read_json(name: str) -> Any:
    with (DATA_DIR / name).open(encoding="utf-8") as file:
        return json.load(file)


@dataclass
class TriageEngine:
    incidents: list[dict[str, str]]
    services: list[dict[str, str]]
    changes: list[dict[str, str]]
    runbooks: list[dict[str, Any]]

    @classmethod
    def from_data(cls) -> "TriageEngine":
        return cls(read_csv("incidents.csv"), read_csv("services.csv"), read_csv("changes.csv"), read_json("runbooks.json"))

    def list_incidents(self) -> list[dict[str, Any]]:
        return [self._summary(incident) for incident in sorted(self.incidents, key=lambda row: row["created_at"], reverse=True)]

    def triage(self, incident_id: str) -> dict[str, Any] | None:
        incident = next((row for row in self.incidents if row["incident_id"] == incident_id), None)
        if incident is None:
            return None

        service = next((row for row in self.services if row["service_id"] == incident["service_id"]), None)
        recent_changes = [row for row in self.changes if row["service_id"] == incident["service_id"]]
        query = tokens(" ".join((incident["title"], incident["description"], incident["symptoms"])))
        ranked: list[dict[str, Any]] = []
        for runbook in self.runbooks:
            corpus = tokens(" ".join([runbook["title"], runbook["summary"], " ".join(runbook["symptoms"]), " ".join(runbook["tags"])]))
            matched = sorted(query & corpus)
            score = len(matched) / max(1, len(query))
            if score > 0:
                ranked.append({"runbook_id": runbook["runbook_id"], "title": runbook["title"], "summary": runbook["summary"], "url": runbook["url"], "score": round(score, 3), "matched_terms": matched, "source": "runbook"})
        ranked.sort(key=lambda item: (-item["score"], item["title"]))
        ranked = ranked[:3]

        priority = {"P1": 1.0, "P2": 0.75, "P3": 0.45}.get(incident["severity"], 0.25)
        urgency = {"P1": "Immediate attention", "P2": "High priority", "P3": "Normal priority"}.get(incident["severity"], "Unclassified")
        top_score = ranked[0]["score"] if ranked else 0.0
        confidence = min(0.95, round(0.25 + top_score * 0.7, 2)) if top_score else 0.15
        status = "strong_match" if confidence >= 0.65 else "verify_context"
        next_step = "Review the linked runbook and verify current system health before taking action." if confidence >= 0.65 else "Gather more context from the service owner; no runbook matched strongly enough to guide action."
        evidence = [{"evidence_id": incident["incident_id"], "kind": "alert", "label": incident["title"], "detail": incident["description"], "source": "synthetic alert feed"}]
        if service:
            evidence.append({"evidence_id": service["service_id"], "kind": "service", "label": service["name"], "detail": f"Owner: {service['owner_team']} · Tier: {service['tier']}", "source": "synthetic service catalog"})
        for change in recent_changes[:2]:
            evidence.append({"evidence_id": change["change_id"], "kind": "change", "label": change["summary"], "detail": f"Changed at {change['changed_at']}", "source": "synthetic change feed"})
        for result in ranked:
            evidence.append({"evidence_id": result["runbook_id"], "kind": "runbook", "label": result["title"], "detail": f"Matched terms: {', '.join(result['matched_terms']) or 'none'}", "source": result["url"]})

        return {
            "incident": self._summary(incident),
            "service": service,
            "urgency": urgency,
            "confidence": confidence,
            "confidence_label": "High" if confidence >= 0.75 else "Medium" if confidence >= 0.4 else "Low",
            "status": status,
            "suggested_next_step": next_step,
            "recommended_action": ranked[0]["title"] if ranked else "Contact the service owner and gather more evidence",
            "recommendations": ranked,
            "evidence": evidence,
            "recent_changes": recent_changes[:2],
            "safety_note": "Recommendations are read-only guidance. SignalDesk does not execute remediation.",
        }

    @staticmethod
    def _summary(incident: dict[str, str]) -> dict[str, Any]:
        return {key: incident[key] for key in ("incident_id", "service_id", "title", "severity", "status", "created_at", "description")}

