from backend.agents.graph import (
    route_after_clinical_assessment,
    route_after_tool_execution,
    route_after_verification,
)


def test_clinical_agent_requests_tools():

    state = {
        "messages": [
            type(
                "FakeMessage",
                (),
                {"tool_calls": [{"name": "corpus_search_tool"}]},
            )()
        ]
    }

    assert route_after_clinical_assessment(state) == "tools"

    print("PASS: Clinical agent can request retrieval tools.")


def test_clinical_agent_hands_off_to_verification():

    state = {
        "messages": [
            type(
                "FakeMessage",
                (),
                {"tool_calls": []},
            )()
        ],
        "clinical_assessment": {
            "seriousness": "serious",
            "expectedness": "undetermined",
        },
        "clinical_evidence": [],
    }

    assert (
        route_after_clinical_assessment(state)
        == "assessment_complete"
    )

    print("PASS: Clinical agent hands off to verification.")


def test_failed_verification_escalates():

    state = {
        "escalation_required": True,
    }

    assert route_after_verification(state) == "escalation"

    print("PASS: Failed verification triggers escalation.")


def test_successful_verification_finishes():

    state = {
        "escalation_required": False,
    }

    from langgraph.graph import END

    assert route_after_verification(state) == END

    print("PASS: Successful verification completes workflow.")


if __name__ == "__main__":

    test_clinical_agent_requests_tools()
    test_clinical_agent_hands_off_to_verification()
    test_failed_verification_escalates()
    test_successful_verification_finishes()

    print("\nAll agent handoff tests passed!")
