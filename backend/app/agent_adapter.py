
from backend.agents.graph import pharmacovigilance_workflow


async def run_agent(case_payload: dict) -> dict:
    """
    Adapt Member 3 API payload to Member 2's LangGraph workflow.
    """

    # Convert API field names to the names expected by the AI agents.
    case_data = dict(case_payload)

    case_data["event_onset_date"] = case_payload.get(
        "onset_date"
    )

    # Derive hospitalisation from the reported outcome.
    case_data["hospitalized"] = (
        case_payload.get("outcome") == "hospitalisation"
    )

    # Default reporting context for marketed products.
    case_data["reporting_context"] = case_payload.get(
        "reporting_context",
        "marketed_product"
    )

    initial_state = {
        "case_id": case_payload["case_id"],
        "case_data": case_data,
        "messages": [],
        "tool_call_count": 0,
        "tool_calls": 0,
        "escalation_required": False,
        "escalation_reasons": [],
        "clinical_evidence": [],
        "errors": [],
    }

    result = await pharmacovigilance_workflow.ainvoke(initial_state)

    assessment = result.get("clinical_assessment") or {}
    verification = result.get("verification_result") or {}

    escalation_required = result.get("escalation_required", False)
    reporting_route = result.get("reporting_route", "")

    if escalation_required or not reporting_route:
        decision_status = "human_review_required"
        routing_recommendation = "escalate_to_human"
    else:
        decision_status = "completed"
        routing_recommendation = reporting_route

    escalation_reasons = result.get("escalation_reasons") or []

    return {
        "decision_status": decision_status,
        "routing_recommendation": routing_recommendation,
        "seriousness": {
            "value": assessment.get("seriousness", "undetermined"),
            "reason": assessment.get("reasoning", ""),
        },
        "expectedness": {
            "value": assessment.get("expectedness", "undetermined"),
            "reason": assessment.get("reasoning", ""),
        },
        "clinical_assessment": assessment,
        "verification": verification,
        "reporting_route": reporting_route,
        "reporting_timeline": result.get("reporting_timeline", ""),
        "citations": assessment.get("evidence_references", []),
        "escalation_reason": "; ".join(escalation_reasons),
        "disclaimer": (
            "Decision support only. A qualified pharmacovigilance "
            "professional must make the final determination."
        ),
    }
