from backend.agents.verification_agent import evidence_verification_agent


def make_evidence(
    chunk_id="DOC002_PAGE_32_CHUNK_001",
    scope="marketed_product",
    passage="Hospitalisation is a seriousness criterion for an adverse event.",
):
    return {
        "chunk_id": chunk_id,
        "document_id": "DOC002",
        "document_name": "IPC Pharmacovigilance Guidance",
        "pdf_page": 32,
        "scope": scope,
        "passage": passage,
    }


def run_test(name, assessment, case, evidence, expected_escalation):
    state = {
        "clinical_assessment": assessment,
        "case_data": case,
        "clinical_evidence": evidence,
    }

    result = evidence_verification_agent(state)

    actual = result["escalation_required"]
    passed = actual == expected_escalation

    print(
        f"{name}: {'PASS' if passed else 'FAIL'} "
        f"(expected escalation={expected_escalation}, actual={actual})"
    )

    if result["verification_result"]["reasons"]:
        for reason in result["verification_result"]["reasons"]:
            print("  Reason:", reason)

    return passed


def main():
    results = []

    # F01: Serious reaction with confirmed hospitalization relationship.
    results.append(run_test(
        "F01 - Seriousness",
        {
            "seriousness": "serious",
            "expectedness": "undetermined",
            "evidence_references": [{
                "chunk_id": "DOC002_PAGE_32_CHUNK_001",
                "claim": "Hospitalisation is a seriousness criterion.",
            }],
        },
        {
            "reporting_context": "marketed_product",
            "hospitalized": True,
            "hospitalization_due_to_event": True,
        },
        [make_evidence()],
        True,
    ))

    # F02: Non-serious reaction, but expectedness remains undetermined.
    results.append(run_test(
        "F02 - Non-serious headache",
        {
            "seriousness": "non_serious",
            "expectedness": "undetermined",
            "evidence_references": [{
                "chunk_id": "DOC002_PAGE_32_CHUNK_001",
                "claim": "Hospitalisation is a seriousness criterion.",
            }],
        },
        {"reporting_context": "marketed_product", "hospitalized": False},
        [make_evidence()],
        True,
    ))

    # F03: Hospitalization relationship is unknown.
    results.append(run_test(
        "F03 - Uncertain hospitalization",
        {
            "seriousness": "serious",
            "expectedness": "undetermined",
            "evidence_references": [{
                "chunk_id": "DOC002_PAGE_32_CHUNK_001",
                "claim": "Hospitalisation is a seriousness criterion.",
            }],
        },
        {
            "reporting_context": "marketed_product",
            "hospitalized": True,
            "hospitalization_due_to_event": None,
        },
        [make_evidence()],
        True,
    ))

    # F04: Mild nausea, expectedness remains undetermined.
    results.append(run_test(
        "F04 - Non-serious nausea",
        {
            "seriousness": "non_serious",
            "expectedness": "undetermined",
            "evidence_references": [{
                "chunk_id": "DOC002_PAGE_32_CHUNK_001",
                "claim": "Hospitalisation is a seriousness criterion.",
            }],
        },
        {"reporting_context": "marketed_product", "hospitalized": False},
        [make_evidence()],
        True,
    ))

    # F05: Serious life-threatening reaction.
    results.append(run_test(
        "F05 - Serious respiratory reaction",
        {
            "seriousness": "serious",
            "expectedness": "undetermined",
            "evidence_references": [{
                "chunk_id": "DOC002_PAGE_32_CHUNK_001",
                "claim": "Hospitalisation is a seriousness criterion.",
            }],
        },
        {
            "reporting_context": "marketed_product",
            "hospitalized": True,
            "hospitalization_due_to_event": True,
        },
        [make_evidence()],
        True,
    ))

    # F06: No approved package insert; expectedness cannot be determined.
    results.append(run_test(
        "F06 - Missing package insert",
        {
            "seriousness": "undetermined",
            "expectedness": "undetermined",
            "evidence_references": [{
                "chunk_id": "DOC002_PAGE_32_CHUNK_001",
                "claim": "Hospitalisation is a seriousness criterion.",
            }],
        },
        {"reporting_context": "marketed_product", "hospitalized": False},
        [make_evidence()],
        True,
    ))

    # F17: No evidence supplied.
    results.append(run_test(
        "F17 - Missing evidence",
        {
            "seriousness": "undetermined",
            "expectedness": "undetermined",
            "evidence_references": [],
        },
        {"reporting_context": "marketed_product"},
        [],
        True,
    ))

    # F18: Citation points to a nonexistent chunk.
    results.append(run_test(
        "F18 - Invalid citation",
        {
            "seriousness": "undetermined",
            "expectedness": "undetermined",
            "evidence_references": [{
                "chunk_id": "NON_EXISTENT_CHUNK",
                "claim": "Hospitalisation is a seriousness criterion.",
            }],
        },
        {"reporting_context": "marketed_product"},
        [make_evidence()],
        True,
    ))

    # Additional test: clinical-trial evidence cannot support a
    # marketed-product reporting assessment.
    results.append(run_test(
        "SCOPE - Clinical trial evidence",
        {
            "seriousness": "serious",
            "expectedness": "undetermined",
            "evidence_references": [{
                "chunk_id": "TRIAL_CHUNK_001",
                "claim": "Hospitalisation is a seriousness criterion.",
            }],
        },
        {"reporting_context": "marketed_product"},
        [make_evidence(
            chunk_id="TRIAL_CHUNK_001",
            scope="clinical_trial",
        )],
        True,
    ))

    passed = sum(results)
    total = len(results)

    print("\nVERIFICATION EVALUATION SUMMARY")
    print("=" * 40)
    print(f"Executed: {total}")
    print(f"Passed:   {passed}")
    print(f"Failed:   {total - passed}")
    print(f"Pass rate: {passed / total * 100:.1f}%")


if __name__ == "__main__":
    main()


def test_verification_scenario_suite(capsys):
    main()
    output = capsys.readouterr().out
    assert "Failed:0" in "".join(output.split())
