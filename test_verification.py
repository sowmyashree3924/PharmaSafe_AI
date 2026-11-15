
from backend.agents.verification_agent import evidence_verification_agent


def test_missing_package_insert_escalates():

    evidence = [
        {
            "chunk_id": "DOC002_PAGE_32_CHUNK_001",
            "document_id": "DOC002",
            "document_name": "Pharmacovigilance Guidance for Marketing Authorization Holders",
            "scope": "marketed_product",
            "pdf_page": 32,
            "passage": "Hospitalisation is a seriousness criterion.",
        }
    ]

    state = {
        "case_data": {
            "hospitalized": True,
            "hospitalization_due_to_event": None,
        },
        "clinical_assessment": {
            "seriousness": "serious",
            "expectedness": "undetermined",
            "evidence_references": [
                {"chunk_id": "DOC002_PAGE_32_CHUNK_001"}
            ],
        },
        "clinical_evidence": evidence,
    }

    result = evidence_verification_agent(state)

    assert result["escalation_required"] is True
    assert result["verification_result"]["passed"] is False

    print("PASS: Missing package insert triggers escalation.")
    print(
        "Verified citations:",
        result["verification_result"]["valid_citation_count"],
    )

    print("Escalation reasons:")
    for reason in result["escalation_reasons"]:
        print("-", reason)


if __name__ == "__main__":
    test_missing_package_insert_escalates()
