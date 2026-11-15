

from langchain_core.tools import tool

from backend.agents.tools.corpus_search import search_corpus
from backend.agents.tools.clause_lookup import lookup_clause
from backend.agents.tools.case_lookup import lookup_case_fields


@tool
def corpus_search_tool(query: str, scope: str = "") -> list[dict]:
    """Search the pharmacovigilance evidence corpus semantically.

    Use scope='marketed_product' for MAH guidance,
    'clinical_trial' for clinical-trial regulations,
    or 'causality_assessment' for WHO-UMC criteria.
    """
    return search_corpus(
        query=query,
        scope=scope or None,
        k=5,
    )


@tool
def clause_lookup_tool(clause_id: str) -> list[dict]:
    """Retrieve a known regulatory clause.

    Available IDs:
    seriousness_criteria,
    serious_ae_reporting,
    non_serious_ae_reporting,
    causality_assessment,
    clinical_trial_rule_42.
    """
    return lookup_clause(clause_id)


AVAILABLE_TOOLS = [
    corpus_search_tool,
    clause_lookup_tool,
]

# Case lookup is deliberately NOT an LLM tool.
# The workflow will call it directly using the original case data.
def run_case_lookup(case: dict) -> dict:
    return lookup_case_fields(case)
