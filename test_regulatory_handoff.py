from langgraph.graph import END

from backend.agents.graph import (
    pharmacovigilance_workflow,
    route_after_verification,
    route_after_regulatory_routing,
)


def test_graph_compiles():
    assert pharmacovigilance_workflow is not None
    print("PASS: LangGraph compiles with regulatory routing node.")


def test_verified_case_reaches_regulatory_router():
    state = {
        "escalation_required": False,
        "verification_result": {"passed": True},
    }

    assert route_after_verification(state) == "regulatory_routing"

    print("PASS: Verified assessment reaches regulatory routing.")


def test_failed_verification_skips_regulatory_router():
    state = {
        "escalation_required": True,
        "verification_result": {"passed": False},
    }

    assert route_after_verification(state) == "escalation"

    print("PASS: Failed verification goes directly to escalation.")


def test_valid_regulatory_route_completes():
    state = {
        "escalation_required": False,
        "reporting_route": "expedited",
    }

    assert route_after_regulatory_routing(state) == END

    print("PASS: Established reporting route completes workflow.")


def test_missing_regulatory_route_escalates():
    state = {
        "escalation_required": False,
        "reporting_route": "",
    }

    assert route_after_regulatory_routing(state) == "escalation"

    print("PASS: Missing reporting route triggers escalation.")


if __name__ == "__main__":
    test_graph_compiles()
    test_verified_case_reaches_regulatory_router()
    test_failed_verification_skips_regulatory_router()
    test_valid_regulatory_route_completes()
    test_missing_regulatory_route_escalates()

    print("\nAll regulatory handoff tests passed!")
