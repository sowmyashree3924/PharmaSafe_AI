from backend.agents.tools.case_lookup import lookup_case_fields
from evaluation.scenarios import SCENARIOS


def run_test(scenario_id, expected_missing):
    scenario = next(
        item for item in SCENARIOS
        if item["id"] == scenario_id
    )

    result = lookup_case_fields(scenario["case"])

    actual_missing = set(result["missing_fields"])
    expected_missing = set(expected_missing)

    passed = expected_missing.issubset(actual_missing)

    print(
        f"{scenario_id}: {'PASS' if passed else 'FAIL'}"
    )
    print("  Missing fields:", result["missing_fields"])
    print("  Complete:", result["complete"])

    return passed


def main():
    results = []

    results.append(run_test(
        "F09",
        ["drug_name", "patient_age", "event_onset_date",
         "drug_start_date", "outcome", "hospitalized"],
    ))

    results.append(run_test(
        "F10",
        ["event_onset_date", "drug_start_date",
         "patient_age", "drug_name", "outcome", "hospitalized"],
    ))

    results.append(run_test(
        "F11",
        ["outcome", "patient_age", "event_onset_date",
         "drug_start_date", "hospitalized"],
    ))

    # Test supported aliases.
    alias_case = {
        "age": 45,
        "drug": "SyntheticDrug-C",
        "reaction": "Dizziness",
        "onset_date": "2026-11-10",
        "treatment_start_date": "2026-11-03",
        "event_outcome": "recovered",
        "hospitalization": False,
    }

    alias_result = lookup_case_fields(alias_case)
    alias_passed = alias_result["complete"]

    print(
        f"ALIASES: {'PASS' if alias_passed else 'FAIL'}"
    )

    results.append(alias_passed)

    passed = sum(results)
    total = len(results)

    print("\nCASE VALIDATION SUMMARY")
    print("=" * 35)
    print(f"Executed: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Pass rate: {passed / total * 100:.1f}%")


if __name__ == "__main__":
    main()


def test_case_validation_suite(capsys):
    main()
    output = capsys.readouterr().out
    assert "Failed:0" in "".join(output.split())
