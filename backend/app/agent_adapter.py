"""Integration seam for Member 2's LangGraph/CrewAI workflow.

Replace run_agent() with the agreed Member 2 import/function once their
agent graph is merged. Until then, this adapter deliberately escalates
rather than inventing a pharmacovigilance determination.
"""
async def run_agent(case_payload: dict) -> dict:
    # TODO MEMBER 2 INTEGRATION:
    # from agents.graph import run_pharmacovigilance_graph
    # return await run_pharmacovigilance_graph(case_payload)
    return {
        "decision_status": "human_review_required",
        "routing_recommendation": "escalate_to_human",
        "seriousness": {"value": "undetermined", "reason": "Agent workflow is not connected."},
        "expectedness": {"value": "undetermined", "reason": "Agent workflow is not connected."},
        "citations": [],
        "escalation_reason": "Member 2's verified agent workflow has not yet been integrated.",
        "disclaimer": "Decision support only. A qualified pharmacovigilance professional must decide."
    }
