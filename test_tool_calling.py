

from langchain_core.messages import AIMessage

from backend.agents.clinical_tools_node import clinical_tool_executor


def make_tool_call(name, call_id):
    return {
        "name": name,
        "args": {"clause_id": "seriousness_criteria"}
        if name == "clause_lookup_tool"
        else {"query": "seriousness criteria"},
        "id": call_id,
        "type": "tool_call",
    }


def test_budget_blocks_oversized_batch():
    fake_message = AIMessage(
        content="",
        tool_calls=[
            make_tool_call("clause_lookup_tool", "test-1"),
            make_tool_call("corpus_search_tool", "test-2"),
            make_tool_call("clause_lookup_tool", "test-3"),
        ],
    )

    state = {
        "messages": [fake_message],
        "tool_call_count": 3,
    }

    result = clinical_tool_executor(state)

    assert result["escalation_required"] is True
    assert result["current_agent"] == "human_escalation"

    print("PASS: Oversized tool batch was blocked.")
    print("Executed calls remain:", state["tool_call_count"])
    print("Escalation:", result["escalation_required"])


if __name__ == "__main__":
    test_budget_blocks_oversized_batch()
