from src.graph import graph


def test_safe_metrics_request_finishes_without_approval():
    config = {"configurable": {"thread_id": "pytest-safe-metrics"}}

    result = graph.invoke({"service_name": "billing-service"}, config)

    assert "__interrupt__" not in result
    assert result["metrics"]["error_rate_percent"] == 3.0
    assert result["next_action"] == "No scaling needed."
    
    
    
def test_metrics_are_saved_in_the_thread_checkpoint():
    config = {"configurable": {"thread_id": "pytest-memory"}}
    graph.invoke({"service_name": "billing-service"}, config)

    saved = graph.get_state(config).values

    assert saved["service_name"] == "billing-service"
    assert saved["metrics"]["error_rate_percent"] == 3.0
    
    
def test_follow_up_uses_saved_metrics():
    config = {"configurable": {"thread_id": "pytest-follow-up"}}

    graph.invoke({"service_name": "billing-service"}, config)
    result = graph.invoke({"use_saved_metrics": True}, config)

    assert result["next_action"] == "billing-service had a 3% error rate."