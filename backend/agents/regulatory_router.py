
from backend.agents.state import PharmacovigilanceState


def normalize_text(value):
    if not isinstance(value, str):
        return ""

    return " ".join(value.lower().split())


def has_reporting_evidence(evidence, required_terms):
    """
    Check that retrieved marketed-product evidence
    contains the required reporting timeline.
    """

    for item in evidence:

        if item.get("scope") != "marketed_product":
            continue

        passage = normalize_text(item.get("passage", ""))

        if all(term in passage for term in required_terms):
            return True

    return False


def regulatory_routing_agent(
    state: PharmacovigilanceState,
) -> dict:
    """
    Determine the reporting pathway using verified evidence.

    Supported currently:
    - Serious AE: expedited reporting within 15 calendar days.
    - Non-serious AE: reporting within 90 days.
    - Unclear cases: human review.

    Periodic and non-reportable classifications are deliberately
    not inferred without supporting regulatory evidence.
    """

    case = state.get("case_data", {})
    assessment = state.get("clinical_assessment", {})
    evidence = state.get("verified_evidence", [])

    reasons = []

    reporting_context = case.get("reporting_context")

    # Do not apply marketed-product timelines to clinical trials.
    if reporting_context != "marketed_product":
        reasons.append(
            "Reporting context is missing or is not a marketed-product case. "
            "The applicable regulatory pathway requires review."
        )

    # Require verified marketed-product evidence.
    marketed_evidence = [
        item for item in evidence
        if item.get("scope") == "marketed_product"
    ]

    if not marketed_evidence:
        reasons.append(
            "No verified marketed-product reporting evidence is available."
        )

    seriousness = assessment.get("seriousness")

    # Serious adverse event pathway.
    if seriousness == "serious":

        if (
            case.get("hospitalized") is True
            and case.get("hospitalization_due_to_event") is not True
        ):
            reasons.append(
                "Hospitalisation is recorded, but its relationship "
                "to the adverse event has not been confirmed."
            )

        if not has_reporting_evidence(
            marketed_evidence,
            ["15 calendar days"],
        ):
            reasons.append(
                "The 15-calendar-day serious AE reporting timeline "
                "is not established by the verified evidence."
            )

        if not reasons:
            return {
                "reporting_route": "expedited",
                "reporting_timeline": "Within 15 calendar days",
                "escalation_required": False,
                "escalation_reasons": [],
                "current_agent": "regulatory_routing",
            }

    # Non-serious adverse event pathway.
    elif seriousness == "non_serious":

        if not has_reporting_evidence(
            marketed_evidence,
            ["90 days"],
        ):
            reasons.append(
                "The 90-day non-serious AE reporting timeline "
                "is not established by the verified evidence."
            )

        if not reasons:
            return {
                "reporting_route": "non_serious_reporting",
                "reporting_timeline": "Within 90 days",
                "escalation_required": False,
                "escalation_reasons": [],
                "current_agent": "regulatory_routing",
            }

    else:
        reasons.append(
            "Seriousness is undetermined; a reporting pathway "
            "cannot be assigned automatically."
        )

    # Never guess periodic or non-reportable status.
    return {
        "reporting_route": "human_review",
        "reporting_timeline": "Not determined",
        "escalation_required": True,
        "escalation_reasons": list(dict.fromkeys(reasons)),
        "current_agent": "human_escalation",
    }
