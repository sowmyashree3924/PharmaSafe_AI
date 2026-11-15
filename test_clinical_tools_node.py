
from langchain_core.messages import AIMessage, ToolMessage
from backend.agents import clinical_tools_node


class FakeTool:
    def __init__(self, name):
        self.name = name

    def invoke(self, args):
        return {"result": "success", "args": args}


def make_call(name, call_id):
    return {
        "name": name,
        "args": {"query": "test query"},
        "id": call_id,
        "type": "tool_call",
    }


def test_oversized_batch_is_blocked():
    message = AIMessage(
        content="",
        tool_calls=[
            make_call("corpus_search_tool", "1"),
            make_call("corpus_search_tool", "2"),
            make_call("corpus_search_tool", "3"),
        ],
    )

    result = clinical_tools_node.clinical_tool_executor({
        "messages": [message],
        "tool_call_count": 3,
    })

    assert result["escalation_required"] is True
    print("PASS: Oversized batch blocked.")


def test_exact_limit_executes():
    original_map = clinical_tools_node.TOOL_MAP

    try:
        clinical_tools_node.TOOL_MAP = {
            "corpus_search_tool": FakeTool("corpus_search_tool")
        }

        message = AIMessage(
            content="",
            tool_calls=[
                make_call("corpus_search_tool", "4"),
                make_call("corpus_search_tool", "5"),
            ],
        )

        result = clinical_tools_node.clinical_tool_executor({
            "messages": [message],
            "tool_call_count": 3,
        })

        assert result["tool_call_count"] == 5
        assert len(result["messages"]) == 2
        assert all(
            isinstance(msg, ToolMessage)
            for msg in result["messages"]
        )

        print("PASS: Exactly five calls execute successfully.")

    finally:
        clinical_tools_node.TOOL_MAP = original_map


if __name__ == "__main__":
    test_oversized_batch_is_blocked()
    test_exact_limit_executes()
    print("\nAll executor tests passed!")
