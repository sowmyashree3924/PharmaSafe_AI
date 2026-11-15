
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from threading import Lock


MAX_RETRIES = 3
TOOL_TIMEOUT_SECONDS = 10
INITIAL_BACKOFF_SECONDS = 0.5

CIRCUIT_FAILURE_THRESHOLD = 3
CIRCUIT_RESET_SECONDS = 30


# Per-tool circuit breaker state.
_circuit_states = {}
_circuit_lock = Lock()


class CircuitOpenError(Exception):
    """Raised when a tool's circuit breaker is open."""


class ToolExecutionError(Exception):
    """Raised when a tool fails after retries."""


def get_circuit_state(tool_name):
    with _circuit_lock:
        return _circuit_states.setdefault(
            tool_name,
            {
                "failures": 0,
                "opened_at": None,
            },
        )


def is_circuit_open(tool_name):
    with _circuit_lock:
        state = _circuit_states.setdefault(
            tool_name,
            {
                "failures": 0,
                "opened_at": None,
            },
        )

        opened_at = state["opened_at"]

        if opened_at is None:
            return False

        elapsed = time.monotonic() - opened_at

        if elapsed < CIRCUIT_RESET_SECONDS:
            return True

        # Allow a new attempt after the cooldown.
        # A successful call will reset the circuit.
        return False


def record_success(tool_name):
    with _circuit_lock:
        _circuit_states[tool_name] = {
            "failures": 0,
            "opened_at": None,
        }


def record_failure(tool_name):
    with _circuit_lock:
        state = _circuit_states.setdefault(
            tool_name,
            {
                "failures": 0,
                "opened_at": None,
            },
        )

        state["failures"] += 1

        if state["failures"] >= CIRCUIT_FAILURE_THRESHOLD:
            state["opened_at"] = time.monotonic()


def reset_circuit_breakers():
    """Reset circuit state. Useful for tests and controlled recovery."""

    with _circuit_lock:
        _circuit_states.clear()


def execute_with_timeout(function, timeout_seconds):
    """
    Execute a synchronous function with a maximum wait time.

    A timed-out worker thread may continue running in the background;
    Python cannot forcibly terminate an arbitrary running thread.
    """

    executor = ThreadPoolExecutor(max_workers=1)

    future = executor.submit(function)

    try:
        return future.result(timeout=timeout_seconds)

    except TimeoutError:
        future.cancel()
        raise TimeoutError(
            f"Tool execution exceeded {timeout_seconds} seconds."
        )

    finally:
        # Do not block the caller waiting for a timed-out thread.
        executor.shutdown(
            wait=False,
            cancel_futures=True,
        )


def run_reliable(
    tool_name,
    function,
    max_retries=MAX_RETRIES,
    timeout_seconds=TOOL_TIMEOUT_SECONDS,
    initial_backoff=INITIAL_BACKOFF_SECONDS,
):
    """
    Execute a tool with:
    - Circuit breaker
    - Timeout
    - Bounded retries
    - Exponential backoff
    """

    if is_circuit_open(tool_name):
        raise CircuitOpenError(
            f"Circuit breaker is open for {tool_name}."
        )

    last_error = None

    for attempt in range(max_retries):

        try:
            result = execute_with_timeout(
                function,
                timeout_seconds,
            )

            record_success(tool_name)

            return result

        except Exception as error:

            last_error = error
            record_failure(tool_name)

            if is_circuit_open(tool_name):
                raise CircuitOpenError(
                    f"Circuit breaker opened for {tool_name}."
                ) from error

            if attempt < max_retries - 1:
                delay = initial_backoff * (2 ** attempt)
                time.sleep(delay)

    raise ToolExecutionError(
        f"{tool_name} failed after {max_retries} attempts: "
        f"{last_error}"
    ) from last_error
