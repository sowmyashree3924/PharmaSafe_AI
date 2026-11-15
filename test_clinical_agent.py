
from backend.agents.clinical_agent import clinical_assessment_agent


synthetic_case = {
    "patient_age": 45,
    "drug_name": "SyntheticDrug-A",
    "reaction_description": "Severe skin peeling",
    "event_onset_date": "2026-11-10",
    "drug_start_date": "2026-11-03",
    "outcome": "hospitalized",
    "hospitalized": True,
}

state = {
    "case_id": "TEST-001",
    "case_data": synthetic_case,
}

result = clinical_assessment_agent(state)

print("\nCLINICAL ASSESSMENT")
print(result["clinical_assessment"])

print("\nRETRIEVED EVIDENCE")

for evidence in result["clinical_evidence"]:
    print(
        evidence["document_name"],
        "| Page:", evidence["pdf_page"],
        "| Chunk:", evidence["chunk_id"],
    )
