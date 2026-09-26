import unittest

from signaldesk.engine import TriageEngine


class TriageEngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = TriageEngine.from_data()

    def test_known_p1_gets_owner_recent_change_and_relevant_runbook(self):
        result = self.engine.triage("INC-1042")
        self.assertEqual(result["service"]["owner_team"], "Commerce Platform")
        self.assertEqual(result["recommendations"][0]["runbook_id"], "RB-017")
        self.assertEqual(result["recent_changes"][0]["change_id"], "CHG-882")

    def test_runbook_recommendation_has_explainable_matched_terms(self):
        result = self.engine.triage("INC-1041")
        self.assertEqual(result["recommendations"][0]["runbook_id"], "RB-023")
        self.assertIn("indexing", result["recommendations"][0]["matched_terms"])

    def test_golden_scenarios_rank_expected_runbook_first(self):
        expected = {"INC-1042": "RB-017", "INC-1041": "RB-023", "INC-1040": "RB-031"}
        for incident_id, runbook_id in expected.items():
            with self.subTest(incident_id=incident_id):
                self.assertEqual(self.engine.triage(incident_id)["recommendations"][0]["runbook_id"], runbook_id)

    def test_unknown_incident_returns_none(self):
        self.assertIsNone(self.engine.triage("INC-9999"))

    def test_summary_does_not_leak_internal_symptom_search_field(self):
        summary = self.engine.list_incidents()[0]
        self.assertNotIn("symptoms", summary)

    def test_every_brief_is_explicitly_read_only(self):
        for incident in self.engine.incidents:
            brief = self.engine.triage(incident["incident_id"])
            self.assertIn("does not execute remediation", brief["safety_note"])
            self.assertIn("source", brief["evidence"][0])


if __name__ == "__main__":
    unittest.main()
