from unittest.mock import patch

from langgraph.types import Command

from src.graph import graph


def test_approval_pauses_and_then_runs_scaling():
    config = {"configurable": {"thread_id": "pytest-approve"}}

    paused = graph.invoke({"service_name": "auth-service"}, config)
    request = paused["__interrupt__"][0].value
    assert request["service_name"] == "auth-service"
    assert request["replica_count"] == 10

    result = graph.invoke(Command(resume=True), config)
    assert result["next_action"] == (
        "Simulated scaling: auth-service now has 10 replicas."
    )


def test_rejection_skips_scaling():
    config = {"configurable": {"thread_id": "pytest-reject"}}

    with patch("src.graph.scale_kubernetes_cluster") as scale:
        paused = graph.invoke({"service_name": "auth-service"}, config)
        assert "__interrupt__" in paused

        result = graph.invoke(Command(resume=False), config)
        scale.assert_not_called()

    assert result["next_action"] == "Scaling canceled."