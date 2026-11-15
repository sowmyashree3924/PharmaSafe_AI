
from typing import Any


REQUIRED_CASE_FIELDS = [
    "patient_age",
    "drug_name",
    "reaction_description",
    "event_onset_date",
    "drug_start_date",
    "outcome",
    "hospitalized",
]


FIELD_ALIASES = {
    "patient_age": ["patient_age", "age"],
    "drug_name": ["drug_name", "drug", "suspected_drug"],
    "reaction_description": [
        "reaction_description",
        "reaction",
        "adverse_reaction",
    ],
    "event_onset_date": [
        "event_onset_date",
        "onset_date",
        "reaction_onset_date",
    ],
    "drug_start_date": [
        "drug_start_date",
        "treatment_start_date",
        "medication_start_date",
    ],
    "outcome": ["outcome", "event_outcome"],
    "hospitalized": ["hospitalized", "hospitalisation", "hospitalization"],
}


def lookup_case_fields(case: dict[str, Any]) -> dict[str, Any]:
    """
    Extract relevant fields from a synthetic adverse event case.
    Supports common field aliases.
    Does not make medical or regulatory decisions.
    """

    fields = {}

    for field, aliases in FIELD_ALIASES.items():
        value = None

        for alias in aliases:
            if case.get(alias) is not None:
                value = case[alias]
                break

        fields[field] = value

    missing_fields = [
        field
        for field, value in fields.items()
        if value is None or value == ""
    ]

    return {
        "case_fields": fields,
        "missing_fields": missing_fields,
        "complete": len(missing_fields) == 0,
    }


if __name__ == "__main__":
    synthetic_case = {
        "patient_age": 45,
        "drug_name": "SyntheticDrug-A",
        "reaction_description": "Severe skin peeling",
        "event_onset_date": "2026-11-10",
        "drug_start_date": "2026-11-03",
        "outcome": "hospitalized",
        "hospitalized": True,
    }

    result = lookup_case_fields(synthetic_case)
    print(result)
