from unittest.mock import patch
from src.circuit_breaker import tool_call_fingerprint
from src.graph import graph




def test_repeated_tool_call_stops_after_one_iteration():
    result = graph.invoke(
        {"service_name": "auth-service", "retry_demo": True},
        {"configurable": {"thread_id": "pytest-repeat"}},
    )

    assert result["next_action"] == "Detected a repeated tool call."
    assert result["completed_iterations"] == 1


def test_iteration_limit_stops_after_six_calls():
    fingerprints = [f"test-call-{number}" for number in range(1, 8)]

    with patch("src.graph.tool_call_fingerprint", side_effect=fingerprints):
        result = graph.invoke(
            {"service_name": "auth-service", "retry_demo": True},
            {"configurable": {"thread_id": "pytest-limit"}},
        )

    assert result["next_action"] == "Reached the six-iteration limit."
    assert result["completed_iterations"] == 6
    
    
    
def test_fingerprint_ignores_argument_order():
    first = {"service_name": "auth-service", "replica_count": 10}
    reordered = {"replica_count": 10, "service_name": "auth-service"}

    assert tool_call_fingerprint(
        "scale_kubernetes_cluster", first
    ) == tool_call_fingerprint("scale_kubernetes_cluster", reordered)