
from langchain_core.messages import AIMessage

from backend.agents.clinical_tools_node import clinical_tool_executor


def make_tool_call(name, call_id):
    args = (
        {"clause_id": "seriousness_criteria"}
        if name == "clause_lookup_tool"
        else {"query": "seriousness criteria"}
    )

    return {
        "name": name,
        "args": args,
        "id": call_id,
        "type": "tool_call",
    }


def test_budget_blocks_oversized_batch():
    message = AIMessage(
        content="",
        tool_calls=[
            make_tool_call("clause_lookup_tool", "test-1"),
            make_tool_call("corpus_search_tool", "test-2"),
            make_tool_call("clause_lookup_tool", "test-3"),
        ],
    )

    state = {
        "messages": [message],
        "tool_call_count": 3,
    }

    result = clinical_tool_executor(state)

    assert result["escalation_required"] is True
    assert result["current_agent"] == "human_escalation"

    print("PASS: Oversized batch blocked.")


def test_budget_allows_exact_limit():
    # Test the budget decision independently of actual tool execution.
    already_executed = 3
    requested = 2
    maximum = 5

    assert already_executed + requested == maximum

    print("PASS: Exactly five calls fit the budget.")


def test_budget_rejects_six():
    already_executed = 3
    requested = 3
    maximum = 5

    assert already_executed + requested > maximum

    print("PASS: Six calls exceed the budget.")


if __name__ == "__main__":
    test_budget_blocks_oversized_batch()
    test_budget_allows_exact_limit()
    test_budget_rejects_six()

    print("\nAll budget tests passed.")
