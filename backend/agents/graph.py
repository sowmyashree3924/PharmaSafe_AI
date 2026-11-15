
from langgraph.graph import StateGraph, START, END

from backend.agents.state import PharmacovigilanceState

from backend.agents.clinical_agent import (
    clinical_agent_node,
    clinical_tool_router,
)

from backend.agents.clinical_tools_node import (
    clinical_tool_executor,
)

from backend.agents.verification_agent import (
    evidence_verification_agent,
)

from backend.agents.regulatory_router import (
    regulatory_routing_agent,
)

from backend.agents.escalation import (
    escalation_agent,
)

from backend.agents.metrics import track_agent


# Instrument actual workflow nodes.
tracked_clinical_agent = track_agent(
    "clinical_assessment"
)(clinical_agent_node)

tracked_clinical_tools = track_agent(
    "clinical_tools"
)(clinical_tool_executor)

tracked_verification_agent = track_agent(
    "verification"
)(evidence_verification_agent)

tracked_regulatory_router = track_agent(
    "regulatory_routing"
)(regulatory_routing_agent)


def route_after_clinical_assessment(state):
    """Choose retrieval, verification, or escalation."""

    if state.get("escalation_required", False):
        return "escalation"

    return clinical_tool_router(state)


def route_after_tool_execution(state):
    """Return to clinical assessment or escalate."""

    if state.get("escalation_required", False):
        return "escalation"

    return "clinical_assessment"


def route_after_verification(state):
    """Only verified assessments proceed to regulatory routing."""

    if state.get("escalation_required", False):
        return "escalation"

    return "regulatory_routing"


def route_after_regulatory_routing(state):
    """Finish if a route is established, otherwise escalate."""

    if state.get("escalation_required", False):
        return "escalation"

    if not state.get("reporting_route"):
        return "escalation"

    return END


def build_workflow():

    workflow = StateGraph(PharmacovigilanceState)

    # Register instrumented workflow nodes.

    workflow.add_node(
        "clinical_assessment",
        tracked_clinical_agent,
    )

    workflow.add_node(
        "clinical_tools",
        tracked_clinical_tools,
    )

    workflow.add_node(
        "verification",
        tracked_verification_agent,
    )

    workflow.add_node(
        "regulatory_routing",
        tracked_regulatory_router,
    )

    workflow.add_node(
        "escalation",
        escalation_agent,
    )

    # Workflow entry.

    workflow.add_edge(
        START,
        "clinical_assessment",
    )

    # Clinical agent dynamically selects tools.

    workflow.add_conditional_edges(
        "clinical_assessment",
        route_after_clinical_assessment,
        {
            "tools": "clinical_tools",
            "assessment_complete": "verification",
            "escalation": "escalation",
        },
    )

    # Tool responses return to the clinical agent.

    workflow.add_conditional_edges(
        "clinical_tools",
        route_after_tool_execution,
        {
            "clinical_assessment": "clinical_assessment",
            "escalation": "escalation",
        },
    )

    # Verification must pass before regulatory routing.

    workflow.add_conditional_edges(
        "verification",
        route_after_verification,
        {
            "regulatory_routing": "regulatory_routing",
            "escalation": "escalation",
        },
    )

    # Regulatory routing produces the final route or escalates.

    workflow.add_conditional_edges(
        "regulatory_routing",
        route_after_regulatory_routing,
        {
            "escalation": "escalation",
            END: END,
        },
    )

    # Human escalation is terminal.

    workflow.add_edge(
        "escalation",
        END,
    )

    return workflow.compile()


pharmacovigilance_workflow = build_workflow()
