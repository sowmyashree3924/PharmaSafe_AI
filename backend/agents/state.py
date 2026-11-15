
from typing import Any, TypedDict
from typing_extensions import Annotated
from langgraph.graph.message import add_messages


class PharmacovigilanceState(TypedDict, total=False):

    # Case identification and input
    case_id: str
    case_data: dict[str, Any]

    # Extracted clinical fields
    extracted_fields: dict[str, Any]
    missing_fields: list[str]

    # Agent conversation
    messages: Annotated[list, add_messages]
    current_agent: str

    # Tool execution limits
    tool_call_count: int
    tool_calls: int

    # Clinical assessment
    clinical_assessment: dict[str, Any]
    clinical_evidence: list[dict[str, Any]]

    # Evidence verification
    verification_result: dict[str, Any]
    verified_evidence: list[dict[str, Any]]

    # Regulatory routing
    reporting_route: str
    reporting_timeline: str

    # Escalation
    escalation_required: bool
    escalation_reasons: list[str]

    # Errors
    errors: list[str]
