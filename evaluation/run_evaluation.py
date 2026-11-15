import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from evaluation.scenarios import SCENARIOS
from evaluation.evaluator import compare_scenario


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = PROJECT_ROOT / "evaluation" / "reports"


def evaluate_scenarios():
    results = []

    for scenario in SCENARIOS:
        scenario_id = scenario["id"]
        category = scenario["category"]
        status = scenario.get("evaluation_status", "active")

        if status.startswith("blocked"):
            results.append({
                "scenario_id": scenario_id,
                "category": category,
                "status": "BLOCKED",
                "reason": status,
                "executed": False,
            })
            continue

        # No actual workflow output is supplied yet.
        # Never compare expected values against invented outputs.
        results.append({
            "scenario_id": scenario_id,
            "category": category,
            "status": "UNTESTED",
            "reason": "Workflow execution harness not connected",
            "executed": False,
        })

    return results


def build_summary(results):
    counts = defaultdict(int)
    category_counts = defaultdict(lambda: defaultdict(int))

    for result in results:
        counts[result["status"]] += 1
        category_counts[result["category"]][result["status"]] += 1

    executed = counts["PASS"] + counts["FAIL"]

    pass_rate = (
        counts["PASS"] / executed * 100
        if executed else None
    )

    return {
        "total_scenarios": len(results),
        "passed": counts["PASS"],
        "failed": counts["FAIL"],
        "blocked": counts["BLOCKED"],
        "untested": counts["UNTESTED"],
        "executed": executed,
        "pass_rate_percent": (
            round(pass_rate, 2) if pass_rate is not None else None
        ),
        "category_results": {
            category: dict(values)
            for category, values in category_counts.items()
        },
    }


def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    results = evaluate_scenarios()
    summary = build_summary(results)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evaluation_type": "fixture_readiness_check",
        "summary": summary,
        "results": results,
    }

    report_path = REPORT_DIR / "evaluation_report.json"

    with report_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)

    print("\nPHARMASAFE AI - EVALUATION REPORT")
    print("=" * 42)

    print(f"Total scenarios : {summary['total_scenarios']}")
    print(f"Passed          : {summary['passed']}")
    print(f"Failed          : {summary['failed']}")
    print(f"Blocked         : {summary['blocked']}")
    print(f"Untested        : {summary['untested']}")
    print(f"Executed        : {summary['executed']}")

    print("\nSCENARIO RESULTS")
    print("-" * 42)

    for result in results:
        print(
            f"{result['scenario_id']} | "
            f"{result['category']} | "
            f"{result['status']} | "
            f"{result['reason']}"
        )

    print("\nCATEGORY SUMMARY")
    for category, values in summary["category_results"].items():
        print(f"{category}: {values}")

    print("\nPass rate: Not available (no workflow scenarios executed)")
    print(f"\nJSON report saved to: {report_path}")


if __name__ == "__main__":
    main()
