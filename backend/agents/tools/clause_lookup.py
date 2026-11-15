
from backend.agents.tools.corpus_search import search_corpus


CLAUSE_QUERIES = {
    "seriousness_criteria": (
        "IPC section 2.5.3.6 seriousness criteria including "
        "death, life-threatening events, hospitalisation, disability "
        "and other medically important conditions"
    ),
    "serious_ae_reporting": (
        "IPC section 2.7.1 reporting serious adverse events "
        "by marketing authorization holders within 15 calendar days"
    ),
    "non_serious_ae_reporting": (
        "IPC section 2.7.2 reporting non-serious adverse events "
        "within 90 calendar days"
    ),
    "causality_assessment": (
        "IPC section 2.8 WHO-UMC causality assessment"
    ),
    "clinical_trial_rule_42": (
        "New Drugs and Clinical Trials Rules 2019 Rule 42 "
        "clinical trial serious adverse event reporting"
    ),
}


def lookup_clause(clause_id: str) -> list[dict]:
    if clause_id not in CLAUSE_QUERIES:
        raise ValueError(f"Unknown clause: {clause_id}")

    scope = (
        "clinical_trial"
        if clause_id == "clinical_trial_rule_42"
        else "marketed_product"
    )

    if clause_id == "causality_assessment":
        scope = "causality_assessment"

    return search_corpus(
        query=CLAUSE_QUERIES[clause_id],
        scope=scope,
        k=3,
    )


if __name__ == "__main__":
    results = lookup_clause("serious_ae_reporting")

    for item in results:
        print("\n----------------------------")
        print("Document:", item["document_name"])
        print("Page:", item["pdf_page"])
        print("Scope:", item["scope"])
        print("Evidence:", item["passage"][:500])
