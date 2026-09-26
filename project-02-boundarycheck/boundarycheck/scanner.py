"""Deterministic rules for a small, customer-provided deployment profile."""

from dataclasses import asdict, dataclass
from typing import Any


SEVERITY_ORDER = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFO": 0}
SEVERITY_PENALTY = {"CRITICAL": 25, "HIGH": 15, "MEDIUM": 8, "LOW": 3, "INFO": 0}


class ProfileError(ValueError):
    """Raised when a profile cannot be scanned safely."""


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    title: str
    path: str
    evidence: str
    explanation: str
    recommendation: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def _at(profile: dict[str, Any], *keys: str, default: Any = None) -> Any:
    current: Any = profile
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def _finding(code: str, severity: str, title: str, path: str, evidence: Any,
             explanation: str, recommendation: str) -> Finding:
    return Finding(code, severity, title, path, repr(evidence), explanation, recommendation)


def scan_profile(profile: dict[str, Any]) -> dict[str, Any]:
    """Return stable findings and an advisory score for a deployment profile."""
    if not isinstance(profile, dict):
        raise ProfileError("The profile's top level must be a JSON object.")

    findings: list[Finding] = []
    auth = _at(profile, "deployment", "identity", "authentication")
    if str(auth or "").lower() not in {"oidc", "saml", "mtls"}:
        findings.append(_finding(
            "BC001", "HIGH", "Enterprise authentication is not specified",
            "deployment.identity.authentication", auth,
            "The profile does not identify a supported sign-in boundary.",
            "Choose the customer's approved OIDC, SAML, or mutual-TLS pattern and verify its configuration.",
        ))

    isolation = _at(profile, "deployment", "identity", "tenant_isolation")
    if isolation != "per_customer":
        findings.append(_finding(
            "BC002", "HIGH", "Customer data isolation is unclear",
            "deployment.identity.tenant_isolation", isolation,
            "A shared or unspecified boundary can expose one customer's records to another.",
            "Enforce and test a per-customer data boundary at the identity, query, and storage layers.",
        ))

    if _at(profile, "deployment", "logging", "capture_prompt_text", default=False) is True:
        findings.append(_finding(
            "BC003", "HIGH", "Prompt text is retained in logs",
            "deployment.logging.capture_prompt_text", True,
            "Prompts can contain personal, confidential, or customer-provided information.",
            "Disable prompt-body logging by default; record metadata or an approved, time-limited sample instead.",
        ))

    if _at(profile, "deployment", "logging", "redact_sensitive_fields", default=False) is not True:
        findings.append(_finding(
            "BC004", "MEDIUM", "Sensitive fields are not marked for redaction",
            "deployment.logging.redact_sensitive_fields",
            _at(profile, "deployment", "logging", "redact_sensitive_fields"),
            "Support and telemetry logs can accidentally become a second store of sensitive data.",
            "Redact customer identifiers and sensitive fields before data reaches logs or traces.",
        ))

    egress = _at(profile, "deployment", "network", "egress_allowlist", default=[])
    if not isinstance(egress, list):
        raise ProfileError("deployment.network.egress_allowlist must be a JSON array.")
    if any(str(host).strip().lower() in {"*", "all", "0.0.0.0/0", "::/0"} for host in egress):
        findings.append(_finding(
            "BC005", "HIGH", "Outbound network access is unrestricted",
            "deployment.network.egress_allowlist", egress,
            "A wildcard destination lets a compromised component contact arbitrary hosts.",
            "Replace wildcards with the minimum named services the deployment needs; log and review denied egress.",
        ))

    tools = _at(profile, "deployment", "tools", default=[])
    if not isinstance(tools, list) or any(not isinstance(item, dict) for item in tools):
        raise ProfileError("deployment.tools must be an array of JSON objects.")
    for index, item in enumerate(tools):
        base = f"deployment.tools[{index}]"
        name = item.get("name", f"tool-{index}")
        if str(item.get("scope", "")).lower() in {"all_tenants", "global", "*"}:
            findings.append(_finding(
                "BC007", "CRITICAL", "A tool can act across customer boundaries",
                f"{base}.scope", item.get("scope"),
                f"Tool '{name}' is configured to reach more than the requesting customer's data.",
                "Restrict the tool to the authenticated customer's records and add cross-tenant denial tests.",
            ))
        if str(item.get("access", "")).lower() in {"write", "delete", "admin"} and item.get("approval_required") is not True:
            findings.append(_finding(
                "BC006", "HIGH", "A write-capable tool has no approval gate",
                f"{base}.approval_required", item.get("approval_required"),
                f"Tool '{name}' can change customer data without an explicit human decision.",
                "Require approval before consequential writes; make the approved action and actor auditable.",
            ))

    if _at(profile, "deployment", "controls", "fail_closed", default=False) is not True:
        findings.append(_finding(
            "BC008", "CRITICAL", "A control may fail open",
            "deployment.controls.fail_closed", _at(profile, "deployment", "controls", "fail_closed"),
            "If identity, policy, or a dependency check fails, the system could continue without its guardrail.",
            "Fail closed for authorization and policy checks; define a safe fallback for unavailable dependencies.",
        ))

    secret_source = str(_at(profile, "deployment", "controls", "secret_source", default="")).lower()
    if secret_source not in {"secret_manager", "environment_reference", "workload_identity"}:
        findings.append(_finding(
            "BC009", "HIGH", "Secret handling is not tied to a managed source",
            "deployment.controls.secret_source", secret_source or None,
            "A profile without an explicit managed source can lead to credentials being copied into config or images.",
            "Use a customer-approved secret manager, workload identity, or environment reference; never commit secret values.",
        ))

    if _at(profile, "deployment", "controls", "tls_enforced", default=False) is not True:
        findings.append(_finding(
            "BC010", "HIGH", "Transport encryption is not confirmed",
            "deployment.controls.tls_enforced", _at(profile, "deployment", "controls", "tls_enforced"),
            "Without an explicit transport-encryption setting, service-to-service traffic may be exposed.",
            "Require TLS for customer and internal service traffic and verify certificate validation is enabled.",
        ))

    if _at(profile, "deployment", "controls", "audit_events", default=False) is not True:
        findings.append(_finding(
            "BC011", "MEDIUM", "Security-relevant actions are not audited",
            "deployment.controls.audit_events", _at(profile, "deployment", "controls", "audit_events"),
            "The team may not be able to reconstruct who invoked a tool or changed a policy.",
            "Record actor, action, timestamp, target, and outcome without storing prompt or secret contents.",
        ))

    eval_cases = _at(profile, "evaluation", "golden_cases", default=0)
    if not isinstance(eval_cases, int) or eval_cases < 1:
        findings.append(_finding(
            "BC012", "MEDIUM", "No repeatable evaluation cases are declared",
            "evaluation.golden_cases", eval_cases,
            "There is no stated regression set to check customer-specific behavior before rollout.",
            "Add representative success, refusal, boundary, and failure cases from the agreed workflow.",
        ))

    threshold = _at(profile, "evaluation", "minimum_pass_rate")
    if not isinstance(threshold, (int, float)) or not 0.0 < threshold <= 1.0:
        findings.append(_finding(
            "BC013", "MEDIUM", "An acceptance threshold is missing or invalid",
            "evaluation.minimum_pass_rate", threshold,
            "Without a pass bar, the team cannot make a consistent launch decision from evaluation results.",
            "Set a customer-approved pass rate between 0 and 1 and define which failures block release.",
        ))

    if _at(profile, "deployment", "controls", "rollback_documented", default=False) is not True:
        findings.append(_finding(
            "BC014", "MEDIUM", "A rollback path is not confirmed",
            "deployment.controls.rollback_documented",
            _at(profile, "deployment", "controls", "rollback_documented"),
            "A team needs a known way to pause or revert a deployment if quality or safety falls.",
            "Document who can pause rollout, how to restore the last known-good version, and how users are informed.",
        ))

    findings.sort(key=lambda finding: (-SEVERITY_ORDER[finding.severity], finding.code, finding.path))
    score = max(0, 100 - sum(SEVERITY_PENALTY[item.severity] for item in findings))
    highest = max((SEVERITY_ORDER[item.severity] for item in findings), default=0)
    status = "BLOCKED" if highest >= 3 else "REVIEW" if findings else "READY TO REVIEW"
    return {
        "schema_version": "1.0",
        "customer": _at(profile, "customer", "name", default="Unnamed deployment"),
        "environment": _at(profile, "customer", "environment", default="unspecified"),
        "service": _at(profile, "customer", "service", default="AI service"),
        "status": status,
        "score": score,
        "finding_count": len(findings),
        "findings": [item.to_dict() for item in findings],
        "disclaimer": "Advisory profile review only. This result is not a live-system scan, audit, or security certification.",
    }
