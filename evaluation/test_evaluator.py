from evaluation.evaluator import evaluate_answer


def test_fully_supported_answer():
    answer = {
        "claims": [
            {"text": "Hospitalisation is a seriousness criterion."}
        ]
    }

    evidence = [
        {
            "passage": (
                "Hospitalisation is a seriousness criterion "
                "for an adverse event."
            )
        }
    ]

    result = evaluate_answer(
        answer,
        evidence,
        "hospitalisation seriousness",
    )

    assert result["groundedness"] == 1.0
    assert result["faithfulness"] == 1.0
    assert result["hallucination_rate"] == 0.0

    print("PASS: Supported claim evaluated correctly.")


def test_unsupported_answer():
    answer = {
        "claims": [
            {"text": "This medicine causes kidney failure."}
        ]
    }

    evidence = [
        {"passage": "Hospitalisation is a seriousness criterion."}
    ]

    result = evaluate_answer(
        answer,
        evidence,
        "medicine adverse reactions",
    )

    assert result["groundedness"] == 0.0
    assert result["hallucination_rate"] == 1.0

    print("PASS: Unsupported claim detected.")


if __name__ == "__main__":
    test_fully_supported_answer()
    test_unsupported_answer()
    print("\nEvaluator tests passed!")
