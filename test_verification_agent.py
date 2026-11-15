from backend.agents.verification_agent import (
    evidence_verification_agent,
)


def test_valid_citation_but_uncertain_case():

    evidence = [
        {
            "chunk_id": "DOC002_PAGE_32_CHUNK_001",
            "document_id": "DOC002",
            "document_name": "IPC Pharmacovigilance Guidance",
            "scope": "marketed_product",
            "pdf_page": 32,
            "passage": (
                "Hospitalisation is a seriousness criterion "
                "for an adverse event."
            ),
        }
    ]

    state = {
        "case_data": {
            "reporting_context": "marketed_product",
            "hospitalized": True,
            "hospitalization_due_to_event": None,
        },
        "clinical_assessment": {
            "reaction_description": "Severe skin peeling",
            "seriousness": "serious",
            "expectedness": "undetermined",
            "causality": "undetermined",
            "reasoning": "Hospitalisation is recorded.",
            "evidence_references": [
                {
                    "chunk_id": "DOC002_PAGE_32_CHUNK_001",
                    "claim": (
                        "Hospitalisation is a seriousness criterion."
                    ),
                }
            ],
        },
        "clinical_evidence": evidence,
    }

    result = evidence_verification_agent(state)

    assert result["verification_result"]["valid_citation_count"] == 1
    assert result["escalation_required"] is True

    print("PASS: Citation resolved.")
    print("PASS: Uncertain expectedness triggers escalation.")
    print("PASS: Unconfirmed hospitalisation relationship triggers escalation.")


def test_fabricated_citation_rejected():

    state = {
        "case_data": {
            "reporting_context": "marketed_product",
        },
        "clinical_assessment": {
            "seriousness": "undetermined",
            "expectedness": "undetermined",
            "evidence_references": [
                {
                    "chunk_id": "FAKE_CHUNK",
                    "claim": "Hospitalisation is a seriousness criterion.",
                }
            ],
        },
        "clinical_evidence": [],
    }

    result = evidence_verification_agent(state)

    assert result["escalation_required"] is True
    assert result["verification_result"]["valid_citation_count"] == 0

    print("PASS: Fabricated citation rejected.")


if __name__ == "__main__":
    test_valid_citation_but_uncertain_case()
    test_fabricated_citation_rejected()

    print("\nAll verification agent tests passed!")
