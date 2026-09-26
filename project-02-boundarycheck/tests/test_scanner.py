import copy
import json
import unittest
from pathlib import Path

from boundarycheck.scanner import ProfileError, scan_profile


ROOT = Path(__file__).resolve().parents[1]


def fixture(name="support-starter.json"):
    return json.loads((ROOT / "examples" / name).read_text(encoding="utf-8"))


class ScannerTests(unittest.TestCase):
    def test_safe_profile_has_no_findings(self):
        result = scan_profile(fixture())
        self.assertEqual(result["status"], "READY TO REVIEW")
        self.assertEqual(result["score"], 100)
        self.assertEqual(result["findings"], [])

    def test_non_object_root_is_rejected(self):
        with self.assertRaisesRegex(ProfileError, "top level"):
            scan_profile(["not", "an", "object"])

    def test_invalid_egress_type_is_rejected(self):
        profile = fixture()
        profile["deployment"]["network"]["egress_allowlist"] = "*"
        with self.assertRaisesRegex(ProfileError, "JSON array"):
            scan_profile(profile)

    def test_authentication_rule(self):
        profile = fixture()
        profile["deployment"]["identity"]["authentication"] = "none"
        self.assertIn("BC001", {f["code"] for f in scan_profile(profile)["findings"]})

    def test_tenant_isolation_rule(self):
        profile = fixture()
        profile["deployment"]["identity"]["tenant_isolation"] = "shared"
        self.assertIn("BC002", {f["code"] for f in scan_profile(profile)["findings"]})

    def test_prompt_logging_rule(self):
        profile = fixture()
        profile["deployment"]["logging"]["capture_prompt_text"] = True
        self.assertIn("BC003", {f["code"] for f in scan_profile(profile)["findings"]})

    def test_redaction_rule(self):
        profile = fixture()
        profile["deployment"]["logging"]["redact_sensitive_fields"] = False
        self.assertIn("BC004", {f["code"] for f in scan_profile(profile)["findings"]})

    def test_wildcard_egress_rule(self):
        profile = fixture()
        profile["deployment"]["network"]["egress_allowlist"] = ["api.example", "*"]
        self.assertIn("BC005", {f["code"] for f in scan_profile(profile)["findings"]})

    def test_write_without_approval_rule(self):
        profile = fixture()
        profile["deployment"]["tools"][1]["approval_required"] = False
        self.assertIn("BC006", {f["code"] for f in scan_profile(profile)["findings"]})

    def test_cross_tenant_scope_is_critical_and_names_path(self):
        result = scan_profile(fixture("retail-risky.json"))
        finding = next(f for f in result["findings"] if f["code"] == "BC007")
        self.assertEqual(finding["severity"], "CRITICAL")
        self.assertEqual(finding["path"], "deployment.tools[0].scope")

    def test_fail_open_is_critical(self):
        finding = next(f for f in scan_profile(fixture("retail-risky.json"))["findings"] if f["code"] == "BC008")
        self.assertEqual(finding["severity"], "CRITICAL")

    def test_secret_source_rule(self):
        profile = fixture()
        profile["deployment"]["controls"]["secret_source"] = "config_file"
        self.assertIn("BC009", {f["code"] for f in scan_profile(profile)["findings"]})

    def test_tls_and_audit_rules(self):
        profile = fixture()
        profile["deployment"]["controls"]["tls_enforced"] = False
        profile["deployment"]["controls"]["audit_events"] = False
        codes = {f["code"] for f in scan_profile(profile)["findings"]}
        self.assertTrue({"BC010", "BC011"}.issubset(codes))

    def test_evaluation_and_rollback_rules(self):
        profile = fixture()
        profile["evaluation"] = {"golden_cases": 0, "minimum_pass_rate": 0.0}
        profile["deployment"]["controls"]["rollback_documented"] = False
        codes = {f["code"] for f in scan_profile(profile)["findings"]}
        self.assertTrue({"BC012", "BC013", "BC014"}.issubset(codes))

    def test_risky_profile_is_blocked(self):
        result = scan_profile(fixture("retail-risky.json"))
        self.assertEqual(result["status"], "BLOCKED")
        self.assertLess(result["score"], 50)

    def test_findings_have_evidence_and_recommendations(self):
        result = scan_profile(fixture("retail-risky.json"))
        self.assertTrue(result["findings"])
        for finding in result["findings"]:
            self.assertTrue(finding["path"])
            self.assertTrue(finding["evidence"])
            self.assertTrue(finding["recommendation"])

    def test_result_is_deterministic_and_severity_sorted(self):
        profile = fixture("retail-risky.json")
        first = scan_profile(profile)
        second = scan_profile(copy.deepcopy(profile))
        self.assertEqual(first, second)
        severities = [f["severity"] for f in first["findings"]]
        ranks = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
        self.assertEqual(severities, sorted(severities, key=ranks.__getitem__))


if __name__ == "__main__":
    unittest.main()
