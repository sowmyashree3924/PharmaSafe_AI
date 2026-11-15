import time

from backend.agents.metrics import agent_metrics, track_agent


@track_agent("clinical_assessment")
def fake_clinical_agent(state):
    time.sleep(0.02)
    return {
        "clinical_assessment": {"seriousness": "serious"},
        "tool_call_count": 2,
    }


@track_agent("verification")
def fake_verification_agent(state):
    return {
        "escalation_required": True,
        "tool_call_count": state.get("tool_call_count", 0),
    }


def test_successful_execution():
    agent_metrics.reset()

    fake_clinical_agent({"tool_call_count": 0})

    metrics = agent_metrics.get_agent_metrics("clinical_assessment")

    assert metrics["total_executions"] == 1
    assert metrics["successful_executions"] == 1
    assert metrics["failed_executions"] == 0
    assert metrics["total_tool_calls"] == 2
    assert metrics["total_execution_time"] > 0

    print("PASS: Successful execution and tool calls recorded.")


def test_failed_execution():
    fake_verification_agent({"tool_call_count": 0})

    metrics = agent_metrics.get_agent_metrics("verification")

    assert metrics["total_executions"] == 1
    assert metrics["failed_executions"] == 1

    print("PASS: Escalated execution recorded.")


def test_metrics_summary():
    all_metrics = agent_metrics.get_all_metrics()

    assert "clinical_assessment" in all_metrics
    assert "verification" in all_metrics

    print("PASS: Multiple agent metrics recorded.")


if __name__ == "__main__":
    test_successful_execution()
    test_failed_execution()
    test_metrics_summary()

    print("\nAll metrics tests passed!")

    for agent, metrics in agent_metrics.get_all_metrics().items():
        print(f"\n{agent}:")
        for key, value in metrics.items():
            print(f"  {key}: {value}")
