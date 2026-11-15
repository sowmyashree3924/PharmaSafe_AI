
import json

from langchain_core.messages import ToolMessage

from backend.agents.tools.agent_tools import AVAILABLE_TOOLS

from backend.agents.reliability import (
    run_reliable,
    CircuitOpenError,
    ToolExecutionError,
)


MAX_TOOL_CALLS = 5

TOOL_MAP = {
    tool.name: tool
    for tool in AVAILABLE_TOOLS
}


def clinical_tool_executor(state: dict) -> dict:
    """
    Execute agent-selected tools with:
    - Five-call budget
    - Timeout
    - Bounded retries
    - Exponential backoff
    - Circuit breaker
    - Human escalation on failure
    """

    messages = state.get("messages", [])

    if not messages:
        return {}

    last_message = messages[-1]

    requested_tools = getattr(
        last_message,
        "tool_calls",
        [],
    )

    if not requested_tools:
        return {}

    already_executed = state.get("tool_call_count", 0)
    requested_count = len(requested_tools)

    # Enforce tool-call budget before execution.
    if already_executed + requested_count > MAX_TOOL_CALLS:
        return {
            "escalation_required": True,
            "escalation_reasons": [
                "Maximum tool-call budget exceeded."
            ],
            "current_agent": "human_escalation",
        }

    tool_messages = []
    escalation_reasons = []

    for call in requested_tools:

        tool_name = call["name"]
        tool_args = call["args"]
        tool_call_id = call["id"]

        tool = TOOL_MAP.get(tool_name)

        if tool is None:

            output = {
                "success": False,
                "error": f"Unknown tool requested: {tool_name}",
            }

            escalation_reasons.append(
                f"Unknown tool requested: {tool_name}"
            )

        else:

            try:
                result = run_reliable(
                    tool_name=tool_name,
                    function=lambda: tool.invoke(tool_args),
                )

                output = {
                    "success": True,
                    "result": result,
                }

            except (CircuitOpenError, ToolExecutionError) as error:

                output = {
                    "success": False,
                    "error": str(error),
                }

                escalation_reasons.append(
                    f"Tool {tool_name} failed: {error}"
                )

            except Exception as error:

                output = {
                    "success": False,
                    "error": str(error),
                }

                escalation_reasons.append(
                    f"Unexpected failure in {tool_name}: {error}"
                )

        tool_messages.append(
            ToolMessage(
                content=json.dumps(
                    output,
                    ensure_ascii=False,
                    default=str,
                ),
                tool_call_id=tool_call_id,
            )
        )

    result = {
        "messages": tool_messages,
        "tool_call_count": already_executed + requested_count,
        "tool_calls": already_executed + requested_count,
        "current_agent": "clinical_tools",
    }

    if escalation_reasons:
        result["escalation_required"] = True
        result["escalation_reasons"] = escalation_reasons
        result["current_agent"] = "human_escalation"

    return result
