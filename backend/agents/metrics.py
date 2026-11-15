import time
from threading import Lock
from collections import defaultdict
from functools import wraps


class AgentMetrics:
    def __init__(self):
        self._metrics = defaultdict(lambda: {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_execution_time": 0.0,
            "average_execution_time": 0.0,
            "total_tool_calls": 0,
        })
        self._lock = Lock()

    def record_execution(self, agent_name, duration, success, tool_calls=0):
        with self._lock:
            metrics = self._metrics[agent_name]
            metrics["total_executions"] += 1

            if success:
                metrics["successful_executions"] += 1
            else:
                metrics["failed_executions"] += 1

            metrics["total_execution_time"] += duration
            metrics["total_tool_calls"] += tool_calls
            metrics["average_execution_time"] = (
                metrics["total_execution_time"] / metrics["total_executions"]
            )

    def get_agent_metrics(self, agent_name):
        with self._lock:
            return dict(self._metrics[agent_name])

    def get_all_metrics(self):
        with self._lock:
            return {name: dict(values) for name, values in self._metrics.items()}

    def reset(self):
        with self._lock:
            self._metrics.clear()


agent_metrics = AgentMetrics()


def track_agent(agent_name):
    def decorator(function):
        @wraps(function)
        def wrapper(state, *args, **kwargs):
            start_time = time.perf_counter()
            success = False
            tool_calls = 0
            result = {}

            try:
                result = function(state, *args, **kwargs)

                if isinstance(result, dict):
                    success = not result.get("escalation_required", False)

                    previous = state.get("tool_call_count", 0)
                    updated = result.get("tool_call_count", previous)
                    tool_calls = max(0, updated - previous)

                return result

            finally:
                duration = time.perf_counter() - start_time
                agent_metrics.record_execution(
                    agent_name,
                    duration,
                    success,
                    tool_calls,
                )

        return wrapper
    return decorator
