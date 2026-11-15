"""
Local deterministic evaluation utilities.

Lexical overlap is used only as a lightweight proxy.
It does not establish semantic entailment or clinical correctness.
"""


def normalize(text):
    return {
        word.lower().strip(".,!?;:()[]{}\"'")
        for word in str(text).split()
        if len(word) > 2
    }


def calculate_overlap(text_a, text_b):
    words_a = normalize(text_a)
    words_b = normalize(text_b)

    if not words_a:
        return 0.0

    return len(words_a & words_b) / len(words_a)


def evaluate_answer(answer, evidence, question=""):
    """
    Calculate lexical support proxies for generated claims.
    """

    claims = answer.get("claims", [])

    if not claims:
        return {
            "groundedness": 0.0,
            "context_relevance": 0.0,
            "faithfulness": 0.0,
            "hallucination_rate": 1.0,
            "evaluated_claims": 0,
            "evaluation_method": "lexical_overlap_proxy",
        }

    passages = [
        item.get("passage", "")
        for item in evidence
    ]

    grounded_claims = 0

    for claim in claims:
        claim_text = claim.get("text", "")

        supported = any(
            calculate_overlap(claim_text, passage) >= 0.30
            for passage in passages
        )

        if supported:
            grounded_claims += 1

    relevant_passages = sum(
        1
        for passage in passages
        if calculate_overlap(question, passage) >= 0.10
    )

    groundedness = grounded_claims / len(claims)

    context_relevance = (
        relevant_passages / len(passages)
        if passages else 0.0
    )

    hallucination_rate = (
        len(claims) - grounded_claims
    ) / len(claims)

    return {
        "groundedness": round(groundedness, 4),
        "context_relevance": round(context_relevance, 4),
        "faithfulness": round(groundedness, 4),
        "hallucination_rate": round(hallucination_rate, 4),
        "evaluated_claims": len(claims),
        "evaluation_method": "lexical_overlap_proxy",
    }


def compare_scenario(expected, actual):
    """
    Compare expected scenario outcomes with actual workflow outputs.

    Missing fields are reported as untested.
    They are never silently counted as passes.
    """

    field_mapping = {
        "escalation": "escalation_required",
        "seriousness": "seriousness",
        "expectedness": "expectedness",
        "causality": "causality",
        "reporting_route": "reporting_route",
    }

    comparisons = {}
    missing = []

    for expected_field, expected_value in expected.items():
        actual_field = field_mapping.get(
            expected_field,
            expected_field,
        )

        if actual_field not in actual:
            missing.append(expected_field)
            continue

        actual_value = actual[actual_field]

        comparisons[expected_field] = {
            "expected": expected_value,
            "actual": actual_value,
            "passed": actual_value == expected_value,
        }

    tested = len(comparisons)

    passed_count = sum(
        item["passed"]
        for item in comparisons.values()
    )

    all_passed = (
        tested > 0
        and not missing
        and passed_count == tested
    )

    return {
        "passed": all_passed,
        "tested_fields": tested,
        "passed_fields": passed_count,
        "missing_fields": missing,
        "comparisons": comparisons,
    }
