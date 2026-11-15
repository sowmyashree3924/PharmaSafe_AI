
from backend.agents.state import PharmacovigilanceState


def escalation_agent(state: PharmacovigilanceState) -> dict:
    reasons = state.get("escalation_reasons", [])

    return {
        "reporting_route": "human_review",
        "escalation_required": True,
        "current_agent": "human_escalation",
        "escalation_reasons": reasons or [
            "The case requires review by a qualified pharmacovigilance professional."
        ],
    }
