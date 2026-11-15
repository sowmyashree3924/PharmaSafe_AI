import unittest
from unittest.mock import patch

from backend.agents.clinical_agent import clinical_assessment_agent


class TestClinicalAgent(unittest.TestCase):

    def test_incomplete_case_escalates_without_gemini(self):
        state = {
            "case_id": "TEST-001",
            "case_data": {
                "patient_age": 45,
                "drug_name": None,
                "reaction_description": "Severe skin peeling",
                "event_onset_date": "2026-11-10",
                "drug_start_date": "2026-11-03",
                "outcome": "hospitalized",
                "hospitalized": True,
            },
        }

        # Gemini must never be invoked for an incomplete case.
        with patch(
            "backend.agents.clinical_agent.get_clinical_model",
            side_effect=AssertionError("Gemini should not be called"),
        ):
            result = clinical_assessment_agent(state)

        self.assertTrue(result["escalation_required"])
        self.assertEqual(result["reporting_route"], "human_review")
        self.assertEqual(result["current_agent"], "human_escalation")
        self.assertIn("drug_name", result["missing_fields"])

        print("PASS: Incomplete case escalated.")
        print("PASS: Gemini was not invoked.")
        print("PASS: Human review routing confirmed.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
