from backend.agents.clinical_agent import (
    parse_clinical_assessment,
    validate_assessment_citations,
)

sample_response = """
{
  "reaction_description": "Severe skin peeling",
  "seriousness": "serious",
  "expectedness": "undetermined",
  "causality": "possible",
  "reasoning": "Hospitalisation is recorded, but its relationship to the event requires confirmation.",
  "evidence_references": [
    {
      "chunk_id": "DOC002_PAGE_32_CHUNK_001",
      "claim": "Hospitalisation is a seriousness criterion."
    }
  ]
}
"""

evidence = [
    {
        "chunk_id": "DOC002_PAGE_32_CHUNK_001",
        "document_id": "DOC002",
        "pdf_page": 32,
        "passage": "Hospitalisation is a seriousness criterion.",
    }
]

assessment = parse_clinical_assessment(sample_response)

passed, errors = validate_assessment_citations(
    assessment,
    evidence,
)

assert assessment["seriousness"] == "serious"
assert assessment["expectedness"] == "undetermined"
assert passed is True

print("PASS: Structured assessment parsed.")
print("PASS: Valid citation accepted.")

# Check that a fabricated citation is rejected.
assessment["evidence_references"][0]["chunk_id"] = "FAKE_CHUNK"

passed, errors = validate_assessment_citations(
    assessment,
    evidence,
)

assert passed is False

print("PASS: Fabricated citation rejected.")
print("\nAll structured assessment tests passed!")
