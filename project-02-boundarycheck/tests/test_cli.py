import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, "-m", "boundarycheck", *args], cwd=ROOT,
                              text=True, capture_output=True, check=False)

    def test_html_report_is_written_and_severity_threshold_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.html"
            result = self.run_cli("scan", "examples/retail-risky.json", "--format", "html",
                                  "--output", str(output), "--fail-on", "high")
            self.assertEqual(result.returncode, 1)
            self.assertIn("Report written", result.stdout)
            self.assertIn("BoundaryCheck", output.read_text(encoding="utf-8"))

    def test_html_escapes_profile_text(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "unsafe.json"
            profile = json.loads((ROOT / "examples" / "support-starter.json").read_text(encoding="utf-8"))
            profile["customer"]["name"] = "<script>alert(1)</script>"
            profile["deployment"]["controls"]["audit_events"] = False
            source.write_text(json.dumps(profile), encoding="utf-8")
            result = self.run_cli("scan", str(source), "--format", "html")
            self.assertEqual(result.returncode, 0)
            self.assertNotIn("<script>alert(1)</script>", result.stdout)
            self.assertIn("&lt;script&gt;", result.stdout)

    def test_malformed_json_returns_two(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "broken.json"
            source.write_text("{broken", encoding="utf-8")
            result = self.run_cli("scan", str(source))
            self.assertEqual(result.returncode, 2)
            self.assertIn("Invalid JSON", result.stderr)

    def test_missing_profile_returns_two(self):
        result = self.run_cli("scan", "missing-profile.json")
        self.assertEqual(result.returncode, 2)
        self.assertIn("Profile not found", result.stderr)


if __name__ == "__main__":
    unittest.main()
