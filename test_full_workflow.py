
import json

from langchain_core.messages import AIMessage

from backend.agents import clinical_agent
from backend.agents import clinical_tools_node
from backend.agents.graph import pharmacovigilance_workflow
from backend.agents.metrics import agent_metrics


# --------------------------------------------------
# 1. Mock retrieval tool
# --------------------------------------------------

CHUNK_ID = "DOC002_PAGE_32_CHUNK_001"

FAKE_EVIDENCE = [
    {
        "chunk_id": CHUNK_ID,
        "document_id": "DOC002",
        "document_name": "IPC Pharmacovigilance Guidance",
        "scope": "marketed_product",
        "pdf_page": 32,
        "passage": (
            "Hospitalisation is a seriousness criterion "
            "for an adverse event."
        ),
    }
]


class FakeTool:

    def __init__(self, name):
        self.name = name

    def invoke(self, args):
        return FAKE_EVIDENCE


# --------------------------------------------------
# 2. Mock Gemini responses
# --------------------------------------------------

class FakeModel:

    def __init__(self):
        self.call_count = 0

    def invoke(self, messages):
        self.call_count += 1

        # First response: request retrieval.
        if self.call_count == 1:
            return AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "corpus_search_tool",
                        "args": {
                            "query": "hospitalisation seriousness criteria"
                        },
                        "id": "mock-tool-call-1",
                        "type": "tool_call",
                    }
                ],
            )

        # Second response: structured assessment.
        return AIMessage(
            content=json.dumps({
                "reaction_description": "Severe skin peeling",
                "seriousness": "serious",
                "expectedness": "undetermined",
                "causality": "undetermined",
                "reasoning": (
                    "Hospitalisation is recorded. Its relationship "
                    "to the adverse event requires confirmation."
                ),
                "evidence_references": [
                    {
                        "chunk_id": CHUNK_ID,
                        "claim": (
                            "Hospitalisation is a seriousness criterion."
                        ),
                    }
                ],
            })
        )


# --------------------------------------------------
# 3. Replace external dependencies with mocks
# --------------------------------------------------

fake_model = FakeModel()

original_model_factory = clinical_agent.get_clinical_model
original_tool_map = clinical_tools_node.TOOL_MAP.copy()

clinical_agent.get_clinical_model = lambda: fake_model

clinical_tools_node.TOOL_MAP = {
    "corpus_search_tool": FakeTool("corpus_search_tool")
}


# --------------------------------------------------
# 4. Reset metrics before workflow execution
# --------------------------------------------------

agent_metrics.reset()


# --------------------------------------------------
# 5. Run complete LangGraph workflow
# --------------------------------------------------

case = {
    "patient_age": 45,
    "drug_name": "SyntheticDrug-A",
    "reaction_description": "Severe skin peeling",
    "event_onset_date": "2026-11-10",
    "drug_start_date": "2026-11-03",
    "outcome": "hospitalized",
    "hospitalized": True,
    "hospitalization_due_to_event": None,
    "reporting_context": "marketed_product",
}

try:

    result = pharmacovigilance_workflow.invoke(
        {
            "case_id": "SYNTHETIC-TEST-001",
            "case_data": case,
            "tool_call_count": 0,
            "clinical_evidence": [],
            "escalation_required": False,
        },
        config={"recursion_limit": 15},
    )

    # --------------------------------------------------
    # 6. Verify workflow results
    # --------------------------------------------------

    assert result.get("clinical_assessment"), (
        "Clinical assessment was not stored."
    )

    assert result["clinical_assessment"]["seriousness"] == "serious"

    assert any(
        item.get("chunk_id") == CHUNK_ID
        for item in result.get("clinical_evidence", [])
    ), "Retrieved evidence was not collected."

    assert result.get("verification_result"), (
        "Verification agent did not run."
    )

    assert result["verification_result"]["valid_citation_count"] == 1

    assert result.get("escalation_required") is True

    assert fake_model.call_count == 2

    print("PASS: Clinical agent requested retrieval.")
    print("PASS: Retrieval tool executed.")
    print("PASS: Evidence reached clinical assessment.")
    print("PASS: Structured assessment was stored.")
    print("PASS: Verification agent received the evidence.")
    print("PASS: Uncertain case was escalated.")
    print("PASS: No real Gemini API calls were made.")

    # --------------------------------------------------
    # 7. Verify actual LangGraph node metrics
    # --------------------------------------------------

    metrics = agent_metrics.get_all_metrics()

    expected_agents = [
        "clinical_assessment",
        "clinical_tools",
        "verification",
    ]

    for agent in expected_agents:
        assert agent in metrics, (
            f"Metrics missing for {agent}"
        )

        assert metrics[agent]["total_executions"] >= 1, (
            f"{agent} was not recorded."
        )

        assert metrics[agent]["total_execution_time"] > 0, (
            f"Execution time missing for {agent}"
        )

    assert metrics["clinical_tools"]["total_tool_calls"] == 1, (
        "Clinical tool-call metrics are incorrect."
    )

    print("\nPASS: Actual clinical agent metrics recorded.")
    print("PASS: Actual clinical tool metrics recorded.")
    print("PASS: Actual verification metrics recorded.")

    print("\nACTUAL WORKFLOW METRICS:")

    for agent, values in metrics.items():
        print(f"\n{agent}:")
        for key, value in values.items():
            print(f"  {key}: {value}")

    print("\nFinal escalation reasons:")

    for reason in result.get("escalation_reasons", []):
        print("-", reason)

    print("\nFULL WORKFLOW + METRICS TEST PASSED!")

finally:

    # Restore original functions and tools.
    clinical_agent.get_clinical_model = original_model_factory
    clinical_tools_node.TOOL_MAP = original_tool_map
