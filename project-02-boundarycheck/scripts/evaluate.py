"""Run a repeatable synthetic policy-coverage check."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from boundarycheck.scanner import scan_profile  # noqa: E402


def safe_profile():
    return json.loads((ROOT / "examples" / "support-starter.json").read_text(encoding="utf-8"))


def mutate(profile, path, value):
    target = profile
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value


def cases():
    definitions = [
        ("safe baseline", [], []),
        ("missing auth", [(('deployment', 'identity', 'authentication'), 'none')], ["BC001"]),
        ("shared tenant", [(('deployment', 'identity', 'tenant_isolation'), 'shared')], ["BC002"]),
        ("prompt logging and no redaction", [
            (('deployment', 'logging', 'capture_prompt_text'), True),
            (('deployment', 'logging', 'redact_sensitive_fields'), False)], ["BC003", "BC004"]),
        ("wildcard egress", [(('deployment', 'network', 'egress_allowlist'), ["*"])], ["BC005"]),
        ("unapproved write", [(('deployment', 'tools', 1, 'approval_required'), False)], ["BC006"]),
        ("cross-tenant tool", [(('deployment', 'tools', 0, 'scope'), "all_tenants")], ["BC007"]),
        ("fail open", [(('deployment', 'controls', 'fail_closed'), False)], ["BC008"]),
        ("unmanaged secret", [(('deployment', 'controls', 'secret_source'), "config_file")], ["BC009"]),
        ("transport and audit", [
            (('deployment', 'controls', 'tls_enforced'), False),
            (('deployment', 'controls', 'audit_events'), False)], ["BC010", "BC011"]),
        ("evaluation and rollback", [
            (('evaluation', 'golden_cases'), 0),
            (('evaluation', 'minimum_pass_rate'), 0.0),
            (('deployment', 'controls', 'rollback_documented'), False)], ["BC012", "BC013", "BC014"]),
        ("combined critical and high settings", [
            (('deployment', 'identity', 'authentication'), "none"),
            (('deployment', 'identity', 'tenant_isolation'), "shared"),
            (('deployment', 'logging', 'capture_prompt_text'), True),
            (('deployment', 'logging', 'redact_sensitive_fields'), False),
            (('deployment', 'network', 'egress_allowlist'), ["*"]),
            (('deployment', 'tools', 0, 'scope'), "all_tenants"),
            (('deployment', 'tools', 1, 'approval_required'), False),
            (('deployment', 'controls', 'fail_closed'), False),
            (('deployment', 'controls', 'secret_source'), "config_file"),
            (('deployment', 'controls', 'tls_enforced'), False),
            (('deployment', 'controls', 'audit_events'), False),
            (('evaluation', 'golden_cases'), 0),
            (('evaluation', 'minimum_pass_rate'), 0.0),
            (('deployment', 'controls', 'rollback_documented'), False)],
            [f"BC{i:03}" for i in range(1, 15)]),
    ]
    for name, changes, expected in definitions:
        profile = copy.deepcopy(safe_profile())
        for path, value in changes:
            mutate(profile, path, value)
        yield name, profile, set(expected)


def main():
    total_expected = 0
    total_detected = 0
    failures = []
    for name, profile, expected in cases():
        actual = {finding["code"] for finding in scan_profile(profile)["findings"]}
        missing = expected - actual
        unexpected = actual - expected
        total_expected += len(expected)
        total_detected += len(expected & actual)
        print(f"{'PASS' if not missing and not unexpected else 'FAIL'}  {name}: expected={len(expected)} detected={len(expected & actual)}")
        if missing or unexpected:
            failures.append((name, sorted(missing), sorted(unexpected)))
    print(f"\nProfiles: 12 · seeded rule instances: {total_expected} · detected: {total_detected}")
    if failures:
        for name, missing, unexpected in failures:
            print(f"{name}: missing={missing}, unexpected={unexpected}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
