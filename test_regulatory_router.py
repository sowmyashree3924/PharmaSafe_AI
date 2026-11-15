from backend.agents.regulatory_router import regulatory_routing_agent


SERIOUS_EVIDENCE = [
    {
        "chunk_id": "IPC_SERIOUS_001",
        "scope": "marketed_product",
        "passage": (
            "Serious adverse events shall be reported "
            "within 15 calendar days."
        ),
    }
]

NON_SERIOUS_EVIDENCE = [
    {
        "chunk_id": "IPC_NON_SERIOUS_001",
        "scope": "marketed_product",
        "passage": (
            "Non-serious adverse events shall be reported "
            "within 90 days."
        ),
    }
]


def test_serious_case():
    state = {
        "case_data": {
            "reporting_context": "marketed_product",
            "hospitalized": True,
            "hospitalization_due_to_event": True,
        },
        "clinical_assessment": {
            "seriousness": "serious",
        },
        "verified_evidence": SERIOUS_EVIDENCE,
    }

    result = regulatory_routing_agent(state)

    assert result["reporting_route"] == "expedited"
    assert result["reporting_timeline"] == "Within 15 calendar days"
    assert result["escalation_required"] is False

    print("PASS: Serious case receives expedited reporting route.")


def test_non_serious_case():
    state = {
        "case_data": {
            "reporting_context": "marketed_product",
        },
        "clinical_assessment": {
            "seriousness": "non_serious",
        },
        "verified_evidence": NON_SERIOUS_EVIDENCE,
    }

    result = regulatory_routing_agent(state)

    assert result["reporting_route"] == "non_serious_reporting"
    assert result["reporting_timeline"] == "Within 90 days"
    assert result["escalation_required"] is False

    print("PASS: Non-serious case receives 90-day reporting route.")


def test_uncertain_hospitalisation():
    state = {
        "case_data": {
            "reporting_context": "marketed_product",
            "hospitalized": True,
            "hospitalization_due_to_event": None,
        },
        "clinical_assessment": {
            "seriousness": "serious",
        },
        "verified_evidence": SERIOUS_EVIDENCE,
    }

    result = regulatory_routing_agent(state)

    assert result["reporting_route"] == "human_review"
    assert result["escalation_required"] is True

    print("PASS: Uncertain hospitalisation triggers human review.")


def test_clinical_trial_context():
    state = {
        "case_data": {
            "reporting_context": "clinical_trial",
        },
        "clinical_assessment": {
            "seriousness": "serious",
        },
        "verified_evidence": SERIOUS_EVIDENCE,
    }

    result = regulatory_routing_agent(state)

    assert result["reporting_route"] == "human_review"
    assert result["escalation_required"] is True

    print("PASS: Clinical-trial case is not assigned MAH route.")


if __name__ == "__main__":
    test_serious_case()
    test_non_serious_case()
    test_uncertain_hospitalisation()
    test_clinical_trial_context()

    print("\nAll regulatory routing tests passed!")
