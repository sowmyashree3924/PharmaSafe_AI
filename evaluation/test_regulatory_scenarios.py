from backend.agents.regulatory_router import regulatory_routing_agent
from evaluation.scenarios import SCENARIOS
from evaluation.evaluator import compare_scenario


def run_regulatory_scenario(scenario):
    case = scenario["case"]

    # Synthetic evidence for testing the router's decision logic.
    # This does not replace real corpus retrieval or verification.
    evidence = []

    if scenario["id"] == "F12":
        evidence = [{
            "chunk_id": "TEST_IPC_SERIOUS_001",
            "scope": "marketed_product",
            "passage": (
                "Serious adverse events must be reported "
                "within 15 calendar days."
            ),
        }]

    state = {
        "case_data": case,
        "clinical_assessment": {
            "seriousness": case.get("seriousness", "undetermined"),
        },
        "verified_evidence": evidence,
    }

    return regulatory_routing_agent(state)


def main():
    selected_ids = {"F12", "F13", "F14"}
    selected = [
        scenario for scenario in SCENARIOS
        if scenario["id"] in selected_ids
    ]

    passed = 0

    print("\nREGULATORY ROUTER EVALUATION")
    print("=" * 45)

    for scenario in selected:
        actual = run_regulatory_scenario(scenario)
        comparison = compare_scenario(
            scenario["expected"],
            actual,
        )

        status = "PASS" if comparison["passed"] else "FAIL"

        if comparison["passed"]:
            passed += 1

        print(
            f"\n{scenario['id']} | {scenario['category']} | {status}"
        )

        for field, result in comparison["comparisons"].items():
            print(
                f"  {field}: expected={result['expected']}, "
                f"actual={result['actual']}"
            )

        if comparison["missing_fields"]:
            print("  Missing:", comparison["missing_fields"])

        if actual.get("escalation_reasons"):
            for reason in actual["escalation_reasons"]:
                print("  Reason:", reason)

    print("\nSUMMARY")
    print(f"Executed: {len(selected)}")
    print(f"Passed:   {passed}")
    print(f"Failed:   {len(selected) - passed}")
    print(
        "Pass rate:",
        f"{passed / len(selected) * 100:.1f}%"
        if selected else "N/A",
    )


if __name__ == "__main__":
    main()


def test_regulatory_scenario_suite(capsys):
    main()
    output = capsys.readouterr().out
    assert "Failed:0" in "".join(output.split())
