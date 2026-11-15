import time

from backend.agents.reliability import (
    run_reliable,
    reset_circuit_breakers,
    CircuitOpenError,
    ToolExecutionError,
)


def test_retry_then_success():
    reset_circuit_breakers()

    attempts = {"count": 0}

    def unstable_function():
        attempts["count"] += 1

        if attempts["count"] < 3:
            raise ValueError("Temporary failure")

        return "success"

    result = run_reliable(
        tool_name="retry_test",
        function=unstable_function,
        max_retries=3,
        timeout_seconds=2,
        initial_backoff=0,
    )

    assert result == "success"
    assert attempts["count"] == 3

    print("PASS: Retry succeeds after temporary failures.")


def test_timeout():
    reset_circuit_breakers()

    def slow_function():
        time.sleep(0.3)
        return "finished"

    try:
        run_reliable(
            tool_name="timeout_test",
            function=slow_function,
            max_retries=1,
            timeout_seconds=0.05,
            initial_backoff=0,
        )

        raise AssertionError("Expected timeout was not raised.")

    except ToolExecutionError:
        print("PASS: Timed-out tool is rejected.")


def test_circuit_breaker_opens():
    reset_circuit_breakers()

    def failing_function():
        raise ValueError("Service unavailable")

    try:
        run_reliable(
            tool_name="circuit_test",
            function=failing_function,
            max_retries=3,
            timeout_seconds=2,
            initial_backoff=0,
        )

        raise AssertionError("Expected failure was not raised.")

    except CircuitOpenError:
        print("PASS: Circuit breaker opens after repeated failures.")

    try:
        run_reliable(
            tool_name="circuit_test",
            function=lambda: "success",
            max_retries=1,
            timeout_seconds=2,
            initial_backoff=0,
        )

        raise AssertionError("Open circuit should reject execution.")

    except CircuitOpenError:
        print("PASS: Open circuit blocks further calls.")


if __name__ == "__main__":
    test_retry_then_success()
    test_timeout()
    test_circuit_breaker_opens()

    print("\nAll reliability tests passed!")
